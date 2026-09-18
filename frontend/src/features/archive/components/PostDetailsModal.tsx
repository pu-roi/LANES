"use client";

import React from "react";
import { format } from "date-fns";
import { 
  User, 
  MapPin, 
  Calendar, 
  Trash2, 
  RotateCcw, 
  EyeOff, 
  FileText,
  Clock,
  Loader2,
  ShieldAlert
} from "lucide-react";
import { ArchivedPost } from "@/features/admin/adminApi";
import { Button, Modal } from "@/shared/ui";

interface PostDetailsModalProps {
  post: ArchivedPost | null;
  isOpen: boolean;
  onClose: () => void;
  onRestore?: (post: ArchivedPost) => void;
  onHardDelete?: (post: ArchivedPost) => void;
  isRestoring?: boolean;
}

export function PostDetailsModal({
  post,
  isOpen,
  onClose,
  onRestore,
  onHardDelete,
  isRestoring = false,
}: PostDetailsModalProps) {
  if (!isOpen || !post) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Archived Post #${post.id}`}>
      <div className="space-y-5 text-gray-800 max-h-[75vh] overflow-y-auto pr-1">
        {/* Header Summary */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 bg-slate-50 border border-slate-200 rounded-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold border border-blue-200 shrink-0">
              {post.author_avatar ? (
                <img src={post.author_avatar} alt="Author" className="w-full h-full rounded-full object-cover" />
              ) : (
                <span>{post.author_name ? post.author_name[0].toUpperCase() : "U"}</span>
              )}
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">{post.author_name}</h3>
              <p className="text-xs text-gray-500">
                Created: {format(new Date(post.created_at), "MMM d, yyyy • h:mm a")}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {post.deleted_at && (
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
                Deleted
              </span>
            )}
            {post.hidden_at && (
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
                Hidden
              </span>
            )}
          </div>
        </div>

        {/* Removal Audit Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {post.deleted_at && (
            <div className="p-3 bg-red-50/50 border border-red-200/70 rounded-xl flex items-start gap-2.5">
              <Trash2 className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-900">Deleted On</p>
                <p className="text-red-700">{format(new Date(post.deleted_at), "MMM d, yyyy • h:mm a")}</p>
                {post.deleted_by_name && (
                  <p className="text-red-600 mt-0.5">By: {post.deleted_by_name}</p>
                )}
              </div>
            </div>
          )}
          {post.hidden_at && (
            <div className="p-3 bg-amber-50/50 border border-amber-200/70 rounded-xl flex items-start gap-2.5">
              <EyeOff className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-900">Hidden On</p>
                <p className="text-amber-700">{format(new Date(post.hidden_at), "MMM d, yyyy • h:mm a")}</p>
                {post.hidden_by_name && (
                  <p className="text-amber-600 mt-0.5">By: {post.hidden_by_name}</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Post Content */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Post Content</label>
          <div className="p-4 bg-white border border-gray-200 rounded-xl text-sm leading-relaxed whitespace-pre-wrap break-words text-gray-900 shadow-sm">
            {post.content}
          </div>
        </div>

        {/* Location Tag */}
        {post.location_tag && (
          <div className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg border border-gray-200">
            <MapPin className="w-4 h-4 text-blue-600 shrink-0" />
            <span className="font-medium">{post.location_tag}</span>
            {post.location_lat && post.location_lng && (
              <span className="text-gray-400">({post.location_lat.toFixed(4)}, {post.location_lng.toFixed(4)})</span>
            )}
          </div>
        )}

        {/* Media Attachments */}
        {post.media_urls && post.media_urls.length > 0 && (
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              Attached Media ({post.media_urls.length})
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {post.media_urls.map((url, idx) => {
                const isVideo = url.match(/\.(mp4|webm|mov|ogg)$/i) || url.includes("/video/upload/");
                return (
                  <div key={idx} className="relative aspect-video rounded-lg overflow-hidden border border-gray-200 bg-black/5 flex items-center justify-center">
                    {isVideo ? (
                      <video src={url} controls className="w-full h-full object-cover" />
                    ) : (
                      <img src={url} alt={`Media ${idx + 1}`} className="w-full h-full object-cover hover:scale-105 transition-transform duration-200" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex flex-col-reverse sm:flex-row items-center justify-end gap-2 pt-4 border-t border-gray-200">
          <Button variant="ghost" onClick={onClose} className="w-full sm:w-auto">
            Close
          </Button>

          {onRestore && (
            <Button
              variant="outline"
              onClick={() => onRestore(post)}
              disabled={isRestoring}
              className="w-full sm:w-auto border-emerald-300 text-emerald-700 hover:bg-emerald-50 focus:ring-emerald-500"
            >
              {isRestoring ? (
                <div className="flex items-center gap-1.5">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Restoring...</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <RotateCcw className="w-4 h-4" />
                  <span>Restore to Feed</span>
                </div>
              )}
            </Button>
          )}

          {onHardDelete && (
            <Button
              variant="danger"
              onClick={() => onHardDelete(post)}
              className="w-full sm:w-auto flex items-center gap-1.5"
            >
              <Trash2 className="w-4 h-4" />
              <span>Permanently Delete</span>
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
