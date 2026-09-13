import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { formatDistanceToNow } from 'date-fns';
import { MapPin, ArrowUpCircle, ArrowDownCircle, AlertTriangle, ShieldCheck, MessageSquare, Share, Map as MapIcon, ChevronLeft, ChevronRight, X, ZoomIn, ZoomOut, MoreHorizontal, Pencil, History, Loader2, Flag } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { FeedPost, getPostEditHistory, updatePost, reportPost } from './feedApi';
import { useToast, MediaViewer, Select } from '@/shared/ui';
import { useAuth } from '@/hooks/useAuth';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { computeCenterCoordinate } from "@/features/map/mapGeoUtils";
interface PostItemProps {
  post: FeedPost;
  onVote: (reportId: number, type: 'upvote' | 'downvote') => void;
  onViewMap?: (lat: number, lng: number) => void;
  isExpanded?: boolean;
  initialMediaIndex?: number;
  onPostClick?: (postId: number, initialMediaIndex?: number) => void;
}

const REPORT_REASON_OPTIONS = [
  { value: 'spam_scam', label: 'Spam or scam' },
  { value: 'misinformation', label: 'Misinformation' },
  { value: 'harassment_hate', label: 'Harassment or hate' },
  { value: 'explicit_violent', label: 'Explicit or violent content' },
  { value: 'other', label: 'Other' },
];

