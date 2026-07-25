"use client";

import { useEffect, useState } from "react";
import { MapPin } from "lucide-react";

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

export function ForecastChart() {
  const [forecast, setForecast] = useState<ForecastSlot[]>([]);
  const [location, setLocation] = useState<string>("Pasig");
  const [loading, setLoading] = useState(true);
  const [hoveredEnvIndex, setHoveredEnvIndex] = useState<number | null>(null);

  useEffect(() => {
    async function fetchForecast() {
      try {
        const res = await fetch("http://localhost:8000/api/v1/weather/forecast?count=12");
          if (res.ok) {
          const data = await res.json();
          setForecast(data.forecast || []);
          setLocation(data.location || "Pasig");
        }
      } catch (err) {
        console.error("Failed to fetch forecast:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchForecast();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 w-full h-[250px] animate-pulse flex flex-col">
        <div className="h-4 w-32 bg-gray-200 rounded mb-4"></div>
        <div className="flex-1 bg-gray-50 rounded-xl"></div>
      </div>
    );
  }

  // Fallback to mock data if the API fails or returns empty (e.g. no API key)
  const displayForecast = forecast.length > 0 ? forecast : [
    { dt: 1, time: new Date().toISOString(), temp: 30, pop: 10, condition: "Clouds", icon: "04d" },
    { dt: 2, time: new Date(Date.now() + 3 * 3600000).toISOString(), temp: 31, pop: 40, condition: "Rain", icon: "10d" },
    { dt: 3, time: new Date(Date.now() + 6 * 3600000).toISOString(), temp: 29, pop: 80, condition: "Rain", icon: "09d" },
    { dt: 4, time: new Date(Date.now() + 9 * 3600000).toISOString(), temp: 28, pop: 90, condition: "Thunderstorm", icon: "11d" },
    { dt: 5, time: new Date(Date.now() + 12 * 3600000).toISOString(), temp: 27, pop: 60, condition: "Rain", icon: "10n" },
    { dt: 6, time: new Date(Date.now() + 15 * 3600000).toISOString(), temp: 26, pop: 20, condition: "Clouds", icon: "04n" },
    { dt: 7, time: new Date(Date.now() + 18 * 3600000).toISOString(), temp: 28, pop: 0, condition: "Clear", icon: "01d" },
    { dt: 8, time: new Date(Date.now() + 21 * 3600000).toISOString(), temp: 31, pop: 0, condition: "Clear", icon: "01d" },
  ];

  // Layout Math
  const width = 800;
  const leftLabelWidth = 80;
  const paddingRight = 40;
  const pointSpacing = (width - leftLabelWidth - paddingRight) / (displayForecast.length - 1);

  // SVG 1: Storm Risk (Rain)
  const svg1Height = 210;
  const s1PadTop = 60;
  const s1PadBot = 60;
  const s1GraphH = svg1Height - s1PadTop - s1PadBot;

  // SVG 2: Environment (Temp & Humidity axes)
  const svg2Height = 250;
  const s2PadTop = 40;
  const s2PadBot = 70;
  const s2GraphH = svg2Height - s2PadTop - s2PadBot;

  // Generate points for both graphs
  const points = displayForecast.map((f, i) => {
    const x = leftLabelWidth + i * pointSpacing;
    const pop = f.pop || 0;
    
    // SVG 1: Rain % Line Y
    const y1 = svg1Height - s1PadBot - (pop / 100) * s1GraphH;
    
    // SVG 2: Temp Line Y (Scale 5 to 55)
    const y2_temp = svg2Height - s2PadBot - ((f.temp - 5) / 50) * s2GraphH;

    // SVG 2: Humidity Line Y (Scale 0 to 100)
    const y2_hum = svg2Height - s2PadBot - ((f.humidity_pct || 0) / 100) * s2GraphH;

    return { 
      x, y1, y2_temp, y2_hum,
      temp: f.temp, pop, icon: f.icon, 
      precip_mm: f.precip_mm || 0, wind_kmh: f.wind_kmh || 0, wind_dir: f.wind_dir || 0, humidity_pct: f.humidity_pct || 0, 
      time: new Date(f.dt * 1000) 
    };
  });

  // SVG 1 Paths (Rain)
  const linePath1 = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y1}` : `L ${p.x} ${p.y1}`)).join(" ");
  const areaPath1 = `${linePath1} L ${points[points.length - 1].x} ${svg1Height - s1PadBot} L ${points[0].x} ${svg1Height - s1PadBot} Z`;

  // SVG 2 Paths (Temp & Humidity)
  const linePathTemp = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y2_temp}` : `L ${p.x} ${p.y2_temp}`)).join(" ");
  const linePathHum = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y2_hum}` : `L ${p.x} ${p.y2_hum}`)).join(" ");


  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 w-full overflow-hidden">
      <div className="flex items-center gap-3 mb-6">
        <h3 className="text-sm font-semibold text-gray-800">12-Hour Detailed Forecast</h3>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-100">
          <MapPin className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider">{location}</span>
        </div>
      </div>
      
      <div className="overflow-x-auto pb-4 custom-scrollbar">
        <div className="min-w-[750px] w-full flex flex-col gap-6">
          
          {/* ===================== GRAPH 1: STORM RISK ===================== */}
          <div>
            <h4 className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-1 ml-4">Storm & Flood Risk</h4>
            <div className="bg-slate-200 rounded-xl border border-slate-300 p-2">
              <svg viewBox={`0 0 ${width} ${svg1Height}`} className="w-full h-auto overflow-visible">
                <defs>
                  <linearGradient id="areaGradientRain" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity="0.45" />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
                  </linearGradient>
                </defs>

                <path d={areaPath1} fill="url(#areaGradientRain)" />
                <path d={linePath1} fill="none" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                <line x1={leftLabelWidth} y1={svg1Height - s1PadBot} x2={width - paddingRight} y2={svg1Height - s1PadBot} stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />

                {/* Y-Axis Row Labels */}
                <g fill="#64748b" fontSize="10" fontWeight="600" textAnchor="start">
                  <text x="5" y="30">Weather</text>
                  <text x="5" y="80">Rain %</text>
                  <text x="5" y={svg1Height - s1PadBot + 20}>Volume</text>
                  <text x="5" y={svg1Height - s1PadBot + 42}>Time</text>
                </g>

                {points.map((p, i) => {
                  const hour = p.time.getHours();
                  const ampm = hour >= 12 ? 'PM' : 'AM';
                  const displayHour = hour % 12 === 0 ? 12 : hour % 12;
                  return (
                    <g key={i}>
                      <image href={`/meteocons/${p.icon}.svg`} x={p.x - 24} y={0} width="48" height="48" />
                      <circle cx={p.x} cy={p.y1} r="4" fill="#ffffff" stroke="#3b82f6" strokeWidth="2" />
                      <text x={p.x} y={p.y1 - 12} textAnchor="middle" fill="#2563eb" fontSize="11" fontWeight="800">{p.pop}%</text>
                      
                      {p.precip_mm > 0 ? (
                        <g transform={`translate(${p.x}, ${svg1Height - s1PadBot + 16})`}>
                          <rect x="-18" y="-12" width="36" height="18" rx="4" fill="#eff6ff" stroke="#bfdbfe" />
                          <text x="0" y="4" textAnchor="middle" fill="#1e3a8a" fontSize="10" fontWeight="700">{p.precip_mm}mm</text>
                        </g>
                      ) : (
                        <text x={p.x} y={svg1Height - s1PadBot + 20} textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">0 mm</text>
                      )}
                      <text x={p.x} y={svg1Height - s1PadBot + 42} textAnchor="middle" fill="#475569" fontSize="10" fontWeight="600">{displayHour} {ampm}</text>
                    </g>
                  )
                })}
              </svg>
            </div>
          </div>

          {/* ===================== GRAPH 2: ENVIRONMENT ===================== */}
          <div>
            <h4 className="text-[10px] font-bold text-orange-500 uppercase tracking-widest mb-1 ml-4">Environment</h4>
            <div className="bg-slate-200 rounded-xl border border-slate-300 p-2">
              <svg viewBox={`0 0 ${width} ${svg2Height}`} className="w-full h-auto overflow-visible">
                {/* Axis Titles */}
                <g fontSize="10" fontWeight="700">
                  <text x={leftLabelWidth} y={20} textAnchor="end" fill="#c2410c">Temperature</text>
                  <text x={width - paddingRight} y={20} textAnchor="start" fill="#047857">Humidity</text>
                </g>
                
                {/* Horizontal Grid Lines & Axes (Drawn First so they are behind the graph) */}
                {[0, 1, 2, 3, 4, 5].map((step) => {
                  const y = s2PadTop + (step / 5) * s2GraphH;
                  const tempVal = 55 - step * 10;
                  const humVal = 100 - step * 20;
                  return (
                    <g key={step}>
                      <line x1={leftLabelWidth} y1={y} x2={width - paddingRight} y2={y} stroke="#cbd5e1" strokeWidth="1" />
                      {/* Left Axis: Temp */}
                      <text x={leftLabelWidth - 10} y={y + 4} textAnchor="end" fill="#c2410c" fontSize="10" fontWeight="600">{tempVal}°</text>
                      {/* Right Axis: Humidity */}
                      <text x={width - paddingRight + 10} y={y + 4} textAnchor="start" fill="#047857" fontSize="10" fontWeight="600">{humVal}%</text>
                    </g>
                  );
                })}

                {/* Humidity Line (Green Solid) */}
                <path d={linePathHum} fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                {/* Temperature Line (Orange Solid) */}
                <path d={linePathTemp} fill="none" stroke="#f97316" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

                {/* Y-Axis Row Labels for Bottom */}
                <g fill="#64748b" fontSize="10" fontWeight="600" textAnchor="start">
                  <text x="5" y={svg2Height - s2PadBot + 25}>Wind</text>
                  <text x="5" y={svg2Height - s2PadBot + 50}>Time</text>
                </g>

                {points.map((p, i) => {
                  const hour = p.time.getHours();
                  const ampm = hour >= 12 ? 'PM' : 'AM';
                  const displayHour = hour % 12 === 0 ? 12 : hour % 12;
                  return (
                    <g key={i}>
                      {/* Temp Point (No text to avoid clutter, axis provides value) */}
                      <circle cx={p.x} cy={p.y2_temp} r="4" fill="#ffffff" stroke="#f97316" strokeWidth="2" />
                      
                      {/* Humidity Point */}
                      <circle cx={p.x} cy={p.y2_hum} r="4" fill="#ffffff" stroke="#10b981" strokeWidth="2" />
                      
                      {/* Wind Data */}
                      <g transform={`translate(${p.x}, ${svg2Height - s2PadBot + 25})`}>
                        <g transform={`translate(-4, -15) rotate(${p.wind_dir}, 4, 4)`}>
                          <path d="M4 0 L4 8 M1 5 L4 8 L7 5" fill="none" stroke="#4b5563" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </g>
                        <text x="0" y="4" textAnchor="middle" fill="#4b5563" fontSize="10" fontWeight="600">{p.wind_kmh} km/h</text>
                      </g>
                      
                      {/* Time Label */}
                      <text x={p.x} y={svg2Height - s2PadBot + 50} textAnchor="middle" fill="#475569" fontSize="10" fontWeight="600">{displayHour} {ampm}</text>
                    </g>
                  )
                })}

                {/* Invisible hover areas */}
                {points.map((p, i) => (
                  <rect
                    key={`hover-${i}`}
                    x={p.x - pointSpacing / 2}
                    y={0}
                    width={pointSpacing}
                    height={svg2Height}
                    fill="transparent"
                    onMouseEnter={() => setHoveredEnvIndex(i)}
                    onMouseLeave={() => setHoveredEnvIndex(null)}
                    style={{ cursor: "crosshair" }}
                  />
                ))}

                {/* Draw Tooltip if hovered */}
                {hoveredEnvIndex !== null && (() => {
                  const p = points[hoveredEnvIndex];
                  const tipY = Math.min(p.y2_temp, p.y2_hum);
                  return (
                    <g pointerEvents="none">
                      {/* Vertical highlight line */}
                      <line x1={p.x} y1={s2PadTop} x2={p.x} y2={svg2Height - s2PadBot} stroke="#9ca3af" strokeWidth="1.5" strokeDasharray="4 4" />
                      
                      {/* Tooltip Box */}
                      <rect x={p.x - 42} y={tipY - 44} width="84" height="36" rx="4" fill="#ffffff" stroke="#e5e7eb" strokeWidth="1" style={{ filter: "drop-shadow(0px 4px 6px rgba(0,0,0,0.1))" }} />
                      
                      {/* Temp Text */}
                      <text x={p.x} y={tipY - 28} textAnchor="middle" fill="#c2410c" fontSize="11" fontWeight="700">{Math.round(p.temp)}°C</text>
                      
                      {/* Hum Text */}
                      <text x={p.x} y={tipY - 14} textAnchor="middle" fill="#047857" fontSize="11" fontWeight="700">{p.humidity_pct}% Humidity</text>
                    </g>
                  );
                })()}
              </svg>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
