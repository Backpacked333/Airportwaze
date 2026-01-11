/**
 * AR Navigation Component for AirportWaze
 * Provides WebXR-based augmented reality navigation with 3D directional indicators
 * Falls back to 2D navigation when AR is not supported
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Camera, Navigation, MapPin, AlertCircle, Compass } from 'lucide-react';

// Types
interface Checkpoint {
  id: string;
  name: string;
  type: string;
  position: {
    latitude: number;
    longitude: number;
    altitude?: number;
  };
  floor?: number;
}

interface NavigationStep {
  instruction: string;
  distance: number;
  direction: 'forward' | 'left' | 'right' | 'backward';
  checkpoint?: Checkpoint;
}

interface ARMarker {
  id: string;
  position: { x: number; y: number; z: number };
  label: string;
  type: 'arrow' | 'checkpoint' | 'destination';
}

interface ARNavigationProps {
  destination: Checkpoint;
  currentPosition: GeolocationPosition | null;
  navigationSteps: NavigationStep[];
  onNavigationComplete?: () => void;
  onError?: (error: string) => void;
}

// Utility functions
const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const R = 6371e3; // Earth's radius in meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;

  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) *
    Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c; // Distance in meters
};

const calculateBearing = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;

  const y = Math.sin(Δλ) * Math.cos(φ2);
  const x = Math.cos(φ1) * Math.sin(φ2) -
    Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
  const θ = Math.atan2(y, x);

  return (θ * 180 / Math.PI + 360) % 360; // Bearing in degrees
};

const formatDistance = (meters: number): string => {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
};

const ARNavigation: React.FC<ARNavigationProps> = ({
  destination,
  currentPosition,
  navigationSteps,
  onNavigationComplete,
  onError
}) => {
  // State
  const [isARSupported, setIsARSupported] = useState<boolean>(false);
  const [isARActive, setIsARActive] = useState<boolean>(false);
  const [deviceOrientation, setDeviceOrientation] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<NavigationStep | null>(null);
  const [distanceToDestination, setDistanceToDestination] = useState<number>(0);
  const [bearingToDestination, setBearingToDestination] = useState<number>(0);
  const [arMarkers, setArMarkers] = useState<ARMarker[]>([]);
  const [cameraPermission, setCameraPermission] = useState<'granted' | 'denied' | 'prompt'>('prompt');

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const xrSessionRef = useRef<any>(null);
  const animationFrameRef = useRef<number>();

  // Check AR support
  useEffect(() => {
    const checkARSupport = async () => {
      if ('xr' in navigator) {
        try {
          const supported = await (navigator as any).xr.isSessionSupported('immersive-ar');
          setIsARSupported(supported);
        } catch (error) {
          console.log('AR not supported:', error);
          setIsARSupported(false);
        }
      } else {
        setIsARSupported(false);
      }
    };

    checkARSupport();
  }, []);

  // Update navigation data
  useEffect(() => {
    if (!currentPosition || !destination) return;

    const distance = calculateDistance(
      currentPosition.coords.latitude,
      currentPosition.coords.longitude,
      destination.position.latitude,
      destination.position.longitude
    );

    const bearing = calculateBearing(
      currentPosition.coords.latitude,
      currentPosition.coords.longitude,
      destination.position.latitude,
      destination.position.longitude
    );

    setDistanceToDestination(distance);
    setBearingToDestination(bearing);

    // Update current step
    if (navigationSteps.length > 0) {
      setCurrentStep(navigationSteps[0]);
    }

    // Check if destination reached
    if (distance < 5 && onNavigationComplete) {
      onNavigationComplete();
    }
  }, [currentPosition, destination, navigationSteps, onNavigationComplete]);

  // Handle device orientation
  useEffect(() => {
    const handleOrientation = (event: DeviceOrientationEvent) => {
      if (event.alpha !== null) {
        setDeviceOrientation(event.alpha);
      }
    };

    window.addEventListener('deviceorientation', handleOrientation);
    return () => window.removeEventListener('deviceorientation', handleOrientation);
  }, []);

  // Start AR session
  const startARSession = useCallback(async () => {
    try {
      // Request camera permission
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraPermission('granted');
      }

      // Try to start WebXR session if supported
      if (isARSupported && 'xr' in navigator) {
        try {
          const xrSession = await (navigator as any).xr.requestSession('immersive-ar', {
            requiredFeatures: ['local', 'hit-test'],
            optionalFeatures: ['dom-overlay'],
            domOverlay: { root: document.body }
          });

          xrSessionRef.current = xrSession;
          setIsARActive(true);

          // Start AR render loop
          const onXRFrame = (time: number, frame: any) => {
            xrSession.requestAnimationFrame(onXRFrame);
            renderARFrame(frame);
          };

          xrSession.requestAnimationFrame(onXRFrame);
        } catch (xrError) {
          console.log('WebXR not available, using fallback AR:', xrError);
          // Use video-based AR fallback
          setIsARActive(true);
          startVideoARRendering();
        }
      } else {
        // Use video-based AR fallback
        setIsARActive(true);
        startVideoARRendering();
      }
    } catch (error) {
      console.error('Failed to start AR:', error);
      setCameraPermission('denied');
      if (onError) {
        onError('Camera access denied. Please enable camera permissions.');
      }
    }
  }, [isARSupported, onError]);

  // Stop AR session
  const stopARSession = useCallback(() => {
    if (xrSessionRef.current) {
      xrSessionRef.current.end();
      xrSessionRef.current = null;
    }

    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    setIsARActive(false);
  }, []);

  // Video-based AR rendering
  const startVideoARRendering = useCallback(() => {
    const renderFrame = () => {
      if (!videoRef.current || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Draw video frame
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      // Draw AR overlays
      drawAROverlays(ctx, canvas.width, canvas.height);

      animationFrameRef.current = requestAnimationFrame(renderFrame);
    };

    renderFrame();
  }, []);

  // Render AR frame (WebXR)
  const renderARFrame = (frame: any) => {
    // WebXR rendering logic would go here
    // This is a simplified version
    console.log('Rendering AR frame:', frame);
  };

  // Draw AR overlays on canvas
  const drawAROverlays = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    if (!currentStep) return;

    // Calculate arrow position based on bearing
    const relativeBearing = (bearingToDestination - deviceOrientation + 360) % 360;
    const screenX = width / 2 + Math.sin(relativeBearing * Math.PI / 180) * 100;
    const screenY = height / 2 - 150;

    // Draw directional arrow
    ctx.save();
    ctx.translate(screenX, screenY);
    ctx.rotate(relativeBearing * Math.PI / 180);

    // Arrow shape
    ctx.fillStyle = 'rgba(37, 99, 235, 0.9)';
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;

    ctx.beginPath();
    ctx.moveTo(0, -40);
    ctx.lineTo(-20, 20);
    ctx.lineTo(0, 10);
    ctx.lineTo(20, 20);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.restore();

    // Draw distance indicator
    ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
    ctx.strokeStyle = 'rgba(37, 99, 235, 0.9)';
    ctx.lineWidth = 2;
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';

    const distanceText = formatDistance(distanceToDestination);
    const textWidth = ctx.measureText(distanceText).width;

    // Background for distance
    ctx.fillStyle = 'rgba(37, 99, 235, 0.9)';
    ctx.fillRect(width / 2 - textWidth / 2 - 15, 50, textWidth + 30, 40);

    // Distance text
    ctx.fillStyle = '#ffffff';
    ctx.fillText(distanceText, width / 2, 77);

    // Draw instruction
    if (currentStep.instruction) {
      ctx.font = '18px Arial';
      const instructionWidth = ctx.measureText(currentStep.instruction).width;

      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
      ctx.fillRect(width / 2 - instructionWidth / 2 - 15, height - 100, instructionWidth + 30, 35);

      ctx.fillStyle = '#ffffff';
      ctx.fillText(currentStep.instruction, width / 2, height - 75);
    }

    // Draw checkpoint markers
    if (currentStep.checkpoint) {
      const markerX = width / 2;
      const markerY = height / 2 + 50;

      ctx.fillStyle = 'rgba(16, 185, 129, 0.9)';
      ctx.beginPath();
      ctx.arc(markerX, markerY, 15, 0, 2 * Math.PI);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopARSession();
    };
  }, [stopARSession]);

  return (
    <div className="ar-navigation relative w-full h-full bg-gray-900">
      {/* AR View */}
      {isARActive ? (
        <div className="relative w-full h-full">
          {/* Video stream */}
          <video
            ref={videoRef}
            className="absolute inset-0 w-full h-full object-cover"
            playsInline
            muted
          />

          {/* AR Canvas overlay */}
          <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full"
            width={window.innerWidth}
            height={window.innerHeight}
          />

          {/* AR Controls */}
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={stopARSession}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2"
            >
              <Camera size={20} />
              Exit AR
            </button>
          </div>

          {/* Navigation Info Panel */}
          <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur-sm rounded-xl p-4 shadow-lg z-10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-blue-600 p-2 rounded-lg">
                  <Navigation className="text-white" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Navigating to</p>
                  <p className="font-semibold text-gray-900">{destination.name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-600">{formatDistance(distanceToDestination)}</p>
                <p className="text-xs text-gray-600">remaining</p>
              </div>
            </div>

            {currentStep && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-sm text-gray-800">{currentStep.instruction}</p>
                {currentStep.distance > 0 && (
                  <p className="text-xs text-gray-600 mt-1">
                    In {formatDistance(currentStep.distance)}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* AR Start Screen */
        <div className="flex items-center justify-center h-full bg-gradient-to-b from-blue-900 to-blue-700 text-white">
          <div className="text-center px-6 max-w-md">
            {cameraPermission === 'denied' ? (
              <>
                <AlertCircle size={64} className="mx-auto mb-4 text-red-400" />
                <h2 className="text-2xl font-bold mb-2">Camera Access Denied</h2>
                <p className="text-blue-200 mb-6">
                  Please enable camera permissions to use AR navigation.
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50"
                >
                  Try Again
                </button>
              </>
            ) : (
              <>
                <div className="bg-white/10 backdrop-blur-sm rounded-full p-6 inline-block mb-6">
                  <Camera size={64} />
                </div>
                <h2 className="text-3xl font-bold mb-3">AR Navigation</h2>
                <p className="text-blue-200 mb-8">
                  Point your phone to see directions overlaid on the real world
                </p>

                {!isARSupported && (
                  <div className="bg-yellow-500/20 border border-yellow-500 rounded-lg p-3 mb-6">
                    <p className="text-sm text-yellow-200">
                      Full AR not supported. Using camera-based navigation.
                    </p>
                  </div>
                )}

                <button
                  onClick={startARSession}
                  className="bg-white text-blue-600 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-blue-50 shadow-xl flex items-center gap-3 mx-auto"
                >
                  <Camera size={24} />
                  Start AR Navigation
                </button>

                {/* Feature highlights */}
                <div className="mt-8 space-y-3 text-left">
                  <div className="flex items-start gap-3">
                    <Compass className="text-blue-300 flex-shrink-0 mt-1" size={20} />
                    <div>
                      <p className="font-semibold">Turn-by-turn directions</p>
                      <p className="text-sm text-blue-200">3D arrows guide you through the airport</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <MapPin className="text-blue-300 flex-shrink-0 mt-1" size={20} />
                    <div>
                      <p className="font-semibold">Visual markers</p>
                      <p className="text-sm text-blue-200">See checkpoints in real-time</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Navigation className="text-blue-300 flex-shrink-0 mt-1" size={20} />
                    <div>
                      <p className="font-semibold">Distance tracking</p>
                      <p className="text-sm text-blue-200">Know exactly how far to your destination</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 2D Navigation Fallback */}
      {!isARActive && currentPosition && (
        <div className="absolute bottom-20 left-4 right-4">
          <div className="bg-white/95 backdrop-blur-sm rounded-lg p-4 shadow-lg">
            <p className="text-sm text-gray-600 mb-2">Or use 2D navigation</p>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">{destination.name}</p>
                <p className="text-sm text-gray-600">{formatDistance(distanceToDestination)}</p>
              </div>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                Map View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ARNavigation;