export function PostItem({ post, onVote, onViewMap, isExpanded = false, initialMediaIndex = 0, onPostClick }: PostItemProps) {
  const router = useRouter();
  const { info, success, error: showError } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [currentMediaIndex, setCurrentMediaIndex] = useState(initialMediaIndex);
  const [isFullscreenMediaOpen, setIsFullscreenMediaOpen] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [editContent, setEditContent] = useState(post.content);
  const [editLocation, setEditLocation] = useState(post.location_tag || '');
  const [isReporting, setIsReporting] = useState(false);
  const [reportReason, setReportReason] = useState('spam_scam');
  const [reportDetails, setReportDetails] = useState('');
  const isAuthor = user?.id === post.user_id;
  const historyQuery = useQuery({ queryKey: ['post-history', post.id], queryFn: () => getPostEditHistory(post.id), enabled: isHistoryOpen });
  const editMutation = useMutation({
    mutationFn: () => updatePost(post.id, { content: editContent.trim(), media_urls: post.media_urls || [], location_tag: editLocation.trim() || undefined, location_lat: post.location_lat, location_lng: post.location_lng }),
    onSuccess: () => { success('Post updated successfully.'); queryClient.invalidateQueries({ queryKey: ['feed'] }); queryClient.invalidateQueries({ queryKey: ['post', post.id] }); setIsEditing(false); },
    onError: (err: unknown) => showError('Failed to update post', err instanceof Error ? err.message : 'Please try again.'),
  });
  const reportMutation = useMutation({ mutationFn: () => reportPost(post.id, reportReason, reportDetails || undefined), onSuccess: () => { success('Report submitted for moderator review.'); setIsReporting(false); }, onError: (err: unknown) => showError('Could not submit report', err instanceof Error ? err.message : 'Please try again.') });

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case "extreme":
        return "bg-red-100 text-red-800 border-red-300";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "medium":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "low":
      default:
        return "bg-lime-100 text-lime-800 border-lime-300";
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case "extreme":
        return "Extreme (Impassable)";
      case "high":
        return "High (Hazardous)";
      case "medium":
        return "Medium (Warning)";
      case "low":
      default:
        return "Low (Passable)";
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

  const displayLocation = post.location_tag || post.report?.human_readable_location || (post.report?.barangay ? `Brgy. ${post.report.barangay}` : null);

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
              {post.updated_at && new Date(post.updated_at).getTime() > new Date(post.created_at).getTime() && <span className="text-gray-400">• Edited</span>}
              {displayLocation && (
                <>
                  <span>•</span>
                  {onViewMap && ((post.location_lat && post.location_lng) || post.report?.geometry) ? (
                    <button
                      type="button"
                      onClick={() => {
                        if (post.report?.geometry) {
                          const geomType = post.report.geometry.type;
                          const coords = post.report.geometry.coordinates;
                          try {
                            const center = computeCenterCoordinate({ type: geomType, coordinates: coords });
                            if (center) onViewMap(center[1], center[0]);
                          } catch (e) { console.error(e); }
                        } else if (post.location_lat && post.location_lng) {
                          onViewMap(post.location_lat, post.location_lng);
                        }
                      }}
                      className="flex items-center gap-1 font-semibold text-gray-600 hover:text-blue-600 transition-colors group"
                      title="View on Map"
                    >
                      <MapPin className="w-3 h-3 text-red-500 group-hover:text-blue-500 transition-colors" />
                      <span className="group-hover:underline">{displayLocation}</span>
                    </button>
                  ) : (
                    <span className="flex items-center gap-1 font-semibold text-gray-600">
                      <MapPin className="w-3 h-3 text-red-500" />
                      {displayLocation}
                    </span>
                  )}
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

        <div className="flex items-start gap-1.5">
          {post.report && (
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 ${getSeverityColor(post.report.severity)}`}>
              <AlertTriangle className="w-3.5 h-3.5" />
              {getSeverityLabel(post.report.severity)}
            </span>
          )}
          <div className="relative">
            <button type="button" aria-label="Post actions" onClick={() => setIsMenuOpen((value) => !value)} className="p-1.5 rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-800"><MoreHorizontal className="w-5 h-5" /></button>
            {isMenuOpen && <div className="absolute right-0 top-9 z-20 w-48 rounded-xl border border-gray-200 bg-white p-1 shadow-lg">
              {isAuthor && <button type="button" onClick={() => { setEditContent(post.content); setEditLocation(post.location_tag || ''); setIsEditing(true); setIsMenuOpen(false); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"><Pencil className="w-4 h-4" />Edit Post</button>}
              {!isAuthor && <button type="button" onClick={() => { setIsReporting(true); setIsMenuOpen(false); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"><Flag className="w-4 h-4" />Report Post</button>}
              <button type="button" onClick={() => { setIsHistoryOpen(true); setIsMenuOpen(false); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"><History className="w-4 h-4" />View Edit History</button>
            </div>}
          </div>
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
                    if (onPostClick) {
                      onPostClick(post.id, index);
                    } else {
                      router.push(`/feed/${post.id}?media=${index}`);
                    }
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
                if (onPostClick) {
                  onPostClick(post.id);
                } else {
                  router.push(`/feed/${post.id}`);
                }
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

        {/* View on Map button — only shown for flood reports (regular post locations use the clickable red pin instead) */}
        {post.report?.geometry && onViewMap && (
          <button 
            onClick={() => {
              const geomType = post.report?.geometry?.type;
              const coords = post.report?.geometry?.coordinates;
              if (!geomType || !coords) return;
              try {
                const center = computeCenterCoordinate({ type: geomType, coordinates: coords });
                if (center) onViewMap(center[1], center[0]);
              } catch (e) {
                console.error("Failed to calculate geometry center", e);
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
      <MediaViewer 
        mediaUrls={post.media_urls || []} 
        initialIndex={currentMediaIndex}
        isOpen={isFullscreenMediaOpen}
        onClose={() => setIsFullscreenMediaOpen(false)}
      />
      {typeof document !== 'undefined' && createPortal(
        <>
      {isEditing && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"><div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-bold text-slate-900">Edit Post</h2><button onClick={() => setIsEditing(false)} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100"><X className="w-5 h-5" /></button></div><textarea value={editContent} onChange={(event) => setEditContent(event.target.value)} className="min-h-40 w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-blue-500" /><input value={editLocation} onChange={(event) => setEditLocation(event.target.value)} placeholder="Location label (optional)" className="mt-3 w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-blue-500" /><div className="mt-4 flex justify-end gap-2"><button onClick={() => setIsEditing(false)} className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button><button disabled={!editContent.trim() || editMutation.isPending} onClick={() => editMutation.mutate()} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{editMutation.isPending ? 'Saving…' : 'Save changes'}</button></div></div></div>}
      {isHistoryOpen && <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4"><div className="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-bold text-slate-900">Edit History</h2><button onClick={() => setIsHistoryOpen(false)} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100"><X className="w-5 h-5" /></button></div>{historyQuery.isLoading && <div className="flex justify-center py-8 text-slate-500"><Loader2 className="h-5 w-5 animate-spin" /></div>}{historyQuery.isError && <p className="py-6 text-center text-sm text-red-600">Could not load edit history.</p>}{historyQuery.data?.length === 0 && <p className="py-6 text-center text-sm text-slate-500">This post has not been edited.</p>}{historyQuery.data?.map((entry) => <div key={entry.id} className="border-t border-slate-100 py-4"><p className="mb-2 text-xs font-medium text-slate-500">Edit {entry.version} · {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}</p><div className="grid gap-3 sm:grid-cols-2"><div><p className="mb-1 text-xs font-semibold text-slate-500">Previous</p><p className="whitespace-pre-wrap text-sm text-slate-700">{entry.previous_content}</p></div><div><p className="mb-1 text-xs font-semibold text-slate-500">Updated</p><p className="whitespace-pre-wrap text-sm text-slate-700">{entry.updated_content}</p></div></div></div>)}</div></div>}
      {isReporting && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">Report Post</h2>
              <button
                onClick={() => setIsReporting(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="mb-4 text-sm text-slate-600">Reports are private and reviewed by moderators.</p>

            <div className="mb-3">
              <Select
                label="Reason"
                options={REPORT_REASON_OPTIONS}
                value={reportReason}
                onChange={(e) => setReportReason(String(e.target.value))}
                placeholder="Select a reason..."
                className="w-full"
              />
            </div>

            <textarea
              value={reportDetails}
              onChange={(event) => setReportDetails(event.target.value)}
              placeholder={reportReason === 'other' ? 'Please explain why (required)' : 'Optional details'}
              className="mt-1 min-h-24 w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-400"
            />

            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setIsReporting(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={reportMutation.isPending || (reportReason === 'other' && !reportDetails.trim())}
                onClick={() => reportMutation.mutate()}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60 transition-colors"
              >
                {reportMutation.isPending ? 'Submitting…' : 'Submit report'}
              </button>
            </div>
          </div>
        </div>
      )}
        </>,
        document.body,
      )}
    </article>
  );
}
