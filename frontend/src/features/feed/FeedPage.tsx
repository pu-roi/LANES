"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { getFeed, votePost, FeedPost } from './feedApi';
import { PostItem } from './PostItem';
import { CreatePostModal } from './CreatePostModal';
import { Loader2, Filter, Image as ImageIcon, Video, Menu, X, Map, Rss, MessageSquarePlus, Settings, TrendingUp, Flame, Heart, Plus, ChevronDown, Pin } from 'lucide-react';
import { useToast, Button } from '@/shared/ui';
import { savedPlacesApi } from '@/features/places/savedPlacesApi';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { EmergencyHotlinesCard } from './components/EmergencyHotlinesCard';

export function FeedPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { error: showError } = useToast();
  const [tab, setTab] = useState<'recent' | 'nearby'>('recent');
  const [userLocation, setUserLocation] = useState<{lat: number, lng: number} | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [preselectedFiles, setPreselectedFiles] = useState<File[]>([]);
  // Stores location pre-fill data received from the map picker round-trip.
  // We read it here (where searchParams is reliably fresh) and pass it as a
  // prop so CreatePostModal never touches useSearchParams for this purpose.
  const [initialLocation, setInitialLocation] = useState<{
    locationTag: string;
    lat: number | null;
    lng: number | null;
  } | null>(null);
  const photoInputRef = React.useRef<HTMLInputElement>(null);
  const videoInputRef = React.useRef<HTMLInputElement>(null);

  const { isAuthenticated } = useAuth();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    if (isDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen]);

  const { data: savedPlaces, isLoading: savedPlacesLoading } = useQuery({
    queryKey: ['saved-places', isAuthenticated],
    queryFn: savedPlacesApi.getSavedPlaces,
    enabled: isAuthenticated,
  });

  const sortedPlaces = savedPlaces ? [...savedPlaces].sort((a, b) => {
    const orderA = a.pin_order ?? 999;
    const orderB = b.pin_order ?? 999;
    if (orderA === orderB) return 0;
    return orderA - orderB;
  }) : [];
  
  const visiblePlaces = sortedPlaces.slice(0, 3);
  const hiddenPlaces = sortedPlaces.slice(3);

  // Auto-open modal if user just came back from map location pick or login redirect
  useEffect(() => {
    if (searchParams.get('openPostModal') === 'true') {
      const locTag = searchParams.get('location_tag');
      const latStr = searchParams.get('lat');
      const lngStr = searchParams.get('lng');
      if (locTag) {
        setInitialLocation({
          locationTag: locTag,
          lat: latStr ? parseFloat(latStr) : null,
          lng: lngStr ? parseFloat(lngStr) : null,
        });
      } else {
        setInitialLocation(null);
      }
      setIsCreateModalOpen(true);
      // Use router.replace so Next.js router state stays in sync with the browser
      // URL. window.history.replaceState was desync-ing the two, causing
      // useSearchParams() in CreatePostModal to return stale values on the
      // second+ "Choose on Map" round-trip.
      router.replace('/feed', { scroll: false });
    }
  }, [searchParams, router]);

  // Request location if nearby tab is clicked and we don't have it
  useEffect(() => {
    if (tab === 'nearby' && !userLocation) {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          },
          (err) => {
            showError("Location Unavailable", "Please enable location permissions to use the Nearby feed.");
            setTab('recent');
          }
        );
      } else {
        showError("Not Supported", "Geolocation is not supported by your browser.");
        setTab('recent');
      }
    }
  }, [tab, userLocation, showError]);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['feed', tab, userLocation?.lat, userLocation?.lng],
    queryFn: () => getFeed(userLocation?.lat, userLocation?.lng, tab, 0, 50),
    enabled: tab === 'recent' || (tab === 'nearby' && userLocation !== null),
  });

  const voteMutation = useMutation({
    mutationFn: ({ postId, type }: { postId: number, type: 'upvote' | 'downvote' }) => votePost(postId, type),
    onSuccess: () => {
      // Invalidate feed to refresh votes
      queryClient.invalidateQueries({ queryKey: ['feed'] });
    },
    onError: (err: any) => {
      if (err.status === 401) {
        showError('Login Required', 'Please log in first to interact with posts!');
      } else {
        showError('Failed to vote', err.message);
      }
    }
  });

  const handleVote = (postId: number, type: 'upvote' | 'downvote') => {
    voteMutation.mutate({ postId, type });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setPreselectedFiles(Array.from(e.target.files));
      setIsCreateModalOpen(true);
    }
  };

  const navItems = [
    { name: 'Community Feed', href: '/feed', icon: Rss },
    { name: 'Live Map', href: '/map', icon: Map },
    { name: 'Submit Report', href: '/map?action=report', icon: MessageSquarePlus },
  ];

  const closeMenu = () => {
    setIsMobileMenuOpen(false);
    if (window.history.state?.sidebar) {
      window.history.back();
    }
  };

  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
      if (!window.history.state?.sidebar) {
        window.history.pushState({ sidebar: true }, '');
      }

      const handlePopState = () => {
        setIsMobileMenuOpen(false);
      };
      
      window.addEventListener('popstate', handlePopState);
      return () => {
        document.body.style.overflow = '';
        window.removeEventListener('popstate', handlePopState);
      };
    } else {
      document.body.style.overflow = '';
    }
  }, [isMobileMenuOpen]);

  return (
    <>
      {/* Header with Tabs */}
          <div className="bg-transparent border-b border-gray-200 px-4 pt-1 pb-0 flex flex-col justify-end">
            <div className="flex items-center gap-3 mb-2 px-2">
              <button 
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden p-2 -ml-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors active:scale-95"
              >
                <Menu className="w-6 h-6" />
              </button>
              <h1 className="text-xl font-extrabold tracking-tight">Community Feed</h1>
            </div>
            
            <div className="flex justify-between items-end px-2">
              <div className="flex gap-6">
                <button 
                  onClick={() => setTab('recent')}
                  className={`pb-3 text-sm font-bold transition-colors relative ${
                    tab === 'recent' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Recent
                  {tab === 'recent' && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 rounded-t-md"></div>
                  )}
                </button>
                
                <button 
                  onClick={() => setTab('nearby')}
                  className={`pb-3 text-sm font-bold transition-colors relative ${
                    tab === 'nearby' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Nearby
                  {tab === 'nearby' && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 rounded-t-md"></div>
                  )}
                </button>
              </div>

              <Button variant="ghost" size="sm" className="text-gray-500 hover:text-blue-600">
                <Filter className="w-4 h-4 mr-1.5" />
                Filters
              </Button>
            </div>
          </div>

          {/* Create Post Input Trigger */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
              <span className="font-bold text-blue-700 text-sm">Me</span>
            </div>
            <button 
              onClick={() => setIsCreateModalOpen(true)}
              className="flex-1 bg-gray-100 hover:bg-gray-200 transition-colors rounded-full text-left px-5 py-3 text-gray-500 text-sm font-medium"
            >
              What's happening in your area?
            </button>
            
            {/* Quick Media Actions */}
            <div className="flex items-center gap-1 border-l border-gray-100 pl-2 shrink-0">
              <input 
                type="file" 
                ref={photoInputRef}
                accept="image/*" 
                multiple 
                className="hidden" 
                onChange={handleFileChange} 
              />
              <input 
                type="file" 
                ref={videoInputRef}
                accept="video/*" 
                multiple 
                className="hidden" 
                onChange={handleFileChange} 
              />
              <button 
                onClick={() => photoInputRef.current?.click()}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors flex items-center justify-center"
                title="Add Photo"
              >
                <ImageIcon className="w-5 h-5" />
              </button>
              <button 
                onClick={() => videoInputRef.current?.click()}
                className="p-2 text-green-600 hover:bg-green-50 rounded-full transition-colors flex items-center justify-center"
                title="Add Video"
              >
                <Video className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Feed Content */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 mt-2 overflow-hidden mb-20">
            {isLoading && (
              <div className="flex flex-col items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
                <p className="text-gray-500 text-sm font-medium">Fetching reports...</p>
              </div>
            )}

            {isError && (
              <div className="p-8 text-center text-red-500">
                <p>Failed to load feed.</p>
                <p className="text-xs mt-2 opacity-70">{(error as Error).message}</p>
              </div>
            )}

            {data && data.posts.length === 0 && (
              <div className="p-16 text-center text-gray-500">
                <p className="font-medium text-lg text-gray-700">No reports found.</p>
                <p className="text-sm mt-1">Check back later or submit a new report.</p>
              </div>
            )}

            {data && data.posts.map((post: FeedPost) => (
              <PostItem 
                key={post.id} 
                post={post} 
                onVote={handleVote}
                onViewMap={(lat, lng) => {
                  // Navigate to /map first (clean URL, no query params), then fire the
                  // fly-to-location event. Using query params was unreliable because
                  // MapCanvas is a persistent component — its searchParams useEffect
                  // dep sometimes didn't change, so the flyTo never triggered.
                  router.push('/map');
                  setTimeout(() => {
                    window.dispatchEvent(new CustomEvent('fly-to-location', {
                      detail: { latitude: lat, longitude: lng, zoom: 16, duration: 1500 }
                    }));
                  }, 150);
                }}
              />
            ))}
          </div>

      {/* Create Post Modal */}
      {isCreateModalOpen && (
        <CreatePostModal 
          onClose={() => {
            setIsCreateModalOpen(false);
            setPreselectedFiles([]);
            setInitialLocation(null);
          }} 
          initialFiles={preselectedFiles}
          initialLocation={initialLocation}
        />
      )}

      {/* Mobile Navigation Drawer */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-[60] flex">
            {/* Backdrop */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50" 
              onClick={closeMenu}
            />
            
            {/* Sidebar Drawer */}
            <motion.div 
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', bounce: 0, duration: 0.3 }}
              className="relative flex w-72 flex-col bg-white shadow-xl h-full"
            >
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <span className="text-lg font-bold text-gray-900">LANES</span>
              <button 
                onClick={closeMenu}
                className="p-2 text-gray-500 hover:bg-gray-100 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Navigation */}
              <div className="space-y-1">
                <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Navigation</h3>
                {navItems.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={closeMenu}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors font-medium text-sm ${
                        isActive
                          ? 'bg-blue-50 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                      {item.name}
                    </Link>
                  );
                })}
              </div>

              {/* Trending Locations */}
              <div className="space-y-1">
                <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" />
                  Trending Hotspots
                </h3>
                <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group">
                  <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-500" /> Espana Blvd</span>
                  <span className="text-xs text-gray-400 group-hover:text-gray-600">12</span>
                </div>
                <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group">
                  <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-500" /> Taft Ave</span>
                  <span className="text-xs text-gray-400 group-hover:text-gray-600">8</span>
                </div>
                <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group">
                  <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-400" /> EDSA-Kamuning</span>
                  <span className="text-xs text-gray-400 group-hover:text-gray-600">5</span>
                </div>
              </div>

              {/* Saved Places */}
              <div className="space-y-1 relative" ref={dropdownRef}>
                <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Heart className="w-3.5 h-3.5" />
                  Saved Places
                </h3>
                
                {savedPlacesLoading ? (
                  <div className="px-3 py-2 animate-pulse flex flex-col gap-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ) : (
                  <>
                    {visiblePlaces.length > 0 ? (
                      visiblePlaces.map((place) => (
                        <div
                          key={place.id}
                          onClick={() => {
                            closeMenu();
                            router.push(`/map?lat=${place.latitude}&lng=${place.longitude}&zoom=16&panel=saveplace&tab=list`);
                          }}
                          className={`px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex items-center justify-between select-none caret-transparent ${place.pin_order !== null ? 'bg-amber-50/30' : ''}`}
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <div className="w-6 h-6 flex items-center justify-center bg-blue-100 rounded-full text-xs shrink-0 select-none pointer-events-none">
                              {place.icon || "📍"}
                            </div>
                            <span className="truncate select-none pointer-events-none">{place.name}</span>
                          </div>
                          {place.pin_order !== null && <Pin className="w-3 h-3 text-amber-500 fill-amber-500 shrink-0 ml-2" />}
                        </div>
                      ))
                    ) : (
                      <div className="px-3 py-2 text-sm text-gray-500 select-none">
                        <p>No saved places yet.</p>
                      </div>
                    )}

                    {hiddenPlaces.length > 0 && (
                      <>
                        {isDropdownOpen && (
                          <div className="space-y-1">
                            {hiddenPlaces.map((place) => (
                              <div
                                key={place.id}
                                onClick={() => {
                                  setIsDropdownOpen(false);
                                  closeMenu();
                                  router.push(`/map?lat=${place.latitude}&lng=${place.longitude}&zoom=16&panel=saveplace&tab=list`);
                                }}
                                className={`px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex items-center justify-between select-none caret-transparent ${place.pin_order !== null ? 'bg-amber-50/30' : ''}`}
                              >
                                <div className="flex items-center gap-3 overflow-hidden">
                                  <div className="w-6 h-6 flex items-center justify-center bg-blue-100 rounded-full text-xs shrink-0 select-none pointer-events-none">
                                    {place.icon || "📍"}
                                  </div>
                                  <span className="truncate select-none pointer-events-none">{place.name}</span>
                                </div>
                                {place.pin_order !== null && <Pin className="w-3 h-3 text-amber-500 fill-amber-500 shrink-0 ml-2" />}
                              </div>
                            ))}
                          </div>
                        )}

                        <button
                          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                          className="flex items-center justify-between w-full px-3 text-xs font-medium text-gray-500 hover:text-gray-700 py-1.5 transition-colors"
                        >
                          {isDropdownOpen ? 'Show less' : `View ${hiddenPlaces.length} more`}
                          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>
                      </>
                    )}

                    <div className="px-3 pt-2 pb-1">
                      <button
                        onClick={() => {
                          closeMenu();
                          router.push('/map?panel=saveplace&tab=add');
                        }}
                        className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium text-xs px-2 py-1.5 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors w-full justify-center select-none"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        Add a Place
                      </button>
                    </div>
                  </>
                )}
              </div>

              <EmergencyHotlinesCard />
            </div>

            <div className="p-4 border-t border-gray-100 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom)+1rem)] md:pb-4">
              <Link
                href="/settings"
                onClick={closeMenu}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors font-medium text-sm text-gray-700 hover:bg-gray-100"
              >
                <Settings className="w-5 h-5 text-gray-500" />
                Settings
              </Link>
            </div>
          </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
