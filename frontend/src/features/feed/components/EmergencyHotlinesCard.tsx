'use client';

import React, { useState } from 'react';
import { Phone, ChevronDown, ExternalLink } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { useHotlines } from '../useHotlines';
import type { HotlineGroup } from '../useHotlines';
import { EmergencyDirectoryModal } from './EmergencyDirectoryModal';

// Config: which agencies to show and their override short number (null = use first from API, false = no badge)
const PRIORITY_HOTLINES: { match: string; label: string; shortNumber: string | false }[] = [
  { match: 'National Emergency Hotline', label: 'National Emergency', shortNumber: '911' },
  { match: 'NDRRMC', label: 'NDRRMC', shortNumber: false },
  { match: 'Red Cross', label: 'Philippine Red Cross', shortNumber: '143' },
];

function HotlineRow({ group }: { group: HotlineGroup }) {
  const [open, setOpen] = useState(false);

  const priority = PRIORITY_HOTLINES.find(p => group.name.includes(p.match));
  const label = priority?.label ?? group.name;
  const shortNumber = priority?.shortNumber ?? false;
  const firstNumber = group.numbers[0];
  const hasMultiple = group.numbers.length > 1;
  const isExpandable = hasMultiple || (!shortNumber && group.numbers.length >= 1);

  return (
    <div>
      <button
        onClick={() => isExpandable && setOpen(o => !o)}
        className={`w-full flex items-center justify-between px-2 py-2 rounded-xl transition-all duration-150 text-left ${
          isExpandable ? 'cursor-pointer' : 'cursor-default'
        } ${open ? 'bg-red-50/80' : 'hover:bg-gray-50/80'}`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
            <Phone className="w-3 h-3 text-red-500" />
          </div>
          <span className="text-[13px] font-semibold text-gray-700 truncate">{label}</span>
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
          {shortNumber !== false ? (
            <a
              href={`tel:${firstNumber?.raw}`}
              onClick={e => e.stopPropagation()}
              className="text-xs font-mono font-bold text-red-600 bg-red-100 hover:bg-red-200 px-2.5 py-1 rounded-lg transition-colors"
            >
              {shortNumber}
            </a>
          ) : (
            <span className="text-[11px] text-red-400 font-medium">Numbers</span>
          )}
          {isExpandable && (
            <ChevronDown
              className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
            />
          )}
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && isExpandable && (
          <motion.div
            key="dropdown"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="mx-2 mb-1 rounded-xl bg-gradient-to-b from-red-50 to-rose-50/60 border border-red-100 divide-y divide-red-100/60">
              {group.numbers.map((num, nIdx) => (
                <a
                  key={nIdx}
                  href={`tel:${num.raw}`}
                  className="flex items-center justify-between px-3 py-2.5 hover:bg-red-100/60 transition-colors group first:rounded-t-xl last:rounded-b-xl"
                >
                  <span className="text-xs font-medium text-gray-700 group-hover:text-red-700 transition-colors leading-snug">
                    {num.display}
                  </span>
                  <ExternalLink className="w-3 h-3 text-red-300 group-hover:text-red-500 flex-shrink-0 ml-2 transition-colors" />
                </a>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function EmergencyHotlinesCard() {
  const { data: hotlines, isLoading } = useHotlines();
  const [modalOpen, setModalOpen] = useState(false);

  const sorted = PRIORITY_HOTLINES
    .map(p => hotlines?.find(g => g.name.includes(p.match)))
    .filter(Boolean) as HotlineGroup[];

  return (
    <>
      <div className="space-y-0.5">
        <h3 className="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Phone className="w-3 h-3" />
          Emergency Hotlines
        </h3>

        {isLoading ? (
          <div className="space-y-2 px-2 animate-pulse">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-9 bg-gray-100 rounded-xl w-full" />
            ))}
          </div>
        ) : sorted.length > 0 ? (
          sorted.map((group, idx) => <HotlineRow key={idx} group={group} />)
        ) : (
          <p className="px-2 text-xs text-gray-400">Hotlines unavailable.</p>
        )}

        {/* View All button */}
        <button
          onClick={() => setModalOpen(true)}
          className="w-full flex items-center justify-center gap-1.5 mt-2 px-3 py-2 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-colors border border-dashed border-red-200 hover:border-red-300"
        >
          <Phone className="w-3 h-3" />
          View All Hotlines
        </button>
      </div>

      <EmergencyDirectoryModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
