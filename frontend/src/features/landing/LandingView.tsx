"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MapPin, ArrowRight, MousePointerClick, TrendingUp, Download } from "lucide-react";

import { useInstallPrompt } from "@/hooks/useInstallPrompt";

import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";

import type { LocationSuggestion } from "@/features/geocoding/types";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { WeatherWidget } from "./WeatherWidget";
import { HomeStats } from "./HomeStats";
import { ForecastChart } from "./ForecastChart";
import { FloodLegend } from "./FloodLegend";

export default function LandingView() {
  const router = useRouter();
  const { isInstallable, triggerInstall } = useInstallPrompt();

  const [locationLabel, setLocationLabel] = useState("");
  const [typedText, setTypedText] = useState("");
  const fullText = "Learn more about LANES";

  useEffect(() => {
    let i = 0;
    let pauseCount = 0;
    const intervalId = setInterval(() => {
      if (i <= fullText.length) {
        setTypedText(fullText.substring(0, i));
        i++;
      } else {
        pauseCount++;
        if (pauseCount > 30) {
          i = 0;
          pauseCount = 0;
        }
      }
    }, 75);
    return () => clearInterval(intervalId);
  }, []);

  const [selectedCoords, setSelectedCoords] = useState<[number, number] | null>(null);
  const [pointType, setPointType] = useState<"start" | "end">("start");
  const [isLoading, setIsLoading] = useState(false);

  const handleUseCurrentLocation = async () => {
    setIsLoading(true);
    try {
      const coords = await getCurrentLocation();
      setSelectedCoords(coords);
      setLocationLabel("Current Location");
    } catch (err: any) {
      alert(err.message || "Unable to retrieve your location");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocationSelect = (suggestion: LocationSuggestion) => {
    setSelectedCoords([suggestion.lng, suggestion.lat]);
    setLocationLabel(suggestion.label);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCoords) {
      return alert("Please select a location from the suggestions or use your current location");
    }

    const [lng, lat] = selectedCoords;
    const params = new URLSearchParams({
      location: `${lng},${lat}`,
      type: pointType,
      label: locationLabel,
    });
    router.push(`/map?${params.toString()}`);
  };

  const scrollToLegend = (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById('flood-legend-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="flex-1 bg-blue-50 flex flex-col min-h-screen relative z-0">
      
      {/* Global Parallax Background */}
      <div 
        className="fixed inset-0 -z-10 opacity-[0.15] pointer-events-none"
        style={{
          backgroundImage: "url('data:image/svg+xml,%3Csvg width=\"60\" height=\"60\" viewBox=\"0 0 60 60\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cg fill=\"none\" fill-rule=\"evenodd\"%3E%3Cg fill=\"%232563eb\" fill-opacity=\"1\"%3E%3Cpath d=\"M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')"
        }}
      />

      {/* ── ABOVE THE FOLD WRAPPER (Sections 1 & 2) ── */}
      <div className="flex flex-col min-h-[100svh] w-full">
        
        {/* ── SECTION 1: Hero & Journey ─────────────────────────────────────────────── */}
        <section className="relative w-full flex-grow flex flex-col justify-center pt-6 pb-[100px] overflow-hidden bg-transparent">
          

          <div className="relative z-10 max-w-7xl w-full mx-auto px-6 md:px-12 flex flex-col lg:flex-row items-center lg:items-start gap-8 lg:gap-12">
            
            {/* Left column: Hero */}
            <div className="flex-1 space-y-5 text-center lg:text-left flex flex-col items-center lg:items-start pt-2">
              <h1 className="text-4xl md:text-5xl lg:text-5xl font-extrabold text-gray-900 tracking-tight leading-[1.15]">
                Navigate Safely <br className="hidden lg:block" /> <span className="text-blue-600">During Floods</span>
              </h1>

              <p className="text-base text-gray-600 max-w-lg leading-relaxed">
                LANES helps commuters and drivers find safe, flood-free
                routes in real-time. Provide your location to view the safest
                path to your destination.{" "}
                <a
                  href="/about"
                  className="text-blue-600 font-semibold hover:underline inline-flex items-center whitespace-nowrap"
                  aria-label="Learn more about LANES"
                >
                  {typedText}
                  <ArrowRight className="inline-block w-3.5 h-3.5 ml-1" />
                </a>
              </p>

              <div className="flex flex-col gap-3 pt-2 w-full lg:max-w-md items-center lg:items-start">
                <a
                  href="#flood-legend-section"
                  onClick={scrollToLegend}
                  className="text-slate-500 font-medium hover:text-blue-600 hover:underline flex items-center transition-colors"
                  aria-label="View Vehicle Clearance Rules"
                >
                  <MousePointerClick className="inline-block w-4 h-4 mr-2" />
                  View Vehicle Clearance Rules
                </a>
                
                {isInstallable && (
                  <div className="flex flex-col sm:flex-row gap-3 mt-4 w-full justify-center lg:justify-start">
                    <Button
                      size="lg"
                      onClick={triggerInstall}
                      className="relative rounded-full shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all duration-300 hover:shadow-[0_0_25px_rgba(59,130,246,0.6)] group"
                    >
                      <Download className="relative w-5 h-5 mr-2 group-hover:translate-y-0.5 transition-transform" />
                      <span className="relative font-bold">Download LANES App</span>
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Right column: Start Your Journey card */}
            <div className="w-full lg:max-w-md">
              <Card className="w-full border border-slate-300 overflow-visible rounded-2xl bg-slate-100/95 backdrop-blur-xl shadow-md">
                <CardHeader className="text-center pb-2 pt-6">
                  <CardTitle className="text-xl font-bold text-gray-900">Start Your Journey</CardTitle>
                </CardHeader>

                <CardContent className="pb-6 px-6 sm:px-8">
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-gray-700">Where are you?</label>

                      <Button
                        type="button"
                        size="lg"
                        className="w-full rounded-xl bg-blue-100 text-blue-800 hover:bg-blue-200 border border-blue-300 font-bold shadow-sm"
                        onClick={handleUseCurrentLocation}
                        disabled={isLoading}
                      >
                        {isLoading ? (
                          "Getting location..."
                        ) : (
                          <>
                            <MapPin className="inline-block w-4 h-4 mr-2" />
                            Use My Current Location
                          </>
                        )}
                      </Button>

                      <div className="relative flex items-center py-1">
                        <div className="flex-grow border-t border-gray-100"></div>
                        <span className="flex-shrink-0 mx-4 text-gray-400 text-[10px] font-bold uppercase tracking-widest">or</span>
                        <div className="flex-grow border-t border-gray-100"></div>
                      </div>

                      <LocationAutocomplete
                        value={locationLabel}
                        onChange={(value) => {
                          setLocationLabel(value);
                          setSelectedCoords(null);
                        }}
                        onSelect={handleLocationSelect}
                        placeholder="Search street (e.g. C. Santos)"
                      />
                    </div>

                    <div className="space-y-3 pt-1">
                      <label className="text-sm font-semibold text-gray-700">
                        Is this location your:
                      </label>
                      <div className="flex gap-6">
                        <label className="flex items-center gap-2 cursor-pointer group">
                          <div className="relative flex items-center justify-center">
                            <input
                              type="radio"
                              name="pointType"
                              value="start"
                              checked={pointType === "start"}
                              onChange={() => setPointType("start")}
                              className="peer appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 cursor-pointer transition-colors"
                            />
                            <div className="absolute w-2 h-2 bg-blue-600 rounded-full scale-0 peer-checked:scale-100 transition-transform"></div>
                          </div>
                          <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors">Starting Point</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer group">
                          <div className="relative flex items-center justify-center">
                            <input
                              type="radio"
                              name="pointType"
                              value="end"
                              checked={pointType === "end"}
                              onChange={() => setPointType("end")}
                              className="peer appearance-none w-4 h-4 border-2 border-gray-300 rounded-full checked:border-blue-600 cursor-pointer transition-colors"
                            />
                            <div className="absolute w-2 h-2 bg-blue-600 rounded-full scale-0 peer-checked:scale-100 transition-transform"></div>
                          </div>
                          <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors">End Point</span>
                        </label>
                      </div>
                    </div>

                    <Button
                      type="submit"
                      size="lg"
                      className="w-full rounded-xl mt-2 shadow-sm font-bold"
                    >
                      Go to Map <ArrowRight className="inline-block w-4 h-4 ml-2" />
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      size="lg"
                      className="w-full bg-white hover:bg-blue-50 text-blue-600 border border-blue-200 rounded-xl shadow-sm font-bold mt-3"
                      onClick={() => router.push("/analytics")}
                    >
                      <TrendingUp className="inline-block w-5 h-5 mr-2" />
                      View Flood Analytics
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Wave Divider 1 */}
          <div className="absolute bottom-0 left-0 w-full overflow-hidden leading-none text-blue-600 bg-transparent shrink-0 flex z-10 translate-y-[1px]">
            <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="relative block w-[200%] h-[100px] fill-current animate-wave-top shrink-0">
              <path d="M0,30 C150,60 450,0 600,30 C750,60 1050,0 1200,30 C1350,60 1650,0 1800,30 C1950,60 2250,0 2400,30 V60 H0 Z"></path>
            </svg>
          </div>
        </section>

        {/* ── SECTION 2: Weather & Stats Bar ─────────────────────────────────────────────── */}
        <section className="w-full bg-blue-600 py-6 relative z-20 shrink-0">
          <div className="max-w-6xl mx-auto px-6">
            <div className="flex flex-col md:flex-row items-stretch justify-center gap-8 lg:gap-16">
              <div className="flex-1 max-w-sm mx-auto md:ml-auto md:mr-0 w-full">
                <WeatherWidget />
              </div>
              <div className="hidden md:block w-px bg-blue-400/50 my-2"></div>
              <div className="flex-1 max-w-sm mx-auto md:mr-auto md:ml-0 w-full">
                <HomeStats />
              </div>
            </div>
          </div>
        </section>

        {/* Wave Divider 2 */}
        <div className="w-full overflow-hidden leading-none -mb-px text-blue-600 bg-white shrink-0 flex">
          <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="relative block w-[200%] h-[100px] fill-current animate-wave-bottom shrink-0">
            <path d="M0,30 C150,0 450,60 600,30 C750,0 1050,60 1200,30 C1350,0 1650,60 1800,30 C1950,0 2250,60 2400,30 V0 H0 Z"></path>
          </svg>
        </div>
      </div>

      {/* ── SECTION 3: Weather Forecast ───────────────────────── */}
      <section className="w-full bg-white py-12">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Weather Forecast</h2>
            <p className="text-gray-500 mt-1 text-sm">
              12-hour localized forecast with rain probability.
            </p>
          </div>
          <div className="w-full">
            <ForecastChart />
          </div>
        </div>
      </section>

      {/* ── SECTION 4: Flood Severity Legend ───────────────────────── */}
      <section className="relative w-full overflow-hidden bg-transparent pt-24 pb-12 flex-grow" id="flood-legend-section">
        {/* Static Wave Divider */}
        <div className="absolute top-0 left-0 w-full overflow-hidden leading-none text-white z-20">
          <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="relative block w-full h-[100px] fill-current">
            <path d="M0,30 C150,0 450,60 600,30 C750,0 1050,60 1200,30 C1350,0 1650,60 1800,30 C1950,0 2250,60 2400,30 V0 H0 Z"></path>
          </svg>
        </div>
        

        <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Vehicle Clearance Rules</h2>
            <p className="text-gray-500 mt-1 text-sm">
              Understand which vehicles can safely pass through specific flood depths.
            </p>
          </div>
          <div className="w-full">
            <FloodLegend />
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="bg-white border-t border-gray-100 py-10 mt-auto">
        <div className="max-w-7xl mx-auto px-6 md:px-12 flex flex-col md:flex-row justify-between items-center text-sm text-gray-500 gap-4">
          <p className="font-medium">&copy; {new Date().getFullYear()} LANES Project. All rights reserved.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-blue-600 transition-colors font-medium">Privacy Policy</a>
            <a href="#" className="hover:text-blue-600 transition-colors font-medium">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
