/**
 * PWA Install Button Component
 *
 * Displays an "Install App" button when the app is installable.
 * Prompts the user to add the app to their home screen.
 */

import { usePWAInstall } from '../hooks/usePWAInstall';

export function PWAInstallButton() {
  const { isInstallable, isInstalled, promptInstall } = usePWAInstall();

  // Don't show if already installed or not installable
  if (isInstalled || !isInstallable) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 md:left-auto md:right-4 md:w-auto">
      <div className="bg-blue-600 text-white rounded-lg shadow-lg p-4 flex items-center gap-3">
        <div className="flex-shrink-0">
          <svg
            className="w-8 h-8"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        </div>

        <div className="flex-grow">
          <h3 className="font-semibold text-sm">Install AirportWaze</h3>
          <p className="text-xs opacity-90">Add to your home screen for faster access</p>
        </div>

        <button
          onClick={promptInstall}
          className="flex-shrink-0 bg-white text-blue-600 px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-50 transition-colors"
        >
          Install
        </button>

        <button
          onClick={() => {
            // Close the prompt (could add to localStorage to not show again)
            const element = document.querySelector('[data-pwa-prompt]');
            if (element) {
              (element as HTMLElement).style.display = 'none';
            }
          }}
          className="flex-shrink-0 text-white hover:text-blue-100 transition-colors"
          aria-label="Close"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
