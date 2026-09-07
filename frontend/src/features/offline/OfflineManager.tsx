import React, { useState, useEffect } from 'react';
import { CloudDownload, CheckCircle, WifiOff } from 'lucide-react';
import { downloadRoutingTiles, isRoutingDataAvailable } from '@/lib/offline/storage';

export const OfflineManager: React.FC = () => {
  const [isAvailable, setIsAvailable] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [downloadStats, setDownloadStats] = useState<{ speed: string; eta: string } | null>(null);

  useEffect(() => {
    isRoutingDataAvailable('philippines_routing.tar').then(setIsAvailable);
  }, []);

  const handleDownload = async () => {
    if (!window.confirm("This will download offline routing map data (~580MB). Wi-Fi is strongly recommended. Continue?")) {
      return;
    }
    
    setIsDownloading(true);
    setProgress(0);
    setDownloadStats(null);
    
    const startTime = Date.now();
    
    // In production, this URL will point to our backend's static directory
    const url = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace('/api/v1', '') + '/static/valhalla/valhalla_tiles.tar';
    
    const success = await downloadRoutingTiles(
      url,
      'philippines_routing.tar',
      (pct, loadedBytes, totalBytes) => {
        setProgress(pct);
        if (loadedBytes && totalBytes) {
          const elapsedSec = (Date.now() - startTime) / 1000;
          if (elapsedSec > 0.5) {
            const bytesPerSec = loadedBytes / elapsedSec;
            const remainingBytes = totalBytes - loadedBytes;
            const remainingSec = Math.max(0, Math.round(remainingBytes / bytesPerSec));

            const speedMb = (bytesPerSec / (1024 * 1024)).toFixed(1);
            const speedStr = `${speedMb} MB/s`;

            let etaStr = "";
            if (remainingSec < 60) {
              etaStr = `${remainingSec}s remaining`;
            } else {
              const mins = Math.floor(remainingSec / 60);
              const secs = remainingSec % 60;
              etaStr = `${mins}m ${secs}s remaining`;
            }

            setDownloadStats({ speed: speedStr, eta: etaStr });
          }
        }
      }
    );
    
    if (success) {
      setIsAvailable(true);
      alert("Offline routing data downloaded successfully!");
    } else {
      alert("Failed to download offline routing data.");
    }
    setIsDownloading(false);
    setDownloadStats(null);
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-full shrink-0 ${isAvailable ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'}`}>
          {isAvailable ? <CheckCircle size={18} /> : <WifiOff size={18} />}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-gray-800 text-xs leading-tight">Offline Routing</h3>
          <p className="text-[11px] text-gray-500 truncate">
            {isAvailable ? 'Ready for offline use' : 'Download required (~580MB)'}
          </p>
        </div>
      </div>

      {!isAvailable && !isDownloading && (
        <button
          onClick={handleDownload}
          className="w-full mt-2.5 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white py-1.5 px-3 rounded-lg text-xs font-semibold transition-colors shadow-sm"
        >
          <CloudDownload size={14} />
          Download Map Data
        </button>
      )}

      {isDownloading && (
        <div className="mt-2.5">
          <div className="flex justify-between text-[11px] text-gray-700 mb-1 font-medium">
            <span>{downloadStats ? downloadStats.eta : "Calculating time..."}</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300" 
              style={{ width: `${progress}%` }}
            />
          </div>
          {downloadStats && (
            <div className="flex justify-between text-[10px] text-gray-400 mt-1">
              <span>Speed: {downloadStats.speed}</span>
              <span>Est. time remaining</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
