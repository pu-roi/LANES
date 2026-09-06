"use client";

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Map, Rss, MessageSquarePlus, TrendingUp, Flame, Heart, Plus, ChevronDown, Pin } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { savedPlacesApi } from '@/features/profile/savedPlacesApi';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { EmergencyHotlinesCard } from './components/EmergencyHotlinesCard';

export function LeftSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const { isAuthenticated } = useAuth();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    if (isDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen]);

  const { data: savedPlaces, isLoading } = useQuery({
    queryKey: ['saved-places', isAuthenticated],
    queryFn: savedPlacesApi.getSavedPlaces,
    enabled: isAuthenticated,
  });

  const sortedPlaces = savedPlaces ? [...savedPlaces].sort((a, b) => {
    const orderA = a.pin_order ?? 999;
    const orderB = b.pin_order ?? 999;
    if (orderA === orderB) return 0;
    return orderA - orderB;
  }) : [];
  
  const visiblePlaces = sortedPlaces.slice(0, 3);
  const hiddenPlaces = sortedPlaces.slice(3);

  const navItems = [
    { name: 'Community Feed', href: '/feed', icon: Rss },
    { name: 'Live Map', href: '/map', icon: Map },
    { name: 'Submit Report', href: '/map?action=report', icon: MessageSquarePlus },
  ];

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col h-[calc(100vh-86px)] sticky top-[86px] bg-transparent overflow-y-auto hidden md:flex px-4 border-r border-gray-200 custom-scrollbar [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-transparent hover:[&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-thumb]:rounded-full transition-colors duration-200">
      <div className="flex-1 py-6 space-y-6">
        {/* Navigation */}
        <div className="space-y-1">
          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Navigation</h3>
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors font-medium text-sm ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                {item.name}
              </Link>
            );
          })}
        </div>

        {/* Trending Locations */}
        <div className="space-y-1">
          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            Trending Hotspots
          </h3>
          <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group">
            <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-500" /> Espana Blvd</span>
            <span className="text-xs text-gray-400 group-hover:text-gray-600">12</span>
          </div>
          <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group">
            <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-500" /> Taft Ave</span>
            <span className="text-xs text-gray-400 group-hover:text-gray-600">8</span>
          </div>
          <div className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex justify-between items-center group">
            <span className="flex items-center gap-2"><Flame className="w-4 h-4 text-orange-400" /> EDSA-Kamuning</span>
            <span className="text-xs text-gray-400 group-hover:text-gray-600">5</span>
          </div>
        </div>

        {/* Saved Places */}
        <div className="space-y-1 relative" ref={dropdownRef}>
          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
            <Heart className="w-3.5 h-3.5" />
            Saved Places
          </h3>
          
          {isLoading ? (
            <div className="px-3 py-2 animate-pulse flex flex-col gap-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ) : (
            <>
              {visiblePlaces.length > 0 ? (
                visiblePlaces.map((place) => (
                  <div
                    key={place.id}
                    onClick={() => {
                      router.push(`/map?lat=${place.latitude}&lng=${place.longitude}&zoom=16&panel=saveplace&tab=list`);
                    }}
                    className={`px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex items-center justify-between select-none caret-transparent ${place.pin_order !== null ? 'bg-amber-50/30' : ''}`}
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-6 h-6 flex items-center justify-center bg-blue-100 rounded-full text-xs shrink-0 select-none pointer-events-none">
                        {place.icon || "📍"}
                      </div>
                      <span className="truncate select-none pointer-events-none">{place.name}</span>
                    </div>
                    {place.pin_order !== null && <Pin className="w-3 h-3 text-amber-500 fill-amber-500 shrink-0 ml-2" />}
                  </div>
                ))
              ) : (
                <div className="px-3 py-2 text-sm text-gray-500 select-none">
                  <p>No saved places yet.</p>
                </div>
              )}

              {hiddenPlaces.length > 0 && (
                <>
                  {isDropdownOpen && (
                    <div className="space-y-1 max-h-48 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                      {hiddenPlaces.map((place) => (
                        <div
                          key={place.id}
                          onClick={() => {
                            setIsDropdownOpen(false);
                            router.push(`/map?lat=${place.latitude}&lng=${place.longitude}&zoom=16&panel=saveplace&tab=list`);
                          }}
                          className={`px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl cursor-pointer transition-colors flex items-center justify-between select-none caret-transparent ${place.pin_order !== null ? 'bg-amber-50/30' : ''}`}
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <div className="w-6 h-6 flex items-center justify-center bg-blue-100 rounded-full text-xs shrink-0 select-none pointer-events-none">
                              {place.icon || "📍"}
                            </div>
                            <span className="truncate select-none pointer-events-none">{place.name}</span>
                          </div>
                          {place.pin_order !== null && <Pin className="w-3 h-3 text-amber-500 fill-amber-500 shrink-0 ml-2" />}
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className="flex items-center justify-between w-full px-3 text-xs font-medium text-gray-500 hover:text-gray-700 py-1.5 transition-colors"
                  >
                    {isDropdownOpen ? 'Show less' : `View ${hiddenPlaces.length} more`}
                    <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>
                </>
              )}

              <div className="px-3 pt-2 pb-1">
                <button
                  onClick={() => router.push('/map?panel=saveplace&tab=add')}
                  className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium text-xs px-2 py-1.5 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors w-full justify-center select-none"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add a Place
                </button>
              </div>
            </>
          )}
        </div>

        <EmergencyHotlinesCard />
      </div>
    </aside>
  );
}
