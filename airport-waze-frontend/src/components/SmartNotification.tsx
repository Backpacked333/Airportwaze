/**
 * iOS-Style Smart Notification Banner
 *
 * Features:
 * - Slides in from top (like iOS notifications)
 * - Auto-dismiss after timeout
 * - Swipe up to dismiss
 * - Tap to expand/view details
 * - Priority-based styling
 * - Haptic feedback simulation
 */

import { useEffect, useState } from 'react';
import { PredictiveAlert } from '../services/intelligenceEngine';
import '../styles/ios-design-tokens.css';

interface SmartNotificationProps {
  alert: PredictiveAlert;
  onDismiss: () => void;
  autoDismissMs?: number;
}

export function SmartNotification({
  alert,
  onDismiss,
  autoDismissMs = 5000
}: SmartNotificationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const startY = useState(0)[0];

  useEffect(() => {
    // Slide in animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto-dismiss
    if (autoDismissMs > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoDismissMs);

      return () => clearTimeout(timer);
    }
  }, [autoDismissMs]);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(onDismiss, 300); // Wait for slide-out animation
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    (startY as any) = touch.clientY;
    setIsDragging(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;

    const touch = e.touches[0];
    const deltaY = touch.clientY - (startY as any);

    // Only allow upward swipe
    if (deltaY < 0) {
      setDragY(deltaY);
    }
  };

  const handleTouchEnd = () => {
    setIsDragging(false);

    // Dismiss if swiped up enough
    if (dragY < -50) {
      handleDismiss();
    } else {
      setDragY(0);
    }
  };

  const priorityColors = {
    low: { bg: 'var(--ios-blue)', icon: '💡' },
    medium: { bg: 'var(--ios-orange)', icon: '📍' },
    high: { bg: 'var(--ios-red)', icon: '⚠️' },
    urgent: { bg: 'var(--ios-red)', icon: '🚨' }
  };

  const { bg, icon } = priorityColors[alert.priority];

  const transform = isDragging
    ? `translateY(${dragY}px)`
    : isVisible
    ? 'translateY(0)'
    : 'translateY(-120%)';

  return (
    <div
      className="fixed top-0 left-0 right-0 z-50 px-4"
      style={{
        paddingTop: 'max(env(safe-area-inset-top), 12px)',
        transform,
        transition: isDragging ? 'none' : 'transform var(--ios-transition-spring)',
        pointerEvents: isVisible ? 'auto' : 'none'
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div
        className="ios-frosted rounded-2xl overflow-hidden shadow-xl"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)'
        }}
      >
        {/* Priority Bar */}
        <div
          style={{
            height: '4px',
            backgroundColor: bg,
            width: '100%'
          }}
        />

        {/* Content */}
        <div className="p-4">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div
              className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-xl"
              style={{
                backgroundColor: 'var(--ios-fill)'
              }}
            >
              {icon}
            </div>

            {/* Text */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <h3
                    className="ios-headline font-semibold"
                    style={{ color: 'var(--ios-label)' }}
                  >
                    {alert.title}
                  </h3>
                  <p
                    className="ios-callout mt-1"
                    style={{
                      color: 'var(--ios-label-secondary)',
                      display: '-webkit-box',
                      WebkitLineClamp: isExpanded ? 'unset' : 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}
                  >
                    {alert.message}
                  </p>
                </div>

                {/* Close Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDismiss();
                  }}
                  className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center"
                  style={{
                    backgroundColor: 'var(--ios-fill-secondary)',
                    color: 'var(--ios-label-tertiary)'
                  }}
                >
                  <svg
                    className="w-4 h-4"
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

              {/* Timestamp */}
              <p
                className="ios-footnote mt-2"
                style={{ color: 'var(--ios-label-tertiary)' }}
              >
                {formatTimeAgo(alert.timestamp)}
              </p>

              {/* Action Button (if URL provided) */}
              {alert.actionUrl && isExpanded && (
                <a
                  href={alert.actionUrl}
                  className="inline-block mt-3 px-4 py-2 rounded-lg ios-button text-sm"
                  onClick={(e) => e.stopPropagation()}
                >
                  View Details
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Format timestamp as "X min ago"
 */
function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
