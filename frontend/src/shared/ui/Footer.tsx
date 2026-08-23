import React from 'react';

export function Footer() {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 py-12 mt-auto">
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex flex-col md:flex-row justify-between items-center text-sm text-slate-400 gap-4">
        <p className="font-medium">&copy; {new Date().getFullYear()} LANES Project. All rights reserved.</p>
        <div className="flex gap-6">
          <a href="#" className="hover:text-white transition-colors font-medium">Privacy Policy</a>
          <a href="#" className="hover:text-white transition-colors font-medium">Terms of Service</a>
        </div>
      </div>
    </footer>
  );
}
