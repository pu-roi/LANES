"use client";

import React, { useState, useMemo, useCallback, useRef, useEffect, createContext, useContext } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  getPost, getComments, postComment, votePost, voteComment,
  deleteComment, editComment, pinComment, searchUsers, CommentResponse
} from './feedApi';
import { PostItem } from './PostItem';
import { Loader2, ArrowLeft, Send, ArrowUp, ArrowDown, MessageSquare, X, Pin, Flag } from 'lucide-react';
import { useToast, Button } from '@/shared/ui';
import { formatCommentTime } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { ConfirmDialog } from '@/shared/ui';
import { useMediaQuery } from '@/hooks/useMediaQuery';

interface CommentNode extends CommentResponse {
  replies: CommentNode[];
}

const MAX_REPLIES = 3;
const MAX_CHARS = 250;
const ROOT_PAGE_SIZE = 10;
const AUTO_COLLAPSE_THRESHOLD = -2;

const PostContext = createContext<any>(null);

export function PostDetailPage({ postId, onBack }: { postId: number; onBack?: () => void }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { error: showError, success, info } = useToast();
  const { user } = useAuth();
  
  const isMobile = useMediaQuery("(max-width: 640px)");
  const maxDepth = isMobile ? 2 : 4;

  // ── comment input state ────────────────────────────────────────────
  const [commentText, setCommentText] = useState('');
  const [replyText, setReplyText] = useState('');
  const [replyingTo, setReplyingTo] = useState<{ id: number; author: string; content: string } | null>(null);

  // ── UI state ───────────────────────────────────────────────────────
  const [isolatedThreadId, setIsolatedThreadId] = useState<number | null>(null);
  const [commentSort, setCommentSort] = useState<'top' | 'recent'>('top');
  const [visibleRootCount, setVisibleRootCount] = useState(ROOT_PAGE_SIZE);

  // ── edit state ─────────────────────────────────────────────────────
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editText, setEditText] = useState('');

  // ── delete state ───────────────────────────────────────────────────
  const [commentToDelete, setCommentToDelete] = useState<number | null>(null);
  const [hiddenComments, setHiddenComments] = useState<Set<number>>(new Set());
  const pendingDeleteTimeouts = useRef<Record<number, NodeJS.Timeout>>({});

  // ── mention state ──────────────────────────────────────────────────
  const [mentionResults, setMentionResults] = useState<string[]>([]);
  const [activeMentionInput, setActiveMentionInput] = useState<'main' | 'reply' | null>(null);
  const mentionDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── queries ────────────────────────────────────────────────────────
  const { data: post, isLoading: postLoading, isError: postError } = useQuery({
    queryKey: ['post', postId],
    queryFn: () => getPost(postId),
  });

  const { data: comments, isLoading: commentsLoading } = useQuery({
    queryKey: ['comments', postId],
    queryFn: () => getComments(postId),
  });

  // ── tree builder ───────────────────────────────────────────────────
  const { commentTree, commentMap } = useMemo(() => {
    if (!comments) return { commentTree: [], commentMap: new Map<number, CommentNode>() };
    const map = new Map<number, CommentNode>();
    const roots: CommentNode[] = [];

    comments.forEach(c => map.set(c.id, { ...c, replies: [] }));
    comments.forEach(c => {
      const node = map.get(c.id)!;
      if (c.parent_id && map.has(c.parent_id)) {
        map.get(c.parent_id)!.replies.push(node);
      } else {
        roots.push(node);
      }
    });

    const sortNodes = (nodes: CommentNode[]) => {
      if (commentSort === 'top') {
        nodes.sort((a, b) => {
          const scoreA = a.upvotes - a.downvotes;
          const scoreB = b.upvotes - b.downvotes;
          return scoreB !== scoreA
            ? scoreB - scoreA
            : new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
      } else {
        nodes.sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      }
      nodes.forEach(node => sortNodes(node.replies));
    };
    sortNodes(roots);

    // Pinned comments always float to the very top of the root list
    roots.sort((a, b) => (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0));

    return { commentTree: roots, commentMap: map };
  }, [comments, commentSort]);

  // ── mutations ──────────────────────────────────────────────────────
  const voteMutation = useMutation({
    mutationFn: ({ type }: { type: 'upvote' | 'downvote' }) => votePost(postId, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['post', postId] });
      queryClient.invalidateQueries({ queryKey: ['feed'] });
    },
    onError: (err: any) => {
      if (err.status === 401) showError('Login Required', 'Please log in first to interact with posts!');
      else showError('Failed to vote', err.message);
    }
  });

  const commentVoteMutation = useMutation({
    mutationFn: ({ commentId, type }: { commentId: number; type: 'upvote' | 'downvote' }) =>
      voteComment(commentId, type),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comments', postId] }),
    onError: (err: any) => {
      if (err.status === 401) showError('Login Required', 'Please log in first!');
      else showError('Failed to vote on comment', err.message);
    }
  });

  const commentMutation = useMutation({
    mutationFn: ({ content, parentId }: { content: string; parentId?: number }) =>
      postComment(postId, content, parentId),
    onSuccess: () => {
      setCommentText('');
      setReplyText('');
      setReplyingTo(null);
      setMentionResults([]);
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
      queryClient.invalidateQueries({ queryKey: ['post', postId] });
      success('Comment added!');
    },
    onError: (err: any) => {
      if (err.status === 401) showError('Login Required', 'Please log in first!');
      else showError('Failed to post comment', err.message);
    }
  });

  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: number) => deleteComment(commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
    },
    onError: (err: any) => showError('Failed to delete comment', err?.response?.data?.detail || err?.message)
  });

  const editCommentMutation = useMutation({
    mutationFn: ({ commentId, content }: { commentId: number; content: string }) =>
      editComment(commentId, content),
    onSuccess: () => {
      setEditingCommentId(null);
      setEditText('');
      success('Comment updated');
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
    },
    onError: (err: any) => showError('Failed to edit comment', err?.message)
  });

  const pinCommentMutation = useMutation({
    mutationFn: (commentId: number) => pinComment(commentId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
      success(data.is_pinned ? 'Comment pinned' : 'Comment unpinned');
    },
    onError: (err: any) => showError('Failed to pin comment', err?.message)
  });

  // ── handlers ───────────────────────────────────────────────────────
  const handleVote = (_id: number, type: 'upvote' | 'downvote') => voteMutation.mutate({ type });

  const handleCommentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || commentText.length > MAX_CHARS) return;
    commentMutation.mutate({ content: commentText });
  };

  const handleReplySubmit = (e: React.FormEvent, parentId: number) => {
    e.preventDefault();
    if (!replyText.trim() || replyText.length > MAX_CHARS) return;
    commentMutation.mutate({ content: replyText, parentId });
  };

  const handleMentionInput = useCallback((text: string, inputKey: 'main' | 'reply') => {
    // Detect last @word in the text
    const match = text.match(/@(\w+)$/);
    if (match && match[1].length >= 1) {
      setActiveMentionInput(inputKey);
      if (mentionDebounceRef.current) clearTimeout(mentionDebounceRef.current);
      mentionDebounceRef.current = setTimeout(async () => {
        try {
          const results = await searchUsers(match[1]);
          setMentionResults(results);
        } catch {
          setMentionResults([]);
        }
      }, 250);
    } else {
      setMentionResults([]);
      setActiveMentionInput(null);
    }
  }, []);

  const insertMention = (username: string, inputKey: 'main' | 'reply') => {
    const replacer = (text: string) => text.replace(/@(\w+)$/, `@${username} `);
    if (inputKey === 'main') setCommentText(prev => replacer(prev));
    else setReplyText(prev => replacer(prev));
    setMentionResults([]);
    setActiveMentionInput(null);
  };

  // ── helper: is current user an admin/staff ─────────────────────────
  const isAdmin = user && (user as any).role && (user as any).role.name !== 'Commuter';
  const isPostAuthor = post && user && (post as any).author_name === (user as any).username;
  const canPin = isAdmin || isPostAuthor;

  const contextValue = {
    user, post, replyingTo, setReplyingTo, replyText, setReplyText,
    editingCommentId, setEditingCommentId, editText, setEditText,
    handleReplySubmit,
    commentMutation, editCommentMutation, deleteCommentMutation, commentVoteMutation, pinCommentMutation,
    activeMentionInput, setActiveMentionInput, mentionResults, setMentionResults,
    insertMention, handleMentionInput, setIsolatedThreadId, info, canPin,
    hiddenComments, setCommentToDelete, maxDepth
  };

  // ── loading / error states ─────────────────────────────────────────
  if (postLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center py-20 min-h-[500px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
        <p className="text-gray-500 text-sm font-medium">Loading post...</p>
      </div>
    );
  }

  if (postError || !post) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center text-red-500">
        <p>Post not found or failed to load.</p>
        <button
          onClick={() => { if (onBack) onBack(); else router.push('/feed'); }}
          className="mt-4 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg text-sm font-medium transition-colors"
        >
          Return
        </button>
      </div>
    );
  }

  // ── visible root slice ─────────────────────────────────────────────
  const rootsToShow = isolatedThreadId && commentMap.has(isolatedThreadId)
    ? null
    : commentTree.slice(0, visibleRootCount);
  const hasMoreRoots = !isolatedThreadId && commentTree.length > visibleRootCount;

  // ── render ─────────────────────────────────────────────────────────
  return (
    <PostContext.Provider value={contextValue}>
      <div className="flex flex-col gap-0 sm:gap-4 mb-20">
      {/* Sticky Header for Mobile */}
      <div className="sticky sm:hidden top-0 z-20 bg-white/80 backdrop-blur-md border-b border-gray-200 py-3 px-4 flex justify-between items-center">
        <h2 className="font-bold text-gray-900">Post Details</h2>
        <button
          onClick={() => { if (onBack) onBack(); else router.push('/feed'); }}
          className="p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-colors active:scale-95"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Desktop Back Button */}
      <div className="hidden sm:flex sticky top-[80px] z-30 py-2 -mt-2 mb-2">
        <button
          onClick={() => { if (onBack) onBack(); else router.push('/feed'); }}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900 font-medium text-sm transition-colors self-start bg-white/90 backdrop-blur-md px-4 py-2 rounded-full shadow-sm border border-gray-200"
        >
          <ArrowLeft className="w-4 h-4" />
          {onBack ? 'Close' : 'Back to Feed'}
        </button>
      </div>

      <div className="bg-white sm:rounded-xl sm:shadow-sm sm:border border-gray-100 border-y sm:border-y-0 overflow-hidden">
        <PostItem
          post={post}
          onVote={handleVote}
          onViewMap={(lat, lng) => router.push(`/map?lat=${lat}&lng=${lng}&zoom=16`)}
          isExpanded={true}
          initialMediaIndex={parseInt(searchParams.get('media') || '0')}
        />
      </div>

      <div className="bg-white sm:rounded-xl sm:shadow-sm sm:border border-gray-100 overflow-hidden p-4 sm:p-6 mt-1 sm:mt-0">
        {/* Header + Sort Toggle */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            Comments
            <span className="bg-gray-100 text-gray-600 text-xs py-0.5 px-2 rounded-full">{post.comment_count}</span>
          </h3>
          {!isolatedThreadId && (
            <div className="flex items-center bg-gray-100 rounded-full p-0.5 gap-0.5">
              <button
                onClick={() => setCommentSort('top')}
                className={`text-xs font-semibold px-3 py-1 rounded-full transition-colors ${commentSort === 'top' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Top
              </button>
              <button
                onClick={() => setCommentSort('recent')}
                className={`text-xs font-semibold px-3 py-1 rounded-full transition-colors ${commentSort === 'recent' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Recent
              </button>
            </div>
          )}
        </div>

        {/* Main comment input - Fixed to bottom on mobile */}
        <div className="fixed sm:hidden bottom-[calc(var(--bottom-nav-height))] left-0 right-0 z-40 bg-white border-t border-gray-200 p-3 mb-0 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
          <div className="max-w-[720px] mx-auto">
            {replyingTo && (
              <div className="flex items-center justify-between bg-blue-50 px-3 py-2 rounded-t-xl border border-blue-100 border-b-0 mb-0 text-xs font-medium text-blue-700">
                <span>Replying to @{replyingTo.author}...</span>
                <Button variant="ghost" size="sm" className="px-2" onClick={() => { setReplyingTo(null); setReplyText(''); }}>
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>
            )}
            <div className="flex gap-3 items-start">
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  if (replyingTo) {
                    handleReplySubmit(e, replyingTo.id);
                  } else {
                    handleCommentSubmit(e);
                  }
                }} 
                className={`flex-1 relative bg-gray-50 border border-gray-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all flex flex-row items-end p-1.5 gap-2 ${replyingTo ? 'rounded-b-xl rounded-t-none border-t-0' : 'rounded-2xl'}`}
              >
                <div className="flex-1 relative w-full">
                  <textarea
                    value={replyingTo ? replyText : commentText}
                    onChange={e => {
                      if (replyingTo) {
                        setReplyText(e.target.value);
                        handleMentionInput(e.target.value, 'reply');
                      } else {
                        setCommentText(e.target.value);
                        handleMentionInput(e.target.value, 'main');
                      }
                      // Auto-resize
                      e.target.style.height = '';
                      if (e.target.value) {
                        e.target.style.height = e.target.scrollHeight + 'px';
                      }
                    }}
                    placeholder={replyingTo ? `Write a reply...` : "Write a comment..."}
                    className="w-full h-[34px] bg-transparent py-1.5 pl-3 text-sm focus:outline-none resize-none overflow-y-auto max-h-[120px]"
                    disabled={commentMutation.isPending}
                    maxLength={MAX_CHARS}
                    rows={1}
                  />
                  {/* Mention dropdown */}
                  {(activeMentionInput === 'main' || activeMentionInput === 'reply') && mentionResults.length > 0 && (
                    <div className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-xl shadow-lg z-50 min-w-[160px]">
                      {mentionResults.map(u => (
                        <button
                          key={u}
                          type="button"
                          onClick={() => insertMention(u, activeMentionInput)}
                          className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 text-gray-800 first:rounded-t-xl last:rounded-b-xl"
                        >
                          @{u}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-2 mb-0.5 pr-1 self-end">
                  <button
                    type="submit"
                    disabled={
                      (replyingTo ? (!replyText.trim() || replyText.length > MAX_CHARS) : (!commentText.trim() || commentText.length > MAX_CHARS)) || commentMutation.isPending
                    }
                    className="w-8 h-8 shrink-0 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-full flex items-center justify-center transition-colors active:scale-95"
                  >
                    {commentMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4 -ml-0.5" />}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Main comment input - Desktop */}
        <div className="mb-8 hidden sm:block">
          <div className="flex gap-3 items-start">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shrink-0 border border-blue-200 mt-0.5">
              <span className="font-bold text-blue-700 text-sm">Me</span>
            </div>
            <form 
              onSubmit={handleCommentSubmit} 
              className="flex-1 relative bg-gray-50 border border-gray-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent rounded-2xl transition-all flex flex-row items-end p-1.5 gap-2"
            >
              <div className="flex-1 relative w-full">
                <textarea
                  value={commentText}
                  onChange={e => {
                    setCommentText(e.target.value);
                    handleMentionInput(e.target.value, 'main');
                    // Auto-resize
                    e.target.style.height = '';
                    if (e.target.value) {
                      e.target.style.height = e.target.scrollHeight + 'px';
                    }
                  }}
                  placeholder="Write a comment..."
                  className="w-full h-[34px] bg-transparent py-1.5 pl-3 text-sm focus:outline-none resize-none overflow-y-auto max-h-[200px]"
                  disabled={commentMutation.isPending}
                  maxLength={MAX_CHARS}
                  rows={1}
                />
                {/* Mention dropdown for main input */}
                {activeMentionInput === 'main' && mentionResults.length > 0 && (
                  <div className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-xl shadow-lg z-50 min-w-[160px]">
                    {mentionResults.map(u => (
                      <button
                        key={u}
                        type="button"
                        onClick={() => insertMention(u, 'main')}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 text-gray-800 first:rounded-t-xl last:rounded-b-xl"
                      >
                        @{u}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2 mb-0.5 pr-1 self-end">
                <span className={`text-[10px] ${commentText.length > MAX_CHARS * 0.93 ? 'text-red-500' : 'text-gray-400'}`}>
                  {commentText.length}/{MAX_CHARS}
                </span>
                <button
                  type="submit"
                  disabled={!commentText.trim() || commentMutation.isPending || commentText.length > MAX_CHARS}
                  className="w-8 h-8 shrink-0 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-full flex items-center justify-center transition-colors"
                >
                  {commentMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4 -ml-0.5" />}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Comments List */}
        <div className="space-y-2">
          {/* Isolated thread back button */}
          {isolatedThreadId && (
            <div className="mb-4 pb-4 border-b border-gray-100">
              <button
                onClick={() => setIsolatedThreadId(null)}
                className="text-sm font-semibold text-blue-500 hover:underline flex items-center gap-1"
              >
                <ArrowLeft className="w-4 h-4" /> View full discussion
              </button>
            </div>
          )}

          {commentsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : !commentTree || commentTree.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              No comments yet. Be the first to share your thoughts!
            </div>
          ) : isolatedThreadId && commentMap.has(isolatedThreadId) ? (
            <CommentThread key={isolatedThreadId} comment={commentMap.get(isolatedThreadId)!} />
          ) : (
            <>
              {rootsToShow!.map(comment => (
                <CommentThread key={comment.id} comment={comment} />
              ))}
              {hasMoreRoots && (
                <button
                  onClick={() => setVisibleRootCount(prev => prev + ROOT_PAGE_SIZE)}
                  className="w-full mt-4 py-2.5 text-sm font-semibold text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-xl border border-blue-100 transition-colors"
                >
                  Load {Math.min(ROOT_PAGE_SIZE, commentTree.length - visibleRootCount)} more comments
                </button>
              )}
            </>
          )}
        </div>
        </div>
      </div>
      <ConfirmDialog
        isOpen={commentToDelete !== null}
        title="Delete Comment"
        message="Are you sure you want to delete this comment?"
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={() => {
          if (commentToDelete !== null) {
            const id = commentToDelete;
            setHiddenComments(prev => new Set(prev).add(id));
            setCommentToDelete(null);

            const timeoutId = setTimeout(() => {
              deleteCommentMutation.mutate(id);
              setHiddenComments(prev => {
                const next = new Set(prev);
                next.delete(id);
                return next;
              });
              delete pendingDeleteTimeouts.current[id];
            }, 5000);
            
            pendingDeleteTimeouts.current[id] = timeoutId;

            success('Comment deleted', 'Your comment will be removed.', {
              label: 'Undo',
              onClick: () => {
                clearTimeout(timeoutId);
                delete pendingDeleteTimeouts.current[id];
                setHiddenComments(prev => {
                  const next = new Set(prev);
                  next.delete(id);
                  return next;
                });
                info('Comment restored', 'Your comment was not deleted.');
              }
            });
          }
        }}
        onCancel={() => setCommentToDelete(null)}
      />
    </PostContext.Provider>
  );
}
  // ── CommentThread sub-component ────────────────────────────────────
  const CommentThread = ({
    comment,
    isRoot = true,
    isLast = true,
    depth = 0,
  }: {
    comment: CommentNode;
    isRoot?: boolean;
    isLast?: boolean;
    depth?: number;
  }) => {
    const ctx = useContext(PostContext);
    const { user, replyingTo, setReplyingTo, replyText, setReplyText, editingCommentId, setEditingCommentId, editText, setEditText, handleReplySubmit, handleEditSubmit, commentMutation, editCommentMutation, deleteCommentMutation, commentVoteMutation, pinCommentMutation, activeMentionInput, mentionResults, setMentionResults, insertMention, handleMentionInput, setIsolatedThreadId, info, canPin, hiddenComments, setCommentToDelete, maxDepth } = ctx;
    
    if (hiddenComments.has(comment.id)) return null;

    const netScore = comment.upvotes - comment.downvotes;
    const defaultCollapsed = netScore <= AUTO_COLLAPSE_THRESHOLD;
    const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
    const [showAllReplies, setShowAllReplies] = useState(false);
    
    const editInputRef = useRef<HTMLTextAreaElement>(null);
    const replyInputRef = useRef<HTMLTextAreaElement>(null);

    const isEditing = editingCommentId === comment.id;
    const isOwn = user?.username === comment.author_name;

    useEffect(() => {
      if (isEditing && editInputRef.current) {
        editInputRef.current.focus();
        // Move cursor to end of text
        const len = editInputRef.current.value.length;
        editInputRef.current.setSelectionRange(len, len);
      }
    }, [isEditing]);

    useEffect(() => {
      if (replyingTo?.id === comment.id && replyInputRef.current) {
        replyInputRef.current.focus();
        const len = replyInputRef.current.value.length;
        replyInputRef.current.setSelectionRange(len, len);
      }
    }, [replyingTo?.id, comment.id]);

    return (
      <div className={`relative ${isRoot ? 'mb-6' : ''}`}>
        {/* Connector lines for child comments */}
        {!isRoot && (
          <>
            {/* Curved branch connecting to this child */}
            <div
              className="absolute border-gray-200"
              style={{
                left: '-21px',
                top: 0,
                height: '12px',
                width: '21px',
                borderBottomWidth: '2px',
                borderLeftWidth: '2px',
                borderBottomLeftRadius: '12px',
                zIndex: 0
              }}
            />
            {/* Straight vertical stem continuing down */}
            {!isLast && (
              <div
                className="absolute bg-gray-200"
                style={{
                  left: '-21px',
                  top: 0,
                  bottom: 0,
                  width: '2px',
                  zIndex: 0
                }}
              />
            )}
          </>
        )}

        <div className="flex gap-2">
          {/* LEFT COLUMN: avatar + thread line */}
          <div className="flex flex-col items-center shrink-0 w-6">
            {isCollapsed ? (
              <div
                className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center border border-gray-200 z-10 relative bg-white cursor-pointer hover:bg-gray-200"
                onClick={() => setIsCollapsed(false)}
              >
                <span className="font-bold text-gray-400 text-[10px]">
                  {comment.is_deleted ? '?' : (comment.author_name ? comment.author_name[0].toUpperCase() : 'U')}
                </span>
              </div>
            ) : (
              <>
                <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center border border-gray-200 z-10 relative bg-white">
                  <span className="font-bold text-gray-400 text-[10px]">
                    {comment.is_deleted ? '?' : (comment.author_name ? comment.author_name[0].toUpperCase() : 'U')}
                  </span>
                </div>
                {comment.replies.length > 0 && (
                  <div
                    className="w-[2px] bg-gray-200 flex-1 relative hover:bg-gray-400 transition-colors cursor-pointer group"
                    onClick={() => setIsCollapsed(true)}
                    title="Collapse thread"
                  >
                    <div className="absolute top-2 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border border-gray-300 rounded-sm flex items-center justify-center text-[10px] font-bold text-gray-500 group-hover:border-gray-500 group-hover:text-gray-700 shadow-sm">
                      -
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* RIGHT COLUMN: content */}
          <div className="flex-1 min-w-0 pb-1">
            {/* Header */}
            <div className="flex items-center gap-2 mb-1 flex-wrap w-full">
              <span className={`font-semibold text-sm truncate max-w-[120px] sm:max-w-xs ${comment.is_deleted ? 'text-gray-400 italic' : 'text-gray-900'}`}>
                {comment.author_name}
              </span>
              <span className="text-gray-400 text-[10px]">
                {formatCommentTime(comment.created_at)}
              </span>
              {comment.edited_at && !comment.is_deleted && (
                <span className="text-gray-400 text-[10px] italic">(edited)</span>
              )}
              {isCollapsed && comment.replies.length > 0 && (
                <span className="text-gray-400 text-[10px] ml-1 italic">
                  ({comment.replies.length} child{comment.replies.length !== 1 ? 'ren' : ''})
                </span>
              )}
              {isCollapsed && netScore <= AUTO_COLLAPSE_THRESHOLD && (
                <span className="text-gray-400 text-[10px] italic">· low score hidden</span>
              )}
              {comment.is_pinned && (
                <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5 ml-auto">
                  <Pin className="w-2.5 h-2.5" />
                  Pinned by @{comment.pinned_by}
                </span>
              )}
            </div>

            {!isCollapsed && (
              <>
                {/* Content */}
                {comment.is_deleted ? (
                  <p className="text-gray-400 text-sm italic">[deleted]</p>
                ) : isEditing ? (
                  <div className="mt-1 mb-2">
                    <textarea
                      ref={editInputRef}
                      value={editText}
                      onChange={e => setEditText(e.target.value)}
                      className="w-full bg-gray-50 border border-blue-200 rounded-xl py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                      rows={3}
                      maxLength={MAX_CHARS}
                    />
                    <div className="flex items-center justify-between mt-1">
                      <span className={`text-[10px] ${editText.length > 950 ? 'text-red-500' : 'text-gray-400'}`}>
                        {editText.length} / {MAX_CHARS}
                      </span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => { setEditingCommentId(null); setEditText(''); }}
                          className="text-xs text-gray-500 hover:text-gray-700 font-medium"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => editCommentMutation.mutate({ commentId: comment.id, content: editText })}
                          disabled={!editText.trim() || editCommentMutation.isPending}
                          className="text-xs font-semibold text-blue-600 hover:text-blue-800 disabled:opacity-40"
                        >
                          {editCommentMutation.isPending ? 'Saving...' : 'Save'}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Quote display if reply has quoted content */}
                    {comment.content.startsWith('> ') && (() => {
                      const lines = comment.content.split('\n');
                      const quoteLines = lines.filter(l => l.startsWith('> '));
                      const bodyLines = lines.filter(l => !l.startsWith('> '));
                      return (
                        <>
                          {quoteLines.length > 0 && (
                            <div className="border-l-2 border-gray-300 pl-2 mb-1">
                              <p className="text-gray-400 text-xs italic truncate">
                                {quoteLines.map(l => l.replace(/^> /, '')).join(' ')}
                              </p>
                            </div>
                          )}
                          <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap break-words">
                            {bodyLines.join('\n')}
                          </p>
                        </>
                      );
                    })()}
                    {!comment.content.startsWith('> ') && (
                      <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap break-words">
                        {comment.content}
                      </p>
                    )}
                  </>
                )}

                {/* Actions */}
                {!comment.is_deleted && !isEditing && (
                  <div className="flex items-center justify-between mt-2 mb-2">
                    <div className="flex items-center gap-4">
                      {/* Vote */}
                      <div className="flex items-center gap-1 bg-gray-50 rounded-full px-2 py-1 border border-gray-100">
                        <button
                          onClick={() => commentVoteMutation.mutate({ commentId: comment.id, type: 'upvote' })}
                          className={`text-gray-500 hover:text-orange-500 transition-colors p-1 ${comment.user_interaction === 'upvote' ? 'text-orange-500' : ''}`}
                        >
                          <ArrowUp className="w-3.5 h-3.5" />
                        </button>
                        <span className="text-xs font-semibold text-gray-700 min-w-[12px] text-center">
                          {netScore}
                        </span>
                        <button
                          onClick={() => commentVoteMutation.mutate({ commentId: comment.id, type: 'downvote' })}
                          className={`text-gray-500 hover:text-blue-500 transition-colors p-1 ${comment.user_interaction === 'downvote' ? 'text-blue-500' : ''}`}
                        >
                          <ArrowDown className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {/* Reply */}
                      <button
                        onClick={() => {
                          setReplyText('');
                          setReplyingTo({ id: comment.id, author: comment.author_name, content: comment.content });
                        }}
                        className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-800 transition-colors"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        Reply
                      </button>

                      {/* Report */}
                      {!isOwn && (
                        <button
                          onClick={() => info('Coming Soon', 'Comment reporting is currently under development.')}
                          className="flex items-center gap-1 text-xs font-medium text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <Flag className="w-3 h-3" />
                          Report
                        </button>
                      )}
                    </div>

                    {/* Right-side: Pin, Edit, Delete */}
                    <div className="flex items-center gap-3">
                      {canPin && (
                        <button
                          onClick={() => pinCommentMutation.mutate(comment.id)}
                          disabled={pinCommentMutation.isPending}
                          className={`text-xs font-medium transition-colors ${comment.is_pinned ? 'text-amber-500 hover:text-amber-700' : 'text-gray-400 hover:text-amber-500'}`}
                        >
                          {comment.is_pinned ? 'Unpin' : 'Pin'}
                        </button>
                      )}
                      {isOwn && (
                        <>
                          <button
                            onClick={() => { setEditingCommentId(comment.id); setEditText(comment.content); }}
                            className="text-xs font-medium text-gray-400 hover:text-blue-500 transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setCommentToDelete(comment.id)}
                            className="text-xs font-medium text-gray-400 hover:text-red-500 transition-colors"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Desktop Inline Reply Form */}
                {replyingTo?.id === comment.id && (
                  <div className="hidden sm:block mt-3 pr-4">
                    {/* Quote preview */}
                    {replyText.startsWith('> ') && (
                      <div className="border-l-2 border-gray-300 pl-2 mb-2">
                        <p className="text-gray-400 text-xs italic truncate">
                          {replyText.split('\n')[0].replace('> ', '')}
                        </p>
                      </div>
                    )}
                    <form
                      onSubmit={e => handleReplySubmit(e, comment.id)}
                      className="flex gap-2 items-end bg-blue-50/50 p-2 rounded-xl border border-blue-100"
                    >
                      <div className="flex-1 relative w-full">
                        <textarea
                          ref={replyInputRef}
                          value={replyText.startsWith('> ') ? replyText.split('\n').slice(2).join('\n') : replyText}
                          onChange={e => {
                            const quoted = replyText.startsWith('> ') ? replyText.split('\n').slice(0, 2).join('\n') + '\n' : '';
                            const newVal = quoted + e.target.value;
                            setReplyText(newVal);
                            handleMentionInput(e.target.value, 'reply');
                            // Auto-resize
                            e.target.style.height = 'auto';
                            e.target.style.height = e.target.scrollHeight + 'px';
                          }}
                          onKeyDown={e => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              if (replyText.trim() && !commentMutation.isPending) {
                                handleReplySubmit(e as any, comment.id);
                              }
                            }
                          }}
                          placeholder={`Replying to ${comment.author_name}... (Shift+Enter for new line)`}
                          className="w-full bg-white border border-blue-200 rounded-xl py-1.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all resize-none overflow-hidden min-h-[36px] max-h-[200px]"
                          disabled={commentMutation.isPending}
                          maxLength={MAX_CHARS}
                          rows={1}
                          autoFocus
                        />
                        {/* Mention dropdown */}
                        {activeMentionInput === 'reply' && mentionResults.length > 0 && (
                          <div className="absolute bottom-full mb-1 left-0 bg-white border border-gray-200 rounded-xl shadow-lg z-50 min-w-[160px]">
                            {mentionResults.map((u: string) => (
                              <button
                                key={u}
                                type="button"
                                onClick={() => insertMention(u, 'reply')}
                                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 text-gray-800 first:rounded-t-xl last:rounded-b-xl"
                              >
                                @{u}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mb-0.5 shrink-0 self-end">
                        <span className={`text-[10px] ${replyText.length > 950 ? 'text-red-500' : 'text-gray-400'}`}>
                          {replyText.replace(/^(> .*\n\n?)/, '').length}/{MAX_CHARS}
                        </span>
                        <button
                          type="submit"
                          disabled={!replyText.trim() || commentMutation.isPending}
                          className="w-8 h-8 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white rounded-full flex items-center justify-center transition-colors shadow-sm"
                        >
                          {commentMutation.isPending
                            ? <Loader2 className="w-3 h-3 animate-spin" />
                            : <Send className="w-3 h-3 -ml-0.5" />}
                        </button>
                        <button
                          type="button"
                          onClick={() => { setReplyingTo(null); setReplyText(''); setMentionResults([]); }}
                          className="w-8 h-8 bg-gray-100 hover:bg-gray-200 text-gray-500 rounded-full flex items-center justify-center transition-colors"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </form>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Nested replies */}
        {!isCollapsed && comment.replies.length > 0 && (
          <div className="pl-8 flex flex-col">
            {depth >= maxDepth ? (
              <div className="relative pt-2 pb-2 flex items-center">
                <div
                  className="absolute border-gray-200"
                  style={{ left: '-21px', top: 0, height: '12px', width: '21px', borderBottomWidth: '2px', borderLeftWidth: '2px', borderBottomLeftRadius: '12px' }}
                />
                <button
                  onClick={() => setIsolatedThreadId(comment.id)}
                  className="text-left text-xs font-semibold text-blue-500 hover:underline flex items-center gap-1"
                >
                  Continue this thread <ArrowLeft className="w-3 h-3 rotate-180" />
                </button>
              </div>
            ) : (
              <>
                {comment.replies.slice(0, showAllReplies ? undefined : MAX_REPLIES).map((reply, idx, arr) => {
                  const hasHiddenReplies = !showAllReplies && comment.replies.length > MAX_REPLIES;
                  const isLastChild = idx === arr.length - 1 && !hasHiddenReplies;
                  return (
                    <CommentThread
                      key={reply.id}
                      comment={reply}
                      isRoot={false}
                      isLast={isLastChild}
                      depth={depth + 1}
                    />
                  );
                })}
                {!showAllReplies && comment.replies.length > MAX_REPLIES && (
                  <div className="relative pt-2 pb-2 flex items-center">
                    <div
                      className="absolute border-gray-200"
                      style={{ left: '-21px', top: 0, height: '12px', width: '21px', borderBottomWidth: '2px', borderLeftWidth: '2px', borderBottomLeftRadius: '12px' }}
                    />
                    <button
                      onClick={() => setShowAllReplies(true)}
                      className="text-left text-xs font-semibold text-blue-500 hover:underline"
                    >
                      Load more replies ({comment.replies.length - MAX_REPLIES} more)
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    );
  };

