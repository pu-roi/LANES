import { WifiOff, AlertTriangle, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function OfflineFallback() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-140px)] p-6 text-center">
      <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6 shadow-sm">
        <WifiOff className="w-10 h-10 text-gray-400" />
      </div>
      
      <h1 className="text-2xl font-bold text-gray-900 mb-2">You are Offline</h1>
      <p className="text-gray-500 mb-8 max-w-sm">
        It looks like you've lost your internet connection. This page hasn't been cached yet.
      </p>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 max-w-sm w-full text-left mb-8 shadow-sm">
        <div className="flex gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-800 text-sm mb-1">Calamity Protocol</h3>
            <p className="text-amber-700 text-xs leading-relaxed">
              During heavy rains or flooding, signal loss is common. Previously loaded map areas and your saved routes remain accessible. Return to the map to view them.
            </p>
          </div>
        </div>
      </div>

      <Link 
        href="/map" 
        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-xl transition-colors shadow-sm"
      >
        <ArrowLeft className="w-5 h-5" />
        Return to Cached Map
      </Link>
    </div>
  );
}
