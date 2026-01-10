/**
 * Telemetry Consent Dialog
 *
 * GDPR/privacy-compliant consent dialog for telemetry collection.
 * Explains what data is collected and how it's used.
 */

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Shield, Activity, MapPin, Users, Lock } from 'lucide-react';

interface TelemetryConsentDialogProps {
  open: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export function TelemetryConsentDialog({ open, onAccept, onDecline }: TelemetryConsentDialogProps) {
  const [understandPrivacy, setUnderstandPrivacy] = useState(false);

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onDecline()}>
      <DialogContent className="bg-slate-800 border-slate-700 max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2 text-xl">
            <Shield className="w-6 h-6 text-blue-400" />
            Help Improve AirportWaze for Everyone
          </DialogTitle>
          <DialogDescription className="text-slate-300 space-y-4 text-base pt-4">
            <p>
              We'd like to collect anonymous location data while you're at the airport to create better
              wait time predictions for all travelers. This works like Waze or Google Maps traffic data.
            </p>

            <div className="bg-slate-700/50 rounded-lg p-4 space-y-4">
              <div className="flex items-start gap-3">
                <Activity className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
                <div>
                  <strong className="text-green-400 block mb-2">What we collect:</strong>
                  <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
                    <li>Your location while inside the airport (GPS coordinates)</li>
                    <li>Movement patterns (walking speed, direction, waiting times)</li>
                    <li>How long you spend at each checkpoint</li>
                    <li>Time and day of week (for peak hour analysis)</li>
                  </ul>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-blue-400 mt-1 flex-shrink-0" />
                <div>
                  <strong className="text-blue-400 block mb-2">Privacy guarantees:</strong>
                  <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
                    <li>
                      <strong>No personally identifiable information</strong> - We don't collect your name,
                      email, phone number, or any PII
                    </li>
                    <li>
                      <strong>Anonymous UUID</strong> - A random ID is generated on your device (not
                      linked to your identity)
                    </li>
                    <li>
                      <strong>K-anonymity protection</strong> - Data is only shown when aggregated with
                      10+ other users
                    </li>
                    <li>
                      <strong>WiFi-only uploads</strong> - Data is uploaded only on WiFi to save your mobile data
                    </li>
                    <li>
                      <strong>Opt-out anytime</strong> - You can disable telemetry in settings at any time
                    </li>
                    <li>
                      <strong>Data retention</strong> - Raw data is kept for 90 days, then automatically
                      deleted
                    </li>
                  </ul>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-purple-400 mt-1 flex-shrink-0" />
                <div>
                  <strong className="text-purple-400 block mb-2">How it helps you and others:</strong>
                  <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
                    <li>More accurate real-time wait predictions</li>
                    <li>Better checkpoint recommendations (faster security lines)</li>
                    <li>Improved "Will I Make It?" probability calculations</li>
                    <li>Automatic discovery of new checkpoints and routes</li>
                    <li>Help fellow travelers make better decisions</li>
                  </ul>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Users className="w-5 h-5 text-orange-400 mt-1 flex-shrink-0" />
                <div>
                  <strong className="text-orange-400 block mb-2">Community-powered:</strong>
                  <p className="text-sm text-slate-400">
                    Like Waze for traffic or Moovit for transit, AirportWaze gets better with more users
                    contributing data. Your anonymous location data helps improve predictions for millions
                    of travelers.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Lock className="w-5 h-5 text-red-400 mt-1 flex-shrink-0" />
                <div>
                  <strong className="text-red-400 block mb-2">Your rights:</strong>
                  <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
                    <li>
                      <strong>Right to access:</strong> View what data we have (contact support)
                    </li>
                    <li>
                      <strong>Right to deletion:</strong> Request deletion of your data anytime
                    </li>
                    <li>
                      <strong>Right to opt-out:</strong> Disable telemetry in settings
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-2 pt-2">
              <Checkbox
                id="privacy"
                checked={understandPrivacy}
                onCheckedChange={(checked) => setUnderstandPrivacy(checked as boolean)}
              />
              <label
                htmlFor="privacy"
                className="text-sm text-slate-300 cursor-pointer leading-relaxed"
              >
                I understand how my data will be used and agree to anonymous data collection for
                improving wait time predictions. I can opt out anytime in settings.
              </label>
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-3 pt-4">
          <Button
            onClick={onDecline}
            variant="outline"
            className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            No Thanks
          </Button>
          <Button
            onClick={() => {
              if (understandPrivacy) {
                onAccept();
              }
            }}
            disabled={!understandPrivacy}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            Enable Data Sharing
          </Button>
        </div>

        <p className="text-xs text-slate-500 text-center pt-2">
          By enabling, you agree to our{' '}
          <a href="/privacy" className="underline hover:text-slate-400">
            Privacy Policy
          </a>{' '}
          and{' '}
          <a href="/terms" className="underline hover:text-slate-400">
            Terms of Service
          </a>
        </p>
      </DialogContent>
    </Dialog>
  );
}
