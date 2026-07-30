import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { formatDistanceToNow } from 'date-fns';
import { MapPin, ArrowUpCircle, ArrowDownCircle, AlertTriangle, ShieldCheck, MessageSquare, Share, Map as MapIcon, ChevronLeft, ChevronRight, X, ZoomIn, ZoomOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { FeedPost } from './feedApi';
import { useToast } from '@/shared/ui';

interface PostItemProps {
  post: FeedPost;
  onVote: (reportId: number, type: 'upvote' | 'downvote') => void;
  onViewMap?: (lat: number, lng: number) => void;
  isExpanded?: boolean;
  initialMediaIndex?: number;
}

export function PostItem({ post, onVote, onViewMap, isExpanded = false, initialMediaIndex = 0 }: PostItemProps) {
  const router = useRouter();
  const { info, success, error: showError } = useToast();
  const [currentMediaIndex, setCurrentMediaIndex] = useState(initialMediaIndex);
  const [isFullscreenMediaOpen, setIsFullscreenMediaOpen] = useState(false);
  const [zoomScale, setZoomScale] = useState(1);

  const closeMediaViewer = () => {
    setIsFullscreenMediaOpen(false);
    setZoomScale(1);
    if (window.history.state?.mediaViewer) {
      window.history.back();
    }
  };

  useEffect(() => {
    if (isFullscreenMediaOpen) {
      document.body.style.overflow = 'hidden';
      if (!window.history.state?.mediaViewer) {
        window.history.pushState({ mediaViewer: true }, '');
      }

      const handlePopState = () => {
        setIsFullscreenMediaOpen(false);
      };
      
      window.addEventListener('popstate', handlePopState);
      return () => {
        document.body.style.overflow = '';
        window.removeEventListener('popstate', handlePopState);
      };
    } else {
      document.body.style.overflow = '';
    }
  }, [isFullscreenMediaOpen]);
  
  // Touch swipe gestures
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEndEvent = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (zoomScale > 1) return;

    const count = post.media_urls?.length || 0;
    if (count > 1) {
      if (isLeftSwipe) { setCurrentMediaIndex(prev => (prev < count - 1 ? prev + 1 : 0)); setZoomScale(1); }
      if (isRightSwipe) { setCurrentMediaIndex(prev => (prev > 0 ? prev - 1 : count - 1)); setZoomScale(1); }
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'extreme': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'extreme': return 'Extreme Severity';
      case 'high': return 'High Severity';
      case 'medium': return 'Moderate Severity';
      default: return 'Low Severity';
    }
  };

  const formatDistance = (meters?: number) => {
    if (meters === undefined || meters === null) return null;
    if (meters < 1000) return `${Math.round(meters)}m away`;
    return `${(meters / 1000).toFixed(1)}km away`;
  };

  const handleShare = () => {
    try {
      if (navigator.share) {
        navigator.share({
          title: 'LANES Flood Report',
          text: post.content || post.report?.raw_text || "Flood Report",
          url: `${window.location.origin}/feed/${post.id}`
        });
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(`${window.location.origin}/feed/${post.id}`);
        success("Link copied to clipboard!");
      } else {
        showError("Share API is not supported on this device/network.");
      }
    } catch (err) {
      showError("Failed to share link");
    }
  };

  return (
    <article className="py-6 px-4 sm:px-6 border-b border-gray-100 last:border-b-0 bg-white">
      
      {/* Header Area */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-100 to-blue-200 flex items-center justify-center border border-blue-300">
            {post.author_avatar ? (
              <img src={post.author_avatar} alt="avatar" className="w-full h-full rounded-full object-cover" />
            ) : (
              <span className="font-bold text-blue-700 text-sm">
                {post.author_name ? post.author_name[0].toUpperCase() : 'E'}
              </span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 text-sm">
                {post.author_name || 'External Source'}
              </span>
              {post.report?.status === 'approved' && (
                <span title="Verified by Admin">
                  <ShieldCheck className="w-4 h-4 text-blue-500" />
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5 flex-wrap">
              <span>{formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}</span>
              {post.location_tag && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1 font-semibold text-gray-600">
                    <MapPin className="w-3 h-3 text-red-500" />
                    {post.location_tag}
                  </span>
                </>
              )}
              {post.distance_meters !== undefined && post.distance_meters !== null && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1 font-medium text-blue-600">
                    <MapPin className="w-3 h-3" />
                    {formatDistance(post.distance_meters)}
                  </span>
                </>
              )}

            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1.5">
          {post.report && (
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 ${getSeverityColor(post.report.severity)}`}>
              <AlertTriangle className="w-3.5 h-3.5" />
              {getSeverityLabel(post.report.severity)}
            </span>
          )}
          {post.report?.human_readable_location && onViewMap && (
            <button 
              onClick={() => {
                if (post.report?.geometry?.type === 'Point') {
                  const [lng, lat] = post.report.geometry.coordinates as number[];
                  onViewMap(lat, lng);
                } else if (post.report?.geometry?.type === 'LineString') {
                  const coords = post.report.geometry.coordinates as number[][];
                  if (coords.length > 0) {
                    const [lng, lat] = coords[0];
                    onViewMap(lat, lng);
                  }
                }
              }}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors max-w-[220px] sm:max-w-[300px]"
              title="View on Map"
            >
              <MapPin className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate hover:underline">{post.report.human_readable_location}</span>
            </button>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="mb-4">
        <p className="text-gray-800 text-[15px] leading-relaxed whitespace-pre-wrap">
          {post.content}
        </p>

        {/* Media rendering */}
        {(() => {
          if (!post.media_urls || post.media_urls.length === 0) return null;

          const count = post.media_urls.length;

          // Expanded view (Carousel)
          if (isExpanded) {
            const url = post.media_urls[currentMediaIndex];
            const isVideo = url.match(/\.(mp4|webm|mov|ogg)$/i) || url.includes('/video/upload/');
            
            return (
              <div 
                className="mt-4 relative rounded-xl overflow-hidden bg-black flex items-center justify-center min-h-[300px] max-h-[600px] cursor-pointer"
                onClick={() => setIsFullscreenMediaOpen(true)}
              >
                {isVideo ? (
                  <video src={url} className="max-w-full max-h-[600px] object-contain pointer-events-none" />
                ) : (
                  <img src={url} alt={`Media ${currentMediaIndex + 1}`} className="max-w-full max-h-[600px] object-contain pointer-events-none" />
                )}
                
                {count > 1 && (
                  <>
                    <button 
                      onClick={(e) => { e.stopPropagation(); setCurrentMediaIndex((prev) => (prev > 0 ? prev - 1 : count - 1)); }}
                      className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/75 text-white p-2 rounded-full transition-colors backdrop-blur-sm z-10"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <button 
                      onClick={(e) => { e.stopPropagation(); setCurrentMediaIndex((prev) => (prev < count - 1 ? prev + 1 : 0)); }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/75 text-white p-2 rounded-full transition-colors backdrop-blur-sm z-10"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                    <div className="absolute bottom-3 left-1/2 -translate-y-1/2 bg-black/50 text-white text-xs px-2.5 py-1 rounded-full backdrop-blur-sm pointer-events-none z-10">
                      {currentMediaIndex + 1} / {count}
                    </div>
                  </>
                )}
              </div>
            );
          }

          // Feed List view (Grid)
          let gridContent = null;

          const renderCell = (index: number, extraClass: string = "", overlayIndex?: number) => {
            const url = post.media_urls![index];
            const isVideo = url.match(/\.(mp4|webm|mov|ogg)$/i) || url.includes('/video/upload/');
            return (
              <div 
                key={index} 
                className={`relative w-full h-full overflow-hidden cursor-pointer hover:opacity-90 transition-opacity ${extraClass}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (!isExpanded) {
                    router.push(`/feed/${post.id}?media=${index}`);
                  } else {
                    setCurrentMediaIndex(index);
                    setIsFullscreenMediaOpen(true);
                  }
                }}
              >
                {isVideo ? (
                  <video src={url} className="w-full h-full object-cover bg-black" />
                ) : (
                  <img src={url} alt="Post attachment" className="w-full h-full object-cover" loading="lazy" />
                )}
                {overlayIndex === index && count > 5 && (
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center pointer-events-none">
                    <span className="text-white text-3xl font-bold">+{count - 5}</span>
                  </div>
                )}
              </div>
            );
          };

          if (count === 1) {
            gridContent = (
              <div className="w-full max-h-[500px]">
                {renderCell(0, "max-h-[500px]")}
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
            <div className="mt-3 rounded-2xl overflow-hidden border border-gray-100 bg-gray-100">
              {gridContent}
            </div>
          );
        })()}
      </div>

      {/* Interaction Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-gray-50 rounded-full border border-gray-200 p-1">
            <button 
              onClick={() => onVote(post.id, 'upvote')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full transition-colors text-sm font-medium ${
                post.user_interaction === 'upvote' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-600 hover:bg-gray-200'
              }`}
            >
              <ArrowUpCircle className={`w-4 h-4 ${post.user_interaction === 'upvote' ? 'fill-blue-200' : ''}`} />
              <span>{post.upvotes}</span>
            </button>
            
            <div className="w-px h-4 bg-gray-300 mx-1"></div>
            
            <button 
              onClick={() => onVote(post.id, 'downvote')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full transition-colors text-sm font-medium ${
                post.user_interaction === 'downvote' 
                  ? 'bg-red-100 text-red-700' 
                  : 'text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span>{post.downvotes}</span>
              <ArrowDownCircle className={`w-4 h-4 ${post.user_interaction === 'downvote' ? 'fill-red-200' : ''}`} />
            </button>
          </div>

          <button 
            onClick={() => {
              if (isExpanded) {
                // Already expanded, maybe focus the input
              } else {
                router.push(`/feed/${post.id}`);
              }
            }}
            className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            <span>{post.comment_count}</span>
          </button>
          
          <button onClick={handleShare} className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors">
            <Share className="w-4 h-4" />
            <span>Share</span>
          </button>
        </div>

        {post.report?.geometry && onViewMap && (
          <button 
            onClick={() => {
              if (post.report?.geometry?.type === 'Point') {
                const [lng, lat] = post.report.geometry.coordinates as number[];
                onViewMap(lat, lng);
              } else if (post.report?.geometry?.type === 'LineString') {
                const coords = post.report.geometry.coordinates as number[][];
                if (coords.length > 0) {
                  const [lng, lat] = coords[0];
                  onViewMap(lat, lng);
                }
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg text-sm font-medium transition-colors border border-blue-100"
          >
            <MapIcon className="w-4 h-4" />
            <span>View on Map</span>
          </button>
        )}
      </div>

      {/* Fullscreen Media Modal */}
      {isFullscreenMediaOpen && post.media_urls && post.media_urls.length > 0 && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[99999] bg-black flex flex-col">
          {/* Header */}
          <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center z-50 bg-gradient-to-b from-black/60 to-transparent">
            <span className="text-white font-medium text-sm">
              {currentMediaIndex + 1} of {post.media_urls.length}
            </span>
            <button 
              onClick={closeMediaViewer}
              className="text-white p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Media Content */}
          <div 
            className="flex-1 flex items-center justify-center overflow-hidden touch-none"
            onTouchStart={onTouchStart}
            onTouchMove={onTouchMove}
            onTouchEnd={onTouchEndEvent}
          >
            {(() => {
              const url = post.media_urls[currentMediaIndex];
              const isVideo = url.match(/\.(mp4|webm|mov|ogg)$/i) || url.includes('/video/upload/');
              return isVideo ? (
                <video src={url} controls autoPlay className="w-full max-h-full object-contain" />
              ) : (
                <TransformWrapper
                  initialScale={1}
                  minScale={1}
                  maxScale={4}
                  centerOnInit
                  onTransformed={(ref) => setZoomScale(ref.state.scale)}
                >
                  {({ zoomIn, zoomOut, resetTransform }) => (
                    <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }} contentStyle={{ width: "100%", height: "100%", display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <img 
                        src={url} 
                        alt="Fullscreen Media" 
                        className="w-full max-h-full object-contain select-none pointer-events-none" 
                      />
                    </TransformComponent>
                  )}
                </TransformWrapper>
              );
            })()}
          </div>

          {/* Navigation Controls (Desktop primarily, but visible if multiple) */}
          {post.media_urls.length > 1 && (
            <>
              <button 
                onClick={(e) => { e.stopPropagation(); setCurrentMediaIndex(prev => (prev > 0 ? prev - 1 : post.media_urls!.length - 1)); setZoomScale(1); }}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-white p-3 hover:bg-white/20 rounded-full transition-colors"
              >
                <ChevronLeft className="w-8 h-8" />
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); setCurrentMediaIndex(prev => (prev < post.media_urls!.length - 1 ? prev + 1 : 0)); setZoomScale(1); }}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white p-3 hover:bg-white/20 rounded-full transition-colors"
              >
                <ChevronRight className="w-8 h-8" />
              </button>
            </>
          )}
        </div>,
        document.body
      )}
    </article>
  );
}
