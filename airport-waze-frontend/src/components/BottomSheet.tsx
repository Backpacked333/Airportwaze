/**
 * iOS-Style Bottom Sheet Component
 *
 * Features:
 * - Swipe to dismiss
 * - Snap points (half, full)
 * - Backdrop blur
 * - Spring animations
 * - Native-feeling gestures
 */

import { useEffect, useRef, useState, ReactNode } from 'react';
import '../styles/ios-design-tokens.css';

interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  snapPoints?: ('quarter' | 'half' | 'full')[];
  initialSnap?: 'quarter' | 'half' | 'full';
}

export function BottomSheet({
  isOpen,
  onClose,
  children,
  title,
  snapPoints = ['half', 'full'],
  initialSnap = 'half'
}: BottomSheetProps) {
  const [currentSnap, setCurrentSnap] = useState(initialSnap);
  const [isDragging, setIsDragging] = useState(false);
  const [dragY, setDragY] = useState(0);
  const sheetRef = useRef<HTMLDivElement>(null);
  const startY = useRef(0);
  const currentY = useRef(0);

  const snapHeights = {
    quarter: '25%',
    half: '50%',
    full: '90%'
  };

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

  const handleTouchStart = (e: React.TouchEvent) => {
    startY.current = e.touches[0].clientY;
    setIsDragging(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;

    currentY.current = e.touches[0].clientY;
    const deltaY = currentY.current - startY.current;

    // Only allow dragging down
    if (deltaY > 0) {
      setDragY(deltaY);
    }
  };

  const handleTouchEnd = () => {
    setIsDragging(false);

    // Threshold for closing (200px drag)
    if (dragY > 200) {
      onClose();
    } else if (dragY > 100 && snapPoints.includes('half') && currentSnap === 'full') {
      // Snap to half
      setCurrentSnap('half');
    } else {
      // Snap back
      setDragY(0);
    }

    setDragY(0);
  };

  if (!isOpen) return null;

  const transform = isDragging ? `translateY(${dragY}px)` : 'translateY(0)';

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 transition-opacity duration-300"
        style={{
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          opacity: isOpen ? 1 : 0
        }}
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div
        ref={sheetRef}
        className="fixed bottom-0 left-0 right-0 z-50 ios-frosted"
        style={{
          height: snapHeights[currentSnap],
          borderTopLeftRadius: 'var(--ios-radius-2xl)',
          borderTopRightRadius: 'var(--ios-radius-2xl)',
          transform,
          transition: isDragging ? 'none' : 'transform var(--ios-transition-spring)',
          boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.1)',
          paddingBottom: 'max(env(safe-area-inset-bottom), 20px)'
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div
            style={{
              width: '40px',
              height: '5px',
              backgroundColor: 'var(--ios-gray3)',
              borderRadius: 'var(--ios-radius-full)'
            }}
          />
        </div>

        {/* Header */}
        {title && (
          <div
            className="px-6 pb-4 flex items-center justify-between"
            style={{
              borderBottom: '1px solid var(--ios-separator)'
            }}
          >
            <h2 className="ios-title" style={{ color: 'var(--ios-label)' }}>
              {title}
            </h2>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-full"
              style={{
                backgroundColor: 'var(--ios-fill)',
                color: 'var(--ios-label-secondary)'
              }}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Content */}
        <div
          className="overflow-y-auto px-6 pt-4"
          style={{
            height: 'calc(100% - 60px)',
            WebkitOverflowScrolling: 'touch'
          }}
        >
          {children}
        </div>
      </div>
    </>
  );
}
