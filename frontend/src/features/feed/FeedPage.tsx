"use client";

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import { getFeed, votePost, FeedPost } from './feedApi';
import { PostItem } from './PostItem';
import { CreatePostModal } from './CreatePostModal';
import { Loader2, Filter, Image as ImageIcon, Video, MapPin } from 'lucide-react';
import { useToast } from '@/shared/ui';

export function FeedPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { error: showError } = useToast();
  const [tab, setTab] = useState<'recent' | 'nearby'>('recent');
  const [userLocation, setUserLocation] = useState<{lat: number, lng: number} | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
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

  return (
    <>
      {/* Header with Tabs */}
          <div className="bg-transparent border-b border-gray-200 px-4 pt-2 pb-0 flex flex-col justify-end mb-2">
            <h1 className="text-xl font-extrabold tracking-tight mb-2 px-2">Community Feed</h1>
            
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

      {isCreateModalOpen && (
        <CreatePostModal 
          onClose={() => {
            setIsCreateModalOpen(false);
            setPreselectedFiles([]);
          }} 
          initialFiles={preselectedFiles}
        />
      )}
    </>
  );
}
