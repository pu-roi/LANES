'use client';

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  X, Phone, Search, Globe, Building2, MapPin, Loader2,
} from 'lucide-react';
import { Tabs, TabContentPanel } from '@/shared/ui';
import { useFullHotlines, type HotlineGroup } from '../useHotlines';

type TabId = 'national' | 'pasig_city' | 'pasig_barangay';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

// ── Agency card: name as header, flat list of tappable numbers ─────────────
function AgencyCard({ group, accentColor = 'red' }: { group: HotlineGroup; accentColor?: 'red' | 'blue' }) {
  const colors = {
    red: {
      icon: 'bg-red-50 text-red-500',
      number: 'hover:bg-red-50 hover:text-red-700',
      divider: 'divide-red-50',
      pill: 'bg-red-50 text-red-600',
    },
    blue: {
      icon: 'bg-blue-50 text-blue-500',
      number: 'hover:bg-blue-50 hover:text-blue-700',
      divider: 'divide-blue-50',
      pill: 'bg-blue-50 text-blue-600',
    },
  }[accentColor];

  return (
    <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
      {/* Agency header */}
      <div className="px-4 py-3 bg-gray-50/80 border-b border-gray-100 flex items-center gap-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${colors.icon}`}>
          <Phone className="w-4 h-4" />
        </div>
        <span className="text-sm font-bold text-gray-800 leading-tight">{group.name}</span>
      </div>

      {/* All numbers — flat, no accordion */}
      <div className={`divide-y ${colors.divider}`}>
        {group.numbers.map((num, i) => (
          <a
            key={i}
            href={`tel:${num.raw}`}
            className={`flex items-center justify-between px-4 py-3 transition-colors group ${colors.number}`}
          >
            <span className="text-sm font-medium text-gray-700 group-hover:text-inherit transition-colors leading-snug">
              {num.display}
            </span>
            <span className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full flex-shrink-0 ml-3 ${colors.pill}`}>
              <Phone className="w-3 h-3" />
              Call
            </span>
          </a>
        ))}
      </div>
    </div>
  );
}

// ── Barangay row: name + numbers inline, sticky letter dividers ────────────
function BarangaySection({ groups, search }: { groups: HotlineGroup[]; search: string }) {
  const filtered = groups.filter(g =>
    g.name.toLowerCase().includes(search.toLowerCase())
  );

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <MapPin className="w-10 h-10 text-gray-200 mb-3" />
        <p className="text-sm font-semibold text-gray-400">No barangay found</p>
        <p className="text-xs text-gray-300 mt-1">Try a different search term</p>
      </div>
    );
  }

  // Group alphabetically
  const grouped: Record<string, HotlineGroup[]> = {};
  for (const g of filtered) {
    const letter = g.name[0].toUpperCase();
    if (!grouped[letter]) grouped[letter] = [];
    grouped[letter].push(g);
  }
  const letters = Object.keys(grouped).sort();

  return (
    <div className="space-y-6">
      {letters.map(letter => (
        <div key={letter}>
          {/* Sticky letter divider */}
          <div className="sticky top-0 bg-white/90 backdrop-blur-sm px-4 py-1.5 border-b border-gray-100 z-10">
            <span className="text-xs font-extrabold text-gray-400 uppercase tracking-widest">{letter}</span>
          </div>

          <div className="divide-y divide-gray-50">
            {grouped[letter].map((brgy, i) => (
              <div key={i} className="px-4 py-3">
                {/* Barangay name */}
                <p className="text-sm font-bold text-gray-800 mb-2 flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  Brgy. {brgy.name}
                </p>
                {/* Numbers as inline pills */}
                <div className="flex flex-wrap gap-2 pl-5">
                  {brgy.numbers.map((num, ni) => (
                    <a
                      key={ni}
                      href={`tel:${num.raw}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-full transition-colors"
                    >
                      <Phone className="w-3 h-3" />
                      {num.display}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main Modal ────────────────────────────────────────────────────────────────
export function EmergencyDirectoryModal({ isOpen, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>('national');
  const [tabDir, setTabDir] = useState(1);
  const [search, setSearch] = useState('');
  const prevTab = useRef<TabId>('national');
  const searchRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useFullHotlines(isOpen);

  const TAB_ORDER: TabId[] = ['national', 'pasig_city', 'pasig_barangay'];

  const handleTabChange = (id: TabId) => {
    const prev = TAB_ORDER.indexOf(prevTab.current);
    const next = TAB_ORDER.indexOf(id);
    setTabDir(next > prev ? 1 : -1);
    prevTab.current = id;
    setActiveTab(id);
    setSearch('');
  };

  useEffect(() => {
    if (activeTab === 'pasig_barangay' && isOpen) {
      setTimeout(() => searchRef.current?.focus(), 200);
    }
  }, [activeTab, isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (isOpen) window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  const tabs = [
    { id: 'national' as TabId, label: 'National', icon: Globe, badge: data?.national.length },
    { id: 'pasig_city' as TabId, label: 'Pasig City', icon: Building2, badge: data?.pasig_city.length },
    { id: 'pasig_barangay' as TabId, label: 'Barangays', icon: MapPin, badge: data?.pasig_barangay.length },
  ];

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-end sm:items-center justify-center p-0 sm:p-6">
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Dialog — tall on desktop, sheet on mobile */}
          <motion.div
            key="dialog"
            initial={{ opacity: 0, y: 48, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 48, scale: 0.97 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full sm:max-w-2xl bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl flex flex-col overflow-hidden"
            style={{ maxHeight: 'min(88vh, 680px)' }}
          >
            {/* ── Header ── */}
            <div className="flex items-start justify-between px-6 pt-6 pb-4 flex-shrink-0">
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 tracking-tight">Emergency Directory</h2>
                <p className="text-sm text-gray-400 mt-0.5">Tap any number to call directly</p>
              </div>
              <button
                onClick={onClose}
                aria-label="Close"
                className="w-9 h-9 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 transition-colors flex-shrink-0"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>

            {/* ── Tabs (shared Tabs component — underline variant) ── */}
            <div className="px-6 flex-shrink-0">
              <Tabs
                tabs={tabs}
                activeTab={activeTab}
                onChange={handleTabChange}
                variant="underline"
                fullWidth
                layoutId="emergency-dir-tabs"

              />
            </div>

            {/* ── Divider ── */}
            <div className="border-t border-gray-100 flex-shrink-0" />

            {/* ── Scrollable content ── */}
            <div className="overflow-y-auto flex-1 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <Loader2 className="w-7 h-7 text-red-400 animate-spin mb-3" />
                  <p className="text-sm text-gray-400 font-medium">Loading directory…</p>
                </div>
              ) : (
                <TabContentPanel tabKey={activeTab} direction={tabDir}>
                  {/* ── National tab ── */}
                  {activeTab === 'national' && (
                    <div className="p-6 space-y-4">
                      {(data?.national ?? []).length > 0 ? (
                        (data?.national ?? []).map((g, i) => (
                          <AgencyCard key={i} group={g} accentColor="red" />
                        ))
                      ) : (
                        <EmptyState icon={Globe} message="National hotlines unavailable." />
                      )}
                    </div>
                  )}

                  {/* ── Pasig City tab ── */}
                  {activeTab === 'pasig_city' && (
                    <div className="p-6 space-y-4">
                      {(data?.pasig_city ?? []).length > 0 ? (
                        (data?.pasig_city ?? []).map((g, i) => (
                          <AgencyCard key={i} group={g} accentColor="red" />
                        ))
                      ) : (
                        <EmptyState icon={Building2} message="Pasig City hotlines unavailable." />
                      )}
                    </div>
                  )}

                  {/* ── Barangays tab ── */}
                  {activeTab === 'pasig_barangay' && (
                    <div>
                      {/* Search bar lives here, inside the scroll area */}
                      <div className="sticky top-0 bg-white/95 backdrop-blur-sm px-6 py-3 border-b border-gray-100 z-20">
                        <div className="relative">
                          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                          <input
                            ref={searchRef}
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Search barangay name…"
                            className="w-full pl-10 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl bg-gray-50 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                          />
                        </div>
                      </div>
                      <BarangaySection
                        groups={data?.pasig_barangay ?? []}
                        search={search}
                      />
                    </div>
                  )}
                </TabContentPanel>
              )}
            </div>

            {/* Safe-area padding for mobile notch */}
            <div className="flex-shrink-0 sm:hidden pb-[env(safe-area-inset-bottom)]" />
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );

  if (typeof document === 'undefined') return null;
  return createPortal(modalContent, document.body);
}

function EmptyState({ icon: Icon, message }: { icon: React.ComponentType<{ className?: string }>; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon className="w-10 h-10 text-gray-200 mb-3" />
      <p className="text-sm font-semibold text-gray-400">{message}</p>
    </div>
  );
}
