import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';
import { Skeleton } from './ui/skeleton';

/**
 * Loading Spinner Component
 *
 * Usage:
 * ```tsx
 * <LoadingSpinner size="md" />
 * <LoadingSpinner size="lg" className="text-primary" />
 * ```
 */
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

export function LoadingSpinner({ size = 'md', className, text }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <Loader2 className={cn('animate-spin', sizeClasses[size], className)} />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
    </div>
  );
}

/**
 * Loading Overlay Component
 *
 * Displays a full-screen loading overlay
 *
 * Usage:
 * ```tsx
 * <LoadingOverlay visible={isLoading} text="Loading data..." />
 * ```
 */
interface LoadingOverlayProps {
  visible: boolean;
  text?: string;
  blur?: boolean;
  className?: string;
}

export function LoadingOverlay({
  visible,
  text = 'Loading...',
  blur = true,
  className,
}: LoadingOverlayProps) {
  if (!visible) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-background/80',
        blur && 'backdrop-blur-sm',
        className
      )}
    >
      <div className="flex flex-col items-center gap-4 rounded-lg bg-card p-8 shadow-lg">
        <LoadingSpinner size="lg" />
        <p className="text-sm font-medium">{text}</p>
      </div>
    </div>
  );
}

/**
 * Card Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <CardSkeleton />
 * <CardSkeleton count={3} />
 * ```
 */
interface CardSkeletonProps {
  count?: number;
  className?: string;
}

export function CardSkeleton({ count = 1, className }: CardSkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className={cn('space-y-3', className)}>
          <Skeleton className="h-[200px] w-full rounded-lg" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
          </div>
        </div>
      ))}
    </>
  );
}

/**
 * List Item Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <ListItemSkeleton />
 * <ListItemSkeleton count={5} />
 * ```
 */
interface ListItemSkeletonProps {
  count?: number;
  showAvatar?: boolean;
  className?: string;
}

export function ListItemSkeleton({
  count = 1,
  showAvatar = true,
  className,
}: ListItemSkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className={cn('flex items-center space-x-4', className)}>
          {showAvatar && <Skeleton className="h-12 w-12 rounded-full" />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        </div>
      ))}
    </>
  );
}

/**
 * Table Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <TableSkeleton rows={5} columns={4} />
 * ```
 */
interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  className?: string;
}

export function TableSkeleton({
  rows = 5,
  columns = 4,
  showHeader = true,
  className,
}: TableSkeletonProps) {
  return (
    <div className={cn('space-y-3', className)}>
      {showHeader && (
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={index} className="h-8 flex-1" />
          ))}
        </div>
      )}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-12 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Text Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <TextSkeleton lines={3} />
 * ```
 */
interface TextSkeletonProps {
  lines?: number;
  className?: string;
}

export function TextSkeleton({ lines = 3, className }: TextSkeletonProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className="h-4"
          style={{
            width: index === lines - 1 ? '70%' : '100%',
          }}
        />
      ))}
    </div>
  );
}

/**
 * Avatar Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <AvatarSkeleton size="md" />
 * ```
 */
interface AvatarSkeletonProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AvatarSkeleton({ size = 'md', className }: AvatarSkeletonProps) {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return <Skeleton className={cn('rounded-full', sizeClasses[size], className)} />;
}

/**
 * Form Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <FormSkeleton fields={4} />
 * ```
 */
interface FormSkeletonProps {
  fields?: number;
  showButton?: boolean;
  className?: string;
}

export function FormSkeleton({ fields = 4, showButton = true, className }: FormSkeletonProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
      {showButton && <Skeleton className="h-10 w-full" />}
    </div>
  );
}

/**
 * Chart Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <ChartSkeleton />
 * ```
 */
interface ChartSkeletonProps {
  className?: string;
}

export function ChartSkeleton({ className }: ChartSkeletonProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <Skeleton className="h-[300px] w-full" />
      <div className="flex justify-center gap-4">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
}

/**
 * Page Skeleton Loader
 *
 * Full page loading skeleton with header and content sections
 *
 * Usage:
 * ```tsx
 * <PageSkeleton />
 * ```
 */
interface PageSkeletonProps {
  className?: string;
}

export function PageSkeleton({ className }: PageSkeletonProps) {
  return (
    <div className={cn('space-y-6 p-6', className)}>
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <CardSkeleton count={6} />
      </div>
    </div>
  );
}

/**
 * Map Skeleton Loader
 *
 * Usage:
 * ```tsx
 * <MapSkeleton />
 * ```
 */
interface MapSkeletonProps {
  className?: string;
}

export function MapSkeleton({ className }: MapSkeletonProps) {
  return (
    <div className={cn('relative', className)}>
      <Skeleton className="h-[600px] w-full rounded-lg" />
      <div className="absolute inset-0 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading map..." />
      </div>
    </div>
  );
}

/**
 * Inline Loading Component
 *
 * Small loading indicator for inline use
 *
 * Usage:
 * ```tsx
 * <InlineLoading />
 * <InlineLoading text="Saving..." />
 * ```
 */
interface InlineLoadingProps {
  text?: string;
  className?: string;
}

export function InlineLoading({ text, className }: InlineLoadingProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Loader2 className="h-4 w-4 animate-spin" />
      {text && <span className="text-sm text-muted-foreground">{text}</span>}
    </div>
  );
}

/**
 * Button Loading State
 *
 * Replaces button content with loading spinner
 *
 * Usage:
 * ```tsx
 * <Button disabled={isLoading}>
 *   {isLoading ? <ButtonLoading /> : 'Submit'}
 * </Button>
 * ```
 */
interface ButtonLoadingProps {
  text?: string;
  className?: string;
}

export function ButtonLoading({ text = 'Loading...', className }: ButtonLoadingProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{text}</span>
    </div>
  );
}

// Re-export all components as named exports
export {
  LoadingSpinner as Spinner,
  LoadingOverlay as Overlay,
  CardSkeleton,
  ListItemSkeleton,
  TableSkeleton,
  TextSkeleton,
  AvatarSkeleton,
  FormSkeleton,
  ChartSkeleton,
  PageSkeleton,
  MapSkeleton,
  InlineLoading,
  ButtonLoading,
};

// Default export for convenience
export default {
  Spinner: LoadingSpinner,
  Overlay: LoadingOverlay,
  Card: CardSkeleton,
  ListItem: ListItemSkeleton,
  Table: TableSkeleton,
  Text: TextSkeleton,
  Avatar: AvatarSkeleton,
  Form: FormSkeleton,
  Chart: ChartSkeleton,
  Page: PageSkeleton,
  Map: MapSkeleton,
  Inline: InlineLoading,
  Button: ButtonLoading,
};
