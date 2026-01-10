/**
 * Boarding Pass Scanner Component
 *
 * Features:
 * - Camera-based QR code scanning
 * - IATA BCBP format support
 * - Real-time scanning feedback
 * - Manual entry fallback
 * - Beautiful iOS-style UI
 */

import { useRef, useState } from 'react';
import { boardingPassScanner, FlightInfo, ScanResult } from '../services/boardingPassScanner';
import { BottomSheet } from './BottomSheet';
import '../styles/ios-design-tokens.css';

interface BoardingPassScannerProps {
  isOpen: boolean;
  onClose: () => void;
  onFlightDetected: (flightInfo: FlightInfo) => void;
}

export function BoardingPassScannerComponent({
  isOpen,
  onClose,
  onFlightDetected
}: BoardingPassScannerProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleStartScan = async () => {
    if (!videoRef.current) return;

    setIsScanning(true);
    setScanResult(null);

    await boardingPassScanner.startScanning(videoRef.current, (result) => {
      setScanResult(result);

      if (result.success && result.flightInfo) {
        // Success! Stop scanning and return result
        handleStopScan();
        onFlightDetected(result.flightInfo);
        onClose();
      }
    });
  };

  const handleStopScan = () => {
    if (videoRef.current) {
      boardingPassScanner.stopScanning(videoRef.current);
    }
    setIsScanning(false);
  };

  const handleManualEntry = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);

    const flightInfo = boardingPassScanner.createManualEntry(
      formData.get('flightNumber') as string,
      formData.get('airport') as string,
      new Date(formData.get('date') as string),
      formData.get('gate') as string || undefined,
      formData.get('terminal') as string || undefined
    );

    onFlightDetected(flightInfo);
    onClose();
  };

  return (
    <BottomSheet
      isOpen={isOpen}
      onClose={() => {
        handleStopScan();
        onClose();
      }}
      title="Scan Boarding Pass"
      snapPoints={['full']}
      initialSnap="full"
    >
      {!showManualEntry ? (
        <div className="space-y-6">
          {/* Instructions */}
          <div className="ios-card p-4">
            <h3
              className="ios-headline mb-2"
              style={{ color: 'var(--ios-label)' }}
            >
              📸 How to Scan
            </h3>
            <ul
              className="ios-callout space-y-2"
              style={{ color: 'var(--ios-label-secondary)' }}
            >
              <li>• Point camera at your boarding pass QR code</li>
              <li>• Hold steady until it scans automatically</li>
              <li>• Works with paper and mobile boarding passes</li>
            </ul>
          </div>

          {/* Camera View */}
          <div className="relative">
            <video
              ref={videoRef}
              className="w-full rounded-xl"
              style={{
                aspectRatio: '4/3',
                backgroundColor: 'var(--ios-gray6)',
                objectFit: 'cover'
              }}
              playsInline
              muted
            />

            {!isScanning && (
              <div
                className="absolute inset-0 flex items-center justify-center rounded-xl"
                style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}
              >
                <div className="text-center text-white">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 opacity-80"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p className="ios-headline">Camera Preview</p>
                </div>
              </div>
            )}

            {isScanning && (
              <div className="absolute inset-0 pointer-events-none">
                {/* Scanning Overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div
                    className="w-64 h-64 border-4 rounded-xl animate-pulse"
                    style={{
                      borderColor: 'var(--ios-blue)',
                      boxShadow: '0 0 20px rgba(0, 122, 255, 0.5)'
                    }}
                  />
                </div>

                {/* Scanning Line */}
                <div
                  className="absolute left-1/2 w-64 h-1 rounded-full animate-pulse"
                  style={{
                    backgroundColor: 'var(--ios-blue)',
                    transform: 'translateX(-50%)',
                    animation: 'scan 2s linear infinite',
                    boxShadow: '0 0 10px rgba(0, 122, 255, 0.8)'
                  }}
                />
              </div>
            )}
          </div>

          {/* Scan Result */}
          {scanResult && !scanResult.success && (
            <div
              className="p-4 rounded-xl"
              style={{
                backgroundColor: 'var(--ios-fill)',
                borderLeft: '4px solid var(--ios-orange)'
              }}
            >
              <p className="ios-callout" style={{ color: 'var(--ios-label)' }}>
                {scanResult.error}
              </p>
            </div>
          )}

          {/* Buttons */}
          <div className="space-y-3">
            {!isScanning ? (
              <button
                onClick={handleStartScan}
                className="w-full ios-button py-4 text-lg"
              >
                📸 Start Scanning
              </button>
            ) : (
              <button
                onClick={handleStopScan}
                className="w-full py-4 text-lg rounded-xl font-semibold"
                style={{
                  backgroundColor: 'var(--ios-red)',
                  color: 'white'
                }}
              >
                ⏹️ Stop Scanning
              </button>
            )}

            <button
              onClick={() => setShowManualEntry(true)}
              className="w-full ios-button-secondary py-4 text-lg"
            >
              ✍️ Enter Manually
            </button>
          </div>

          {/* Privacy Notice */}
          <div className="ios-footnote text-center" style={{ color: 'var(--ios-label-tertiary)' }}>
            🔒 Your boarding pass data stays on your device.
            <br />
            We never store or share your flight information.
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Manual Entry Form */}
          <div
            className="flex items-center gap-2 mb-4 cursor-pointer"
            onClick={() => setShowManualEntry(false)}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
              style={{ color: 'var(--ios-blue)' }}
            >
              <path d="M15 19l-7-7 7-7" />
            </svg>
            <span className="ios-headline" style={{ color: 'var(--ios-blue)' }}>
              Back to Scanner
            </span>
          </div>

          <form onSubmit={handleManualEntry} className="space-y-4">
            <div>
              <label className="ios-callout block mb-2" style={{ color: 'var(--ios-label)' }}>
                Flight Number
              </label>
              <input
                type="text"
                name="flightNumber"
                placeholder="AA123"
                required
                className="w-full px-4 py-3 rounded-xl ios-callout"
                style={{
                  backgroundColor: 'var(--ios-fill)',
                  border: 'none',
                  color: 'var(--ios-label)'
                }}
              />
            </div>

            <div>
              <label className="ios-callout block mb-2" style={{ color: 'var(--ios-label)' }}>
                Airport
              </label>
              <input
                type="text"
                name="airport"
                placeholder="JFK"
                required
                maxLength={3}
                className="w-full px-4 py-3 rounded-xl ios-callout uppercase"
                style={{
                  backgroundColor: 'var(--ios-fill)',
                  border: 'none',
                  color: 'var(--ios-label)'
                }}
              />
            </div>

            <div>
              <label className="ios-callout block mb-2" style={{ color: 'var(--ios-label)' }}>
                Departure Date
              </label>
              <input
                type="date"
                name="date"
                required
                className="w-full px-4 py-3 rounded-xl ios-callout"
                style={{
                  backgroundColor: 'var(--ios-fill)',
                  border: 'none',
                  color: 'var(--ios-label)'
                }}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ios-callout block mb-2" style={{ color: 'var(--ios-label)' }}>
                  Terminal (Optional)
                </label>
                <input
                  type="text"
                  name="terminal"
                  placeholder="1"
                  className="w-full px-4 py-3 rounded-xl ios-callout"
                  style={{
                    backgroundColor: 'var(--ios-fill)',
                    border: 'none',
                    color: 'var(--ios-label)'
                  }}
                />
              </div>

              <div>
                <label className="ios-callout block mb-2" style={{ color: 'var(--ios-label)' }}>
                  Gate (Optional)
                </label>
                <input
                  type="text"
                  name="gate"
                  placeholder="A1"
                  className="w-full px-4 py-3 rounded-xl ios-callout uppercase"
                  style={{
                    backgroundColor: 'var(--ios-fill)',
                    border: 'none',
                    color: 'var(--ios-label)'
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full ios-button py-4 text-lg mt-6"
            >
              ✈️ Continue
            </button>
          </form>
        </div>
      )}

      <style>{`
        @keyframes scan {
          0% { top: 10%; }
          50% { top: 90%; }
          100% { top: 10%; }
        }
      `}</style>
    </BottomSheet>
  );
}
