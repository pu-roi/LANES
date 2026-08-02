import React, { useState, useEffect } from 'react';
import { Sparkles, X, CloudRain, Droplets, Thermometer, Wind, Loader2 } from 'lucide-react';

interface ForecastSlot {
  dt: number;
  time: string;
  temp: number;
  pop: number;
  condition: string;
  icon: string;
  precip_mm?: number;
  showers_mm?: number;
  wind_kmh?: number;
  wind_dir?: number;
  humidity_pct?: number;
}

interface WeatherInsightsModalProps {
  isOpen: boolean;
  onClose: () => void;
  forecast: ForecastSlot[];
  location: string;
}

interface AIInsights {
  storm_risk?: string;
  environment?: string;
}

export function WeatherInsightsModal({ isOpen, onClose, forecast, location }: WeatherInsightsModalProps) {
  const [insights, setInsights] = useState<AIInsights | null>(null);
  const [model, setModel] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Removed useEffect that auto-fetches

  const fetchInsights = async () => {
    if (forecast.length === 0) return;
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/v1/weather/insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          forecast,
          location
        }),
      });

      if (!response.ok) {
        // Try to get detail
        let errorMsg = 'Failed to fetch insights';
        try {
          const errData = await response.json();
          if (errData.detail) errorMsg = errData.detail;
        } catch(e) {}
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setInsights(data.insights);
      setModel(data.model);
    } catch (err: any) {
      console.error('Error fetching insights:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop overlay for mobile */}
      <div
        className="fixed inset-0 bg-black/40 z-[99] sm:hidden"
        onClick={onClose}
      />

      {/* Modal / Popover Content */}
      <div className="fixed sm:absolute z-[100] bottom-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] sm:bottom-auto left-0 right-0 sm:left-auto sm:right-6 sm:top-17 sm:w-[450px] bg-white sm:rounded-2xl rounded-t-2xl shadow-2xl border border-gray-100 overflow-hidden transform transition-transform flex flex-col max-h-[85vh]">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50/50 shrink-0">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-blue-600" />
              </div>
              <h3 className="font-bold text-gray-900">AI Weather Insights</h3>
            </div>
            {model && (
              <p className="text-[10px] text-gray-500 mt-1 ml-10 font-medium">
                Powered by: <span className="text-gray-700">{model}</span>
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-gray-50 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto custom-scrollbar pb-[calc(1.25rem+env(safe-area-inset-bottom))] sm:pb-5">
          
          {/* Dynamic AI Insights Section */}
          <div className="mb-6">
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">AI Explanation</h4>
            
            {loading ? (
              <div className="flex flex-col items-center justify-center py-6 text-gray-400">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500 mb-2" />
                <p className="text-sm">Analyzing weather patterns...</p>
              </div>
            ) : error ? (
              <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm mb-4">
                {error}
                <button 
                  onClick={fetchInsights}
                  className="mt-3 px-4 py-2 bg-white text-red-600 rounded-lg text-sm font-semibold border border-red-200 hover:bg-red-50 transition-colors w-full"
                >
                  Try Again
                </button>
              </div>
            ) : insights ? (
              <div className="space-y-3">
                {/* Storm Risk Summary */}
                {insights.storm_risk && (
                  <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100/50">
                    <div className="flex items-center gap-2 mb-1">
                      <CloudRain className="w-3.5 h-3.5 text-blue-600" />
                      <h5 className="font-semibold text-gray-900 text-sm">Storm & Flood Risk</h5>
                    </div>
                    <p className="text-xs text-gray-700 leading-snug">
                      {insights.storm_risk}
                    </p>
                  </div>
                )}
                
                {/* Environment Summary */}
                {insights.environment && (
                  <div className="p-3 bg-teal-50/50 rounded-xl border border-teal-100/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Thermometer className="w-3.5 h-3.5 text-teal-600" />
                      <h5 className="font-semibold text-gray-900 text-sm">Environmental Conditions</h5>
                    </div>
                    <p className="text-xs text-gray-700 leading-snug">
                      {insights.environment}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 flex flex-col items-center text-center">
                <Sparkles className="w-6 h-6 text-blue-500 mb-2" />
                <p className="text-sm text-gray-600 mb-4">Generate a personalized, intelligent summary of the current forecast conditions.</p>
                <button 
                  onClick={fetchInsights}
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-colors shadow-sm w-full"
                >
                  Generate AI Insights
                </button>
              </div>
            )}
          </div>

          <div className="h-px bg-gray-100 w-full mb-5" />

          {/* Static Chart Legend */}
          <div>
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Chart Legend</h4>

            <div className="space-y-4">
              {/* Rain Risk */}
              <div className="flex items-start gap-3">
                <div className="mt-0.5 w-6 h-6 rounded-md bg-blue-100 flex items-center justify-center shrink-0">
                  <CloudRain className="w-3.5 h-3.5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Storm Risk (Blue Graph)</p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-snug">The dark blue bars and line represent the probability of rain (%). The raindrop icons show the expected volume (mm/h).</p>
                </div>
              </div>

              {/* Temperature */}
              <div className="flex items-start gap-3">
                <div className="mt-0.5 w-6 h-6 rounded-md bg-red-50 flex items-center justify-center shrink-0">
                  <Thermometer className="w-3.5 h-3.5 text-red-500" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Temperature (Red Line)</p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-snug">The red curve represents the ambient temperature in degrees Celsius (°C) over time.</p>
                </div>
              </div>

              {/* Humidity */}
              <div className="flex items-start gap-3">
                <div className="mt-0.5 w-6 h-6 rounded-md bg-teal-50 flex items-center justify-center shrink-0">
                  <Droplets className="w-3.5 h-3.5 text-teal-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Humidity (Teal Line)</p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-snug">The teal curve shows the relative humidity percentage. Higher humidity makes the air feel warmer and stickier.</p>
                </div>
              </div>

              {/* Wind */}
              <div className="flex items-start gap-3">
                <div className="mt-0.5 w-6 h-6 rounded-md bg-gray-100 flex items-center justify-center shrink-0">
                  <Wind className="w-3.5 h-3.5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Wind (Arrows)</p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-snug">The tiny arrows on the timeline indicate wind direction and speed (km/h).</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
