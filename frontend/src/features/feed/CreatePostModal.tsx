import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import { X, Image as ImageIcon, Video, Send, Loader2, MapPin, Crosshair, ChevronLeft } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import imageCompression from 'browser-image-compression';
import { createPost } from './feedApi';
import { useToast } from '@/shared/ui';
import LoginForm from '@/features/auth/LoginForm';
import { useAuth } from '@/hooks/useAuth';
import { searchLocations, getCurrentLocation } from '@/features/geocoding/geocodingApi';
import type { LocationSuggestion } from '@/features/geocoding/types';

import { useRouter, useSearchParams } from 'next/navigation';
import { get, set, del } from 'idb-keyval';
const slideVariants = {
  enter: (direction: 'forward' | 'backward') => ({
    x: direction === 'forward' ? '100%' : '-100%',
    opacity: 0
  }),
  center: {
    x: 0,
    opacity: 1
  },
  exit: (direction: 'forward' | 'backward') => ({
    x: direction === 'forward' ? '-100%' : '100%',
    opacity: 0
  })
};

interface CreatePostModalProps {
  onClose: () => void;
  initialFiles?: File[];
}

export function CreatePostModal({ onClose, initialFiles }: CreatePostModalProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [content, setContent] = useState(() => {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('lanes_draft_post') || '';
    }
    return '';
  });
  const [selectedFiles, setSelectedFiles] = useState<{ file: File; preview: string }[]>([]);
  const [locationTag, setLocationTag] = useState('');
  const objectUrlsRef = React.useRef<string[]>([]);
  const hasRestoredRef = React.useRef(false);
  const [showDraftConfirm, setShowDraftConfirm] = useState(false);

  const handleCloseRequest = () => {
    if (content.trim() || selectedFiles.length > 0 || locationTag.trim()) {
      setShowDraftConfirm(true);
    } else {
      onClose();
    }
  };

  const handleSaveDraftAndClose = async () => {
    sessionStorage.setItem('lanes_draft_post', content);
    if (selectedFiles.length > 0) {
      await set('lanes_draft_files', selectedFiles.map(f => f.file));
    }
    onClose();
  };

  const handleDiscardAndClose = async () => {
    sessionStorage.removeItem('lanes_draft_post');
    await del('lanes_draft_files');
    onClose();
  };

  // Safely initialize selectedFiles from initialFiles on mount/prop change
  useEffect(() => {
    if (initialFiles && initialFiles.length > 0) {
      const mapped = initialFiles.map(file => ({
        file,
        preview: URL.createObjectURL(file)
      }));
      setSelectedFiles(mapped);
    }
  }, [initialFiles]);

  // Keep track of all object URLs created for previewing files
  useEffect(() => {
    objectUrlsRef.current = selectedFiles.map(f => f.preview);
  }, [selectedFiles]);

  // Clean up object URLs on component unmount
  useEffect(() => {
    return () => {
      objectUrlsRef.current.forEach(url => URL.revokeObjectURL(url));
    };
  }, []);

  const [showLocationInput, setShowLocationInput] = useState(false);
  const [viewMode, setViewMode] = useState<'write' | 'location'>('write');
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward');
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showAuthPrompt, setShowAuthPrompt] = useState(false);
  const { isAuthenticated } = useAuth();
  const { success, error: showError } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (isAuthenticated && showAuthPrompt) {
      setShowAuthPrompt(false);
    }
  }, [isAuthenticated, showAuthPrompt]);

  // Handle location tag search query suggestions
  useEffect(() => {
    if (locationTag.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchLocations(locationTag);
        setSuggestions(results);
      } catch (err: any) {
        showError("Search Error", err.message || "Failed to search locations");
      } finally {
        setIsSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [locationTag]);

  useEffect(() => {
    setMounted(true);
    document.body.style.overflow = 'hidden';
    
    // Check searchParams for location tag pre-fill
    const locTag = searchParams.get('location_tag');
    if (locTag) {
      setLocationTag(locTag);
      setShowLocationInput(true);
      
      // Clean up URL search params
      const params = new URLSearchParams(window.location.search);
      params.delete('location_tag');
      params.delete('openPostModal');
      window.history.replaceState(
        null, 
        '', 
        window.location.pathname + (params.toString() ? '?' + params.toString() : '')
      );
    }
    
    if (typeof window !== 'undefined') {
      const draft = sessionStorage.getItem('lanes_draft_post');
      if (draft && !content) {
        setContent(draft);
      }
    }
    
    // Always restore files from IndexedDB
    if (!hasRestoredRef.current) {
      hasRestoredRef.current = true;
      get('lanes_draft_files').then(files => {
        if (files && files.length > 0) {
          const mapped = files.map((file: File) => ({
            file,
            preview: URL.createObjectURL(file)
          }));
          setSelectedFiles(prev => [...prev, ...mapped]);
          del('lanes_draft_files');
        }
      }).catch((err: any) => {
        showError("Draft Error", "Failed to restore files from IndexedDB: " + err.message);
      });
    }
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [searchParams]);

  const handleChooseOnMap = async () => {
    sessionStorage.setItem('lanes_draft_post', content);
    if (selectedFiles.length > 0) {
      await set('lanes_draft_files', selectedFiles.map(f => f.file));
    }
    router.push('/map?action=pickPostLocation');
  };

  const handleUseCurrentLocation = async () => {
    try {
      const [lng, lat] = await getCurrentLocation();
      const res = await fetch(`https://photon.komoot.io/reverse?lon=${lng}&lat=${lat}`);
      if (!res.ok) throw new Error("Reverse geocode failed");
      const data = await res.json();
      let resolvedLabel = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
      if (data.features && data.features.length > 0) {
        const props = data.features[0].properties;
        const parts = [props.name, props.street, props.locality, props.city, props.state]
          .filter(Boolean)
          .filter((value, index, self) => self.indexOf(value) === index);
        resolvedLabel = parts.slice(0, 2).join(", ") || resolvedLabel;
      }
      setLocationTag(resolvedLabel);
      setIsFocused(false);
    } catch (err: any) {
      showError('Location Error', err.message || 'Could not fetch current location.');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const MAX_FILE_SIZE_MB = 20;
      const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
      
      const files = Array.from(e.target.files);
      const validFiles: { file: File; preview: string }[] = [];
      
      for (const file of files) {
        if (file.size > MAX_FILE_SIZE_BYTES) {
          showError(`File "${file.name}" is too large. Maximum size is ${MAX_FILE_SIZE_MB}MB.`);
          continue;
        }
        validFiles.push({
          file,
          preview: URL.createObjectURL(file)
        });
      }
      
      if (validFiles.length > 0) {
        setSelectedFiles(prev => [...prev, ...validFiles]);
      }
    }
  };

  const removeFile = (indexToRemove: number) => {
    setSelectedFiles(prev => {
      const updated = [...prev];
      URL.revokeObjectURL(updated[indexToRemove].preview);
      updated.splice(indexToRemove, 1);
      return updated;
    });
  };

  const createMutation = useMutation({
    mutationFn: async () => {
      // Compress images before sending
      const compressedImages = await Promise.all(
        selectedFiles.map(async (f) => {
          if (!f.file.type.startsWith('image/')) return f.file;
          
          try {
            const options = {
              maxSizeMB: 1,
              maxWidthOrHeight: 1200,
              useWebWorker: true,
              fileType: 'image/webp'
            };
            const compressedBlob = await imageCompression(f.file, options);
            return new File([compressedBlob], f.file.name.replace(/\.[^/.]+$/, "") + ".webp", {
              type: 'image/webp',
              lastModified: Date.now(),
            });
          } catch (error: any) {
            showError("Compression Failed", `Failed to compress ${f.file.name}: ${error.message}`);
            return f.file; // fallback to original
          }
        })
      );

      return createPost({ 
        content, 
        images: compressedImages,
        location_tag: locationTag.trim() || undefined
      });
    },
    onSuccess: () => {
      success('Post created successfully!');
      sessionStorage.removeItem('lanes_draft_post');
      setLocationTag('');
      queryClient.invalidateQueries({ queryKey: ['feed'] });
      onClose();
    },
    onError: (err: any) => {
      if (err.status === 401 || err.message.includes('401') || err.message.includes('authenticated') || err.message.includes('credentials') || err.message.includes('logged in')) {
        localStorage.removeItem('lanes_token');
        setShowAuthPrompt(true);
      } else {
        showError('Failed to create post', err.message);
      }
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      showError("Please enter a description for your post.");
      return;
    }
    
    if (!localStorage.getItem('lanes_token')) {
      sessionStorage.setItem('lanes_draft_post', content);
      sessionStorage.setItem('lanes_post_intent', 'true');
      setShowAuthPrompt(true);
      return;
    }
    
    createMutation.mutate();
  };

  if (!mounted) return null;

  // Helper to render media (video vs image)
  const renderMedia = (f: {file: File, preview: string}, className: string) => {
    if (f.file.type.startsWith('video/')) {
      return <video src={f.preview} controls className={className + " bg-black"} />;
    }
    return <img src={f.preview} alt="Preview" className={className} />;
  };

  // Facebook style grid preview
  const renderGridPreview = () => {
    if (selectedFiles.length === 0) return null;

    const count = selectedFiles.length;
    let gridContent = null;

    // Helper for rendering a grid cell with remove button
    const renderCell = (index: number, extraClass: string = "", overlayIndex?: number) => (
      <div key={index} className={`relative w-full h-full overflow-hidden ${extraClass}`}>
        {renderMedia(selectedFiles[index], "w-full h-full object-cover")}
        {overlayIndex === index && count > 5 && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center pointer-events-none">
            <span className="text-white text-3xl font-bold">+{count - 5}</span>
          </div>
        )}
        <button 
          type="button" 
          onClick={() => removeFile(index)} 
          className="absolute top-2 right-2 p-1.5 bg-black/50 text-white rounded-full hover:bg-black/70 backdrop-blur-md z-10 scale-90"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );

    if (count === 1) {
      gridContent = (
        <div className="w-full max-h-[300px]">
          {renderCell(0, "max-h-[300px]")}
        </div>
      );
    } else if (count === 2) {
      gridContent = (
        <div className="grid grid-cols-2 gap-1 w-full aspect-video">
          {renderCell(0)}
          {renderCell(1)}
        </div>
      );
    } else if (count === 3) {
      gridContent = (
        <div className="flex flex-col gap-1 w-full aspect-square">
          <div className="flex-1 w-full">{renderCell(0)}</div>
          <div className="flex-1 grid grid-cols-2 gap-1 w-full">
            {renderCell(1)}
            {renderCell(2)}
          </div>
        </div>
      );
    } else if (count === 4) {
      gridContent = (
        <div className="flex flex-col gap-1 w-full aspect-square">
          <div className="flex-[2] w-full">{renderCell(0)}</div>
          <div className="flex-[1] grid grid-cols-3 gap-1 w-full">
            {renderCell(1)}
            {renderCell(2)}
            {renderCell(3)}
          </div>
        </div>
      );
    } else {
      // 5 or more (Facebook style: 2 on top, 3 on bottom)
      gridContent = (
        <div className="flex flex-col gap-1 w-full aspect-square">
          <div className="flex-1 grid grid-cols-2 gap-1 w-full">
            {renderCell(0)}
            {renderCell(1)}
          </div>
          <div className="flex-1 grid grid-cols-3 gap-1 w-full">
            {renderCell(2)}
            {renderCell(3)}
            {renderCell(4, "", 4)}
          </div>
        </div>
      );
    }

    return (
      <div className="relative mt-2 rounded-xl overflow-hidden border border-gray-200 shrink-0">
        {gridContent}
      </div>
    );
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh] relative">
        {/* Auth Prompt Overlay */}
        {showAuthPrompt && (
          <div className="absolute inset-0 z-[70] bg-white/95 backdrop-blur-md flex flex-col items-center justify-center p-6 animate-in fade-in">
            <button 
              onClick={() => setShowAuthPrompt(false)}
              className="absolute top-4 right-4 p-2 bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-700 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="w-full max-w-sm">
              <h3 className="text-2xl font-bold text-gray-900 mb-2 text-center">Login Required</h3>
              <p className="text-gray-600 mb-6 text-center text-sm">Sign in to share your post and photos with the community.</p>
              <LoginForm />
            </div>
          </div>
        )}

        {/* Draft Confirmation Overlay */}
        {showDraftConfirm && (
          <div className="absolute inset-0 z-[80] bg-black/40 backdrop-blur-sm flex flex-col items-center justify-center p-6 animate-in fade-in">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
              <div className="p-6 border-b border-gray-100">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Save as draft?</h3>
                <p className="text-sm text-gray-600">You have unsaved changes. Would you like to save this post as a draft or discard it completely?</p>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50">
                <button 
                  onClick={() => setShowDraftConfirm(false)}
                  className="px-4 py-2 bg-transparent hover:bg-gray-200 text-gray-600 font-medium rounded-lg transition-colors"
                >
                  Keep Editing
                </button>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={handleDiscardAndClose}
                    className="px-4 py-2 bg-white hover:bg-red-50 text-red-600 border border-gray-200 hover:border-red-200 font-medium rounded-lg transition-colors"
                  >
                    Discard Post
                  </button>
                  <button 
                    onClick={handleSaveDraftAndClose}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-sm"
                  >
                    Save Draft
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-100">
          {viewMode === 'location' ? (
            <div className="flex items-center gap-2">
              <button 
                type="button"
                onClick={() => {
                  setDirection('backward');
                  setViewMode('write');
                }}
                className="p-2 bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-700 rounded-full transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h2 className="text-xl font-bold text-gray-900 font-sans">Add Location</h2>
            </div>
          ) : (
            <h2 className="text-xl font-bold text-gray-900">Create Post</h2>
          )}
          <button 
            type="button"
            onClick={handleCloseRequest}
            className="p-2 bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-700 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-auto relative overflow-hidden flex flex-col min-h-[350px]">
          <AnimatePresence initial={false} custom={direction} mode="wait">
            {viewMode === 'location' ? (
              <motion.div
                key="location"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="w-full flex-auto p-5 flex flex-col min-h-0 bg-white"
              >
                {/* Location Input */}
                <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-500 transition-all duration-200 shrink-0">
                  <MapPin className="w-4 h-4 text-red-500 shrink-0" />
                  <input
                    type="text"
                    placeholder="Search for a location... (e.g. Pasig Cathedral)"
                    value={locationTag}
                    onChange={(e) => setLocationTag(e.target.value)}
                    autoFocus
                    className="w-full bg-transparent text-sm text-gray-800 border-none focus:ring-0 focus:outline-none placeholder-gray-400 p-0"
                  />
                  {locationTag && (
                    <button 
                      type="button" 
                      onClick={() => setLocationTag('')}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Suggestions List Container */}
                <div className="mt-3 flex-1 overflow-y-auto rounded-xl border border-gray-100 divide-y divide-gray-100 shadow-sm min-h-[250px]">
                  <ul>
                    {/* Choose on Map */}
                    <li>
                      <button
                        type="button"
                        onClick={handleChooseOnMap}
                        className="flex items-center gap-3 w-full px-4 py-3.5 text-left hover:bg-blue-50/50 transition-colors border-b border-gray-100"
                      >
                        <div className="bg-blue-100 p-2 rounded-full shrink-0">
                          <Crosshair className="w-4 h-4 text-blue-600" />
                        </div>
                        <span className="text-sm font-semibold text-blue-600">Choose on Map</span>
                      </button>
                    </li>

                    {/* Use Current Location */}
                    <li>
                      <button
                        type="button"
                        onClick={async () => {
                          setDirection('backward');
                          await handleUseCurrentLocation();
                          setViewMode('write');
                        }}
                        className="flex items-center gap-3 w-full px-4 py-3.5 text-left hover:bg-blue-50/50 transition-colors border-b border-gray-100"
                      >
                        <div className="bg-gray-100 p-2 rounded-full shrink-0">
                          <MapPin className="w-4 h-4 text-gray-600" />
                        </div>
                        <span className="text-sm font-semibold text-gray-700">Use Current Location</span>
                      </button>
                    </li>

                    {/* Searching loader */}
                    {isSearching && (
                      <div className="px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                        <span>Searching locations...</span>
                      </div>
                    )}

                    {/* Autocomplete Results */}
                    {!isSearching && suggestions.map((suggestion) => (
                      <li key={suggestion.id}>
                        <button
                          type="button"
                          onClick={() => {
                            setDirection('backward');
                            setLocationTag(suggestion.label);
                            setViewMode('write');
                          }}
                          className="flex items-center gap-3 w-full px-4 py-3.5 text-left hover:bg-gray-50 transition-colors"
                        >
                          <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                          <div className="flex flex-col min-w-0">
                            <span className="text-sm font-semibold text-gray-800">{suggestion.label}</span>
                            <span className="text-[11px] text-gray-400 truncate">{suggestion.displayName}</span>
                          </div>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="write"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="w-full flex-auto flex flex-col min-h-0 bg-white"
              >
                <form onSubmit={handleSubmit} className="flex-auto flex flex-col overflow-y-auto min-h-0">
                  <div className="p-4 flex-auto flex flex-col justify-between">
                    <div className="flex flex-col">
                      <textarea
                        className="w-full text-gray-800 text-lg border-none focus:outline-none focus:ring-0 focus:border-transparent resize-none min-h-[60px] overflow-hidden placeholder-gray-400 bg-transparent"
                        placeholder="What's happening in your area?"
                        value={content}
                        onChange={(e) => {
                          setContent(e.target.value);
                          e.target.style.height = 'auto';
                          e.target.style.height = e.target.scrollHeight + 'px';
                        }}
                        disabled={createMutation.isPending}
                        autoFocus
                      ></textarea>

                      {/* Location Tag Chip */}
                      {locationTag && (
                        <div className="mt-2 mb-1 flex items-center justify-between bg-blue-50 border border-blue-100 rounded-xl px-4 py-2.5 animate-in fade-in slide-in-from-top-1 duration-200 shrink-0">
                          <div className="flex items-center gap-2 min-w-0">
                            <MapPin className="w-4 h-4 text-red-500 shrink-0" />
                            <span className="text-xs font-semibold text-blue-800 truncate">{locationTag}</span>
                          </div>
                          <button 
                            type="button" 
                            onClick={() => setLocationTag('')}
                            className="p-1 text-blue-400 hover:text-blue-600 rounded-full hover:bg-blue-100 transition-colors"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}

                      {renderGridPreview()}
                    </div>
                  </div>

                  {/* Footer Actions */}
                  <div className="p-4 border-t border-gray-100 flex items-center justify-between bg-gray-50 shrink-0">
                    <div className="flex items-center gap-2">
                      <label 
                        className="cursor-pointer text-blue-600 hover:bg-blue-100 p-2 rounded-full transition-colors flex items-center justify-center"
                        title="Add Photo"
                      >
                        <ImageIcon className="w-5 h-5" />
                        <input 
                          type="file" 
                          accept="image/*" 
                          multiple
                          className="hidden" 
                          onChange={handleFileChange}
                          disabled={createMutation.isPending}
                        />
                      </label>

                      <label 
                        className="cursor-pointer text-green-600 hover:bg-green-100 p-2 rounded-full transition-colors flex items-center justify-center"
                        title="Add Video"
                      >
                        <Video className="w-5 h-5" />
                        <input 
                          type="file" 
                          accept="video/*" 
                          multiple
                          className="hidden" 
                          onChange={handleFileChange}
                          disabled={createMutation.isPending}
                        />
                      </label>

                      <button 
                        type="button"
                        onClick={() => {
                          setDirection('forward');
                          setViewMode('location');
                        }}
                        className={`text-red-500 hover:bg-red-100 p-2 rounded-full transition-colors flex items-center justify-center ${locationTag ? 'bg-red-50 text-red-600 font-bold' : ''}`}
                        title="Add Location"
                        disabled={createMutation.isPending}
                      >
                        <MapPin className="w-5 h-5" />
                      </button>
                    </div>

                    <button
                      type="submit"
                      disabled={createMutation.isPending || !content.trim()}
                      className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-bold shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                    >
                      {createMutation.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Posting...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Post
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>,
    document.body
  );
}
