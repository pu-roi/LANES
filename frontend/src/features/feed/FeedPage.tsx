"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { getFeed, votePost, FeedPost, FeedResponse, VoteResponse } from './feedApi';
import { PostItem } from './PostItem';
import { CreatePostModal } from './CreatePostModal';
import { Loader2, Filter, Image as ImageIcon, Video, Menu, X, Map, Rss, MessageSquarePlus, TrendingUp, Flame, Heart, Plus, ChevronDown, Pin, MapPin, AlertTriangle } from 'lucide-react';
import { useToast, Button } from '@/shared/ui';
import { savedPlacesApi } from '@/features/places/savedPlacesApi';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { EmergencyHotlinesCard } from './components/EmergencyHotlinesCard';
import { resolveProfileCoordinates } from '@/constants/locations';

export function FeedPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { error: showError, info: showInfo } = useToast();
  const [tab, setTab] = useState<'recent' | 'nearby'>('recent');
  const [userLocation, setUserLocation] = useState<{lat: number, lng: number} | null>(null);
  const [locationLabel, setLocationLabel] = useState<string | null>(null);
  const [locationSource, setLocationSource] = useState<'gps' | 'profile' | 'saved' | null>(null);
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

  const { user, isAuthenticated } = useAuth();

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

  // Auto-open modal if user just came back from map location pick or login redirect, or refreshed while composing
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
    } else if (typeof window !== 'undefined') {
      const rawDraft = localStorage.getItem('lanes_draft_post') || sessionStorage.getItem('lanes_draft_post');
      if (rawDraft) {
        try {
          const parsed = JSON.parse(rawDraft);
          if (parsed.isModalOpen) {
            setIsCreateModalOpen(true);
          }
        } catch (e) {}
      }
    }
  }, [searchParams, router]);

  // Round coordinates to ~110m (3 decimals) to avoid GPS jitter cache-thrashing
  const snapCoord = (val: number) => Math.round(val * 1000) / 1000;

  const switchToProfileLocation = (quiet = false): boolean => {
    const profileAddr = user?.profile?.address;
    if (profileAddr?.barangay) {
      const coords = resolveProfileCoordinates(profileAddr.barangay, profileAddr.city_municipality);
      if (coords) {
        setUserLocation(coords);
      }
      const bgyLabel = `Brgy. ${profileAddr.barangay}${profileAddr.city_municipality ? `, ${profileAddr.city_municipality}` : ''}`;
      setLocationLabel(bgyLabel);
      setLocationSource('profile');
      if (!quiet) {
        showInfo("Using Profile Address", `Showing feed near your registered address in ${bgyLabel}.`);
      }
      return true;
    }
    return false;
  };

  const requestGpsLocation = (silentFallback = false) => {
    if (!('geolocation' in navigator)) {
      if (!silentFallback) showError("Not Supported", "Geolocation is not supported by your browser.");
      const fallbackSuccess = switchToProfileLocation(silentFallback);
      if (!fallbackSuccess && !silentFallback) {
        showError("Location Required", "Please update your registered address in your Profile.");
      }
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const snappedLat = snapCoord(pos.coords.latitude);
        const snappedLng = snapCoord(pos.coords.longitude);
        setUserLocation({ lat: snappedLat, lng: snappedLng });
        setLocationLabel("Current Location");
        setLocationSource('gps');
      },
      (_err) => {
        // 1. Fallback to registered profile address first
        const fallbackSuccess = switchToProfileLocation(silentFallback);
        if (!fallbackSuccess) {
          // 2. Secondary fallback to saved places
          const fallbackPlace = savedPlaces?.find((p) => p.name?.trim().toLowerCase() === 'home') || (savedPlaces?.[0]);
          if (fallbackPlace) {
            setUserLocation({ lat: snapCoord(fallbackPlace.latitude), lng: snapCoord(fallbackPlace.longitude) });
            setLocationLabel(fallbackPlace.name || "Saved Location");
            setLocationSource('saved');
            if (!silentFallback) {
              showInfo("Using Saved Place", `Showing feed near your saved "${fallbackPlace.name}" place.`);
            }
          } else if (!silentFallback) {
            showError("Location Required", "Please allow GPS location or complete your registered address in your Profile to view nearby posts.");
          }
        }
      },
      { timeout: 8000, maximumAge: 60000 }
    );
  };

  // Request location if nearby tab is clicked and we don't have it
  useEffect(() => {
    if (tab === 'nearby' && !userLocation) {
      requestGpsLocation(true);
    }
  }, [tab, userLocation, user, savedPlaces]);

  const feedQueryKey = ['feed', tab, userLocation?.lat, userLocation?.lng, locationSource];

  const { data, isLoading, isError, error } = useQuery({
    queryKey: feedQueryKey,
    queryFn: () => getFeed(userLocation?.lat, userLocation?.lng, tab, 0, 50),
    enabled: tab === 'recent' || (tab === 'nearby' && (userLocation !== null || isAuthenticated)),
  });

  // Sync resolved location name from backend if not already set
  useEffect(() => {
    if (data?.resolved_location_name && (!locationLabel || locationLabel === "your location")) {
      setLocationLabel(data.resolved_location_name);
      if (!locationSource) {
        setLocationSource('profile');
      }
    }
  }, [data?.resolved_location_name, locationLabel, locationSource]);


  const voteMutation = useMutation({
    mutationFn: ({ postId, type }: { postId: number; type: 'upvote' | 'downvote' }) => votePost(postId, type),
    onMutate: async ({ postId, type }) => {
      // Cancel outgoing refetches so they don't overwrite optimistic update
      await queryClient.cancelQueries({ queryKey: ['feed'] });

      // Snapshot previous feed state
      const previousFeed = queryClient.getQueryData<FeedResponse>(feedQueryKey);

      // Optimistically update target post in feed query cache
      if (previousFeed) {
        queryClient.setQueryData<FeedResponse>(feedQueryKey, {
          ...previousFeed,
          posts: previousFeed.posts.map((p) => {
            if (p.id !== postId) return p;

            let newUpvotes = p.upvotes || 0;
            let newDownvotes = p.downvotes || 0;
            let newInteraction: 'upvote' | 'downvote' | undefined = undefined;

            if (p.user_interaction === type) {
              // Toggle off (undo vote)
              if (type === 'upvote') newUpvotes = Math.max(0, newUpvotes - 1);
              if (type === 'downvote') newDownvotes = Math.max(0, newDownvotes - 1);
              newInteraction = undefined;
            } else if (p.user_interaction) {
              // Switch/flip between upvote and downvote
              if (type === 'upvote') {
                newUpvotes += 1;
                newDownvotes = Math.max(0, newDownvotes - 1);
                newInteraction = 'upvote';
              } else {
                newDownvotes += 1;
                newUpvotes = Math.max(0, newUpvotes - 1);
                newInteraction = 'downvote';
              }
            } else {
              // New vote from neutral state
              if (type === 'upvote') newUpvotes += 1;
              if (type === 'downvote') newDownvotes += 1;
              newInteraction = type;
            }

            return {
              ...p,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_interaction: newInteraction,
            };
          }),
        });
      }

      return { previousFeed };
    },
    onSuccess: (voteRes: VoteResponse, { postId }) => {
      // Lock in authoritative backend numbers
      queryClient.setQueryData<FeedResponse>(feedQueryKey, (old) => {
        if (!old) return old;
        return {
          ...old,
          posts: old.posts.map((p) => {
            if (p.id !== postId) return p;
            return {
              ...p,
              upvotes: voteRes.upvotes,
              downvotes: voteRes.downvotes,
              user_interaction: (voteRes.user_interaction as 'upvote' | 'downvote') || undefined,
            };
          }),
        };
      });
      // Synchronize single post query if opened
      queryClient.invalidateQueries({ queryKey: ['post', postId] });
    },
    onError: (err: any, _vars, context) => {
      // Rollback to snapshot on failure
      if (context?.previousFeed) {
        queryClient.setQueryData(feedQueryKey, context.previousFeed);
      }
      if (err.status === 401) {
        showError('Login Required', 'Please log in first to interact with posts!');
      } else {
        showError('Failed to vote', err.message || 'Could not register your vote.');
      }
    },
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
  };

  const handleSavedPlaceClick = (latitude: number, longitude: number) => {
    closeMenu();
    router.push(`/map?lat=${latitude}&lng=${longitude}&zoom=16`);
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('fly-to-location', {
        detail: { latitude, longitude, zoom: 16, duration: 1500 },
      }));
    }, 150);
  };

  const handleNavClick = (href: string) => {
    setIsMobileMenuOpen(false);
    router.push(href);
  };

  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  return (
    <>
      {/* Header with Tabs */}
          <div className="bg-transparent border-b border-gray-200 px-3 sm:px-4 pt-1 pb-0 flex flex-col justify-end">
            <div className="flex items-center gap-2.5 sm:gap-3 mb-2 px-1 sm:px-2">
              <button 
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden p-1.5 -ml-1 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors active:scale-95"
                aria-label="Open navigation menu"
              >
                <Menu className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
              <h1 className="text-lg sm:text-xl font-extrabold tracking-tight text-gray-900">Community Feed</h1>
            </div>
            
            <div className="flex justify-between items-end px-1 sm:px-2">
              <div className="flex gap-4 sm:gap-6">
                <button 
                  onClick={() => setTab('recent')}
                  className={`pb-2.5 sm:pb-3 text-xs sm:text-sm font-bold transition-colors relative ${
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
                  className={`pb-2.5 sm:pb-3 text-xs sm:text-sm font-bold transition-colors relative ${
                    tab === 'nearby' ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Nearby
                  {tab === 'nearby' && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 rounded-t-md"></div>
                  )}
                </button>
              </div>

              <Button variant="ghost" size="sm" className="text-gray-500 hover:text-blue-600 text-xs sm:text-sm px-2 sm:px-3">
                <Filter className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1 sm:mr-1.5" />
                Filters
              </Button>
            </div>
          </div>

          <div className="px-3 sm:px-0 pt-3 sm:pt-4">
            {/* Create Post Input Trigger */}
            <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-3.5 sm:p-4 mb-3 sm:mb-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                <span className="font-bold text-blue-700 text-sm">Me</span>
              </div>
              <button 
                onClick={() => setIsCreateModalOpen(true)}
                className="flex-1 min-w-0 bg-gray-100 hover:bg-gray-200 transition-colors rounded-full text-left px-3.5 sm:px-5 py-2.5 sm:py-3 text-gray-500 text-sm font-medium truncate"
              >
                <span className="sm:hidden">What's happening?</span>
                <span className="hidden sm:inline">What's happening in your area?</span>
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
            <div className="space-y-3 sm:space-y-4 mb-20">
              {tab === 'nearby' && (userLocation || locationLabel) && (
                <div className="space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-medium text-blue-700 bg-blue-50/90 border border-blue-200/70 rounded-xl px-3.5 py-2.5 shadow-xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <MapPin className="w-4 h-4 shrink-0 text-blue-500" />
                      <span className="truncate">
                        Showing posts near <strong className="font-semibold text-blue-900">{locationLabel || "your location"}</strong>
                        {locationSource === 'profile' && <span className="ml-1 text-blue-600 font-normal">(from Profile Address)</span>}
                        {locationSource === 'gps' && <span className="ml-1 text-blue-600 font-normal">(Current GPS)</span>}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-auto">
                      {locationSource !== 'gps' && (
                        <button
                          type="button"
                          onClick={() => requestGpsLocation(false)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-blue-700 hover:text-blue-800 bg-white hover:bg-blue-100/50 border border-blue-200 rounded-md transition-colors"
                        >
                          Use Current GPS
                        </button>
                      )}
                      {locationSource !== 'profile' && user?.profile?.address?.barangay && (
                        <button
                          type="button"
                          onClick={() => switchToProfileLocation(false)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-blue-700 hover:text-blue-800 bg-white hover:bg-blue-100/50 border border-blue-200 rounded-md transition-colors"
                        >
                          Use Profile Address
                        </button>
                      )}
                    </div>
                  </div>

                  {data?.expanded_radius && (
                    <div className="flex items-center gap-2 text-xs font-medium text-amber-800 bg-amber-50 border border-amber-200/80 rounded-xl px-3.5 py-2.5 shadow-xs">
                      <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
                      <span>No reports found within 5 km. Showing community posts within an expanded 15 km radius.</span>
                    </div>
                  )}
                </div>
              )}

              {tab === 'nearby' && !userLocation && !isLoading && !data && (
                <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-8 sm:p-12 text-center text-gray-600">
                  <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
                    <MapPin className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-gray-900 text-base mb-1">Location Required for Nearby Feed</h3>
                  <p className="text-sm text-gray-500 max-w-md mx-auto mb-4">
                    To see flood reports and posts near you, enable GPS or set your home address in your profile.
                  </p>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    <Button size="sm" onClick={() => requestGpsLocation(false)}>
                      Enable GPS
                    </Button>
                    {isAuthenticated ? (
                      <Button variant="outline" size="sm" onClick={() => router.push('/profile')}>
                        Set Profile Address
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm" onClick={() => router.push('/login')}>
                        Log In to Use Profile
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {isLoading && (
                <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center py-20">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
                  <p className="text-gray-500 text-sm font-medium">Fetching reports...</p>
                </div>
              )}

              {isError && (
                <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-8 text-center text-red-500">
                  <p>Failed to load feed.</p>
                  <p className="text-xs mt-2 opacity-70">{(error as Error).message}</p>
                </div>
              )}

              {data && data.posts.length === 0 && (
                <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-16 text-center text-gray-500">
                  <p className="font-medium text-lg text-gray-700">No reports found{tab === 'nearby' ? ' nearby' : ''}.</p>
                  <p className="text-sm mt-1">{tab === 'nearby' ? 'No community posts or flood reports were found in your area.' : 'Check back later or submit a new report.'}</p>
                </div>
              )}

              {data && data.posts.map((post: FeedPost) => (
                <PostItem 
                  key={post.id} 
                  post={post} 
                  onVote={handleVote}
                  onViewMap={(lat, lng) => {
                    // The URL also carries the target if the deferred map has
                    // not mounted yet. The event handles an already-open map.
                    router.push(`/map?lat=${lat}&lng=${lng}&zoom=16`);
                    setTimeout(() => {
                      window.dispatchEvent(new CustomEvent('fly-to-location', {
                        detail: { latitude: lat, longitude: lng, zoom: 16, duration: 1500 }
                      }));
                    }, 150);
                  }}
                />
              ))}
            </div>
          </div>

      {/* Create Post Modal */}
      {isCreateModalOpen && (
        <CreatePostModal 
          onClose={() => {
            setIsCreateModalOpen(false);
            setPreselectedFiles([]);
            setInitialLocation(null);
            if (typeof window !== 'undefined') {
              const rawDraft = localStorage.getItem('lanes_draft_post') || sessionStorage.getItem('lanes_draft_post');
              if (rawDraft) {
                try {
                  const parsed = JSON.parse(rawDraft);
                  parsed.isModalOpen = false;
                  localStorage.setItem('lanes_draft_post', JSON.stringify(parsed));
                  sessionStorage.setItem('lanes_draft_post', JSON.stringify(parsed));
                } catch (e) {}
              }
            }
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
                    <button
                      key={item.name}
                      type="button"
                      onClick={() => handleNavClick(item.href)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors font-medium text-sm text-left ${
                        isActive
                          ? 'bg-blue-50 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
                      }`}
                    >
                      <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                      {item.name}
                    </button>
                  );
                })}
              </div>

              {/* Trending Locations */}
              <div className="space-y-1">
                <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" />
                  Trending Hotspots
                </h3>
                <div 
                  onClick={() => handleNavClick("/map?lat=14.6091&lng=120.9899&zoom=15")}
                  className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group active:scale-98"
                >
                  <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-500" /> Espana Blvd</span>
                  <span className="text-xs text-gray-400 group-hover:text-gray-600">12</span>
                </div>
                <div 
                  onClick={() => handleNavClick("/map?lat=14.5648&lng=120.9932&zoom=15")}
                  className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group active:scale-98"
                >
                  <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-500" /> Taft Ave</span>
                  <span className="text-xs text-gray-400 group-hover:text-gray-600">8</span>
                </div>
                <div 
                  onClick={() => handleNavClick("/map?lat=14.6353&lng=121.0433&zoom=15")}
                  className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group active:scale-98"
                >
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
                          onClick={() => handleSavedPlaceClick(place.latitude, place.longitude)}
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
                                  handleSavedPlaceClick(place.latitude, place.longitude);
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

          </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
