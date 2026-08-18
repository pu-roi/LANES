"use client";

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

export interface MediaViewerProps {
  mediaUrls: string[];
  initialIndex?: number;
  isOpen: boolean;
  onClose: () => void;
}

export function MediaViewer({ mediaUrls, initialIndex = 0, isOpen, onClose }: MediaViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [zoomScale, setZoomScale] = useState(1);

  const handleClose = () => {
    setZoomScale(1);
    onClose();
  };

  useEffect(() => {
    if (isOpen) {
      setCurrentIndex(initialIndex);
    }
  }, [isOpen, initialIndex]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);
  
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

    const count = mediaUrls.length;
    if (count > 1) {
      if (isLeftSwipe) { setCurrentIndex(prev => (prev < count - 1 ? prev + 1 : 0)); setZoomScale(1); }
      if (isRightSwipe) { setCurrentIndex(prev => (prev > 0 ? prev - 1 : count - 1)); setZoomScale(1); }
    }
  };

  if (!isOpen || mediaUrls.length === 0 || typeof document === 'undefined') return null;

  return createPortal(
    <div className="fixed inset-0 z-[99999] bg-black flex flex-col">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center z-50 bg-gradient-to-b from-black/60 to-transparent">
        <span className="text-white font-medium text-sm">
          {currentIndex + 1} of {mediaUrls.length}
        </span>
        <button 
          onClick={handleClose}
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
          const url = mediaUrls[currentIndex];
          if (!url) return null;
          const isVideo = url.match(/\.(mp4|webm|mov|ogg)$/i) || url.includes('/video/upload/');
          return isVideo ? (
            <video src={url} controls autoPlay className="w-full max-h-full object-contain" />
          ) : (
            <TransformWrapper
              initialScale={1}
              minScale={1}
              maxScale={4}
              centerOnInit
              onTransform={(ref) => setZoomScale(ref.state.scale)}
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

      {/* Navigation Controls */}
      {mediaUrls.length > 1 && (
        <>
          <button 
            onClick={(e) => { e.stopPropagation(); setCurrentIndex(prev => (prev > 0 ? prev - 1 : mediaUrls.length - 1)); setZoomScale(1); }}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-white p-3 hover:bg-white/20 rounded-full transition-colors"
          >
            <ChevronLeft className="w-8 h-8" />
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); setCurrentIndex(prev => (prev < mediaUrls.length - 1 ? prev + 1 : 0)); setZoomScale(1); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-white p-3 hover:bg-white/20 rounded-full transition-colors"
          >
            <ChevronRight className="w-8 h-8" />
          </button>
        </>
      )}
    </div>,
    document.body
  );
}
