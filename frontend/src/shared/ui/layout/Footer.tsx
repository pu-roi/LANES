import React from 'react';
import { LegalNoticeTrigger } from '@/features/legal/LegalNoticeTrigger';

export function Footer() {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 pt-12 pb-[calc(3rem+var(--bottom-nav-height)+env(safe-area-inset-bottom))] sm:pb-12 mt-auto">
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex flex-col md:flex-row justify-between items-center text-sm text-slate-400 gap-4">
        <p className="font-medium">&copy; {new Date().getFullYear()} LANES Project. All rights reserved.</p>
        <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
          <LegalNoticeTrigger notice="privacy" className="hover:text-white focus-visible:text-white focus-visible:underline transition-colors font-medium">Privacy Policy</LegalNoticeTrigger>
          <LegalNoticeTrigger notice="terms" className="hover:text-white focus-visible:text-white focus-visible:underline transition-colors font-medium">Terms of Service</LegalNoticeTrigger>
        </div>
      </div>
    </footer>
  );
}
