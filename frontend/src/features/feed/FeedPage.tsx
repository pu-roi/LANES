"use client";

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { getFeed, votePost, FeedPost } from './feedApi';
import { PostItem } from './PostItem';
import { CreatePostModal } from './CreatePostModal';
import { Loader2, Filter, Image as ImageIcon, Video, MapPin, Menu, X, Map, Rss, MessageSquarePlus, Settings, TrendingUp, Flame, Heart, Phone } from 'lucide-react';
import { useToast } from '@/shared/ui';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';

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
  const photoInputRef = React.useRef<HTMLInputElement>(null);
  const videoInputRef = React.useRef<HTMLInputElement>(null);

  // Auto-open modal if user just logged in from a draft redirect
  useEffect(() => {
    if (searchParams.get('openPostModal') === 'true') {
      setIsCreateModalOpen(true);
      window.history.replaceState(null, '', '/feed');
    }
  }, [searchParams]);

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

              <button className="pb-2.5 text-gray-500 hover:text-blue-600 transition-colors flex items-center gap-1.5 text-sm font-medium">
                <Filter className="w-4 h-4" />
                Filters
              </button>
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
                onViewMap={(lat, lng) => router.push(`/map?lat=${lat}&lng=${lng}&zoom=16`)} 
              />
            ))}
          </div>

      {/* Create Post Modal */}
      {isCreateModalOpen && (
        <CreatePostModal 
          onClose={() => {
            setIsCreateModalOpen(false);
            setPreselectedFiles([]);
          }} 
          initialFiles={preselectedFiles}
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
              <div className="space-y-1">
                <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Heart className="w-3.5 h-3.5" />
                  Saved Places
                </h3>
                <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex items-center gap-3">
                  <MapPin className="w-4 h-4 text-blue-500" />
                  <span>Home</span>
                </div>
                <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex items-center gap-3">
                  <MapPin className="w-4 h-4 text-purple-500" />
                  <span>Office</span>
                </div>
              </div>

              {/* Emergency Hotlines */}
              <div className="space-y-1">
                <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Phone className="w-3.5 h-3.5" />
                  Emergency
                </h3>
                <div className="px-3 py-2.5 text-sm text-red-700 bg-red-50 hover:bg-red-100 border border-red-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center">
                  <span className="font-semibold">NDRRMC</span>
                  <span className="text-xs font-mono">911</span>
                </div>
                <div className="px-3 py-2.5 mt-2 text-sm text-red-700 bg-red-50 hover:bg-red-100 border border-red-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center">
                  <span className="font-semibold">Red Cross</span>
                  <span className="text-xs font-mono">143</span>
                </div>
              </div>
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
