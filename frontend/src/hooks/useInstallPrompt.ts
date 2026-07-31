import { useState, useEffect } from 'react';

// Define the BeforeInstallPromptEvent interface since it's not standard in TypeScript DOM types yet
interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isAppInstalled, setIsAppInstalled] = useState(false);

  useEffect(() => {
    // Check if the app is already running as standalone (installed)
    if (window.matchMedia('(display-mode: standalone)').matches || (window.navigator as any).standalone === true) {
      setIsAppInstalled(true);
    }

    const handleBeforeInstallPrompt = (e: Event) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      // Stash the event so it can be triggered later.
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };

    const handleAppInstalled = () => {
      // Clear the prompt once the app is installed
      setDeferredPrompt(null);
      setIsAppInstalled(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const triggerInstall = async () => {
    if (!deferredPrompt) {
      if (process.env.NODE_ENV === 'development') {
        alert("PWA Installation is disabled in development mode. Build the app for production to fully test this feature.");
      }
      return;
    }

    // Show the install prompt
    await deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    
    // We no longer need the prompt. Clear it up.
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
    }
  };

  const isDev = process.env.NODE_ENV === 'development';

  return {
    isInstallable: isDev || (deferredPrompt !== null && !isAppInstalled),
    triggerInstall,
    isAppInstalled
  };
}
