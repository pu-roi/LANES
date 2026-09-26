"use client";

import { useId } from "react";
import { motion } from "framer-motion";
import { FLOOD_DEPTH_SPECS, FLOOD_DEPTH_OPTIONS } from "@/lib/floodDepth";

/* ─── SVG Coordinate System ───────────────────────────
 *  viewBox : 0 0 390 460
 *  Person  : crown y=45, flat shoes planted on ground y=415 → 370 SVG units = 165 cm
 *  Scale   : 370 / 165 ≈ 2.2424 SVG-units / cm
 *  Ruler   : x ≈ 52 (left edge with bold, clear 10-11.5px labels)
 *  Person  : centered at x = 168 (bounds: x=109.0 to 227.0, natural healthy bulky commuter build)
 *  Bubble  : x ≈ 260 to 380 (large, prominent 12.5px/11px card clear of body)
 * ──────────────────────────────────────────────────── */
const SVG_W = 390;
const SVG_H = 460;
const PERSON_TOP = 45;
const GROUND_Y = 415;
const PERSON_H = GROUND_Y - PERSON_TOP; // 370
const REF_CM = 165;
const SCALE = PERSON_H / REF_CM; // ≈ 2.2424 SVG-units / cm
const RULER_X = 52;
const BUBBLE_X = 260;
const BUBBLE_W = 120;
const BUBBLE_H = 44;

/* Natural, healthy, comfortably bulky commuter standing silhouette with flat soles firmly planted on the ground */
const MODERN_PERSON_PATH =
  "M 168.0,45.0 C 178.0,45.0 187.0,52.0 187.5,64.0 C 188.0,76.0 183.0,88.0 177.0,92.5 C 176.5,95.0 178.0,99.0 180.0,103.5 C 185.0,106.0 202.0,109.0 214.0,116.0 C 220.0,120.0 224.0,138.0 225.5,158.0 C 227.0,178.0 226.0,200.0 224.0,220.0 C 222.5,235.0 221.0,248.0 219.0,260.0 C 218.0,267.0 216.5,273.0 214.5,276.5 C 213.0,279.0 210.0,279.0 208.5,276.0 C 207.0,272.5 207.5,264.0 208.5,256.0 C 209.5,244.0 210.5,226.0 210.0,208.0 C 209.0,190.0 207.5,170.0 205.0,150.0 C 203.5,138.0 201.0,129.0 198.0,123.0 C 197.0,133.0 196.0,150.0 195.5,166.0 C 195.0,182.0 194.0,198.0 194.0,214.0 C 194.0,225.0 195.5,235.0 197.5,243.0 C 199.0,253.0 198.0,273.0 196.5,296.0 C 195.0,316.0 194.0,340.0 193.0,364.0 C 192.0,380.0 191.0,392.0 190.0,399.0 C 193.0,401.5 198.0,406.0 204.0,408.5 C 210.0,411.0 214.0,413.0 214.0,415.0 L 180.0,415.0 C 178.0,414.0 177.5,408.0 178.5,402.0 C 179.0,399.0 180.5,399.0 180.5,399.0 C 180.0,380.0 179.0,355.0 178.0,330.0 C 177.0,305.0 176.0,280.0 175.0,255.0 C 174.0,242.0 171.0,231.0 168.0,230.0 C 165.0,231.0 162.0,242.0 161.0,255.0 C 160.0,280.0 159.0,305.0 158.0,330.0 C 157.0,355.0 156.0,380.0 155.5,399.0 C 157.0,399.0 158.5,408.0 158.0,414.0 L 156.0,415.0 L 122.0,415.0 C 122.0,413.0 126.0,411.0 132.0,408.5 C 138.0,406.0 143.0,401.5 146.0,399.0 C 145.0,392.0 144.0,380.0 143.0,364.0 C 142.0,340.0 141.0,316.0 139.5,296.0 C 138.0,273.0 137.0,253.0 138.5,243.0 C 140.5,235.0 142.0,225.0 142.0,214.0 C 142.0,198.0 141.0,182.0 140.5,166.0 C 140.0,150.0 139.0,133.0 138.0,123.0 C 135.0,129.0 132.5,138.0 131.0,150.0 C 128.5,170.0 127.0,190.0 126.0,208.0 C 125.5,226.0 126.5,244.0 127.5,256.0 C 128.5,264.0 129.0,272.5 127.5,276.0 C 126.0,279.0 123.0,279.0 121.5,276.5 C 119.5,273.0 118.0,267.0 117.0,260.0 C 115.0,248.0 113.5,235.0 112.0,220.0 C 110.0,200.0 109.0,178.0 110.5,158.0 C 112.0,138.0 116.0,120.0 122.0,116.0 C 134.0,109.0 151.0,106.0 156.0,103.5 C 158.0,99.0 159.5,95.0 159.0,92.5 C 153.0,88.0 148.0,76.0 148.5,64.0 C 149.0,52.0 158.0,45.0 168.0,45.0 z";

/* Wavy water-surface path (coords relative to the motion group) */
const WAVE =
  "M 0,0 Q 25,-4 50,0 Q 75,4 100,0 Q 125,-4 150,0 Q 175,4 200,0 " +
  "Q 225,-4 250,0 Q 275,4 300,0 Q 325,-4 350,0 Q 375,4 400,0 " +
  "L 400,500 L 0,500 Z";

/* Severity → fill colour */
const COLORS: Record<string, string> = {
  low: "#84cc16",
  medium: "#f59e0b",
  high: "#f97316",
  extreme: "#dc2626",
};

const SPRING = { type: "spring" as const, stiffness: 120, damping: 18 };

function depthY(cm: number) {
  return GROUND_Y - cm * SCALE;
}

/* ─── Component ─────────────────────────────────────── */
interface Props {
  hoveredDepth: string | null;
}

export function FloodGaugeSilhouette({ hoveredDepth }: Props) {
  const uid = useId();
  const clipId = `pc${uid}`;

  const spec = hoveredDepth
    ? (FLOOD_DEPTH_SPECS[hoveredDepth] ?? null)
    : null;

  /* Push water below the person when idle so nothing is visible */
  const waterY = spec ? depthY(spec.centimeters) : GROUND_Y + 20;
  const color = spec ? (COLORS[spec.severity] ?? "#3b82f6") : "#3b82f6";

  return (
    <div className="flex flex-col items-center w-full">
      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        className="w-full max-h-[340px] lg:max-h-[440px] select-none drop-shadow-sm"
        role="img"
        aria-label="Flood depth gauge — 165 cm reference person"
      >
        {/* ── Defs ── */}
        <defs>
          <clipPath id={clipId}>
            <path d={MODERN_PERSON_PATH} />
          </clipPath>
          <linearGradient id={`grad-${uid}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.72} />
            <stop offset="100%" stopColor={color} stopOpacity={0.9} />
          </linearGradient>
          <filter id={`badge-shadow-${uid}`} x="-10%" y="-10%" width="130%" height="130%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000000" floodOpacity="0.08" />
          </filter>
        </defs>

        {/* ── Ruler Axis ── */}
        <line
          x1={RULER_X}
          y1={PERSON_TOP - 8}
          x2={RULER_X}
          y2={GROUND_Y}
          stroke="#cbd5e1"
          strokeWidth={1.5}
        />
        {/* Ruler Top Label */}
        <text
          x={RULER_X}
          y={PERSON_TOP - 16}
          textAnchor="middle"
          fontSize={8.5}
          fontWeight={700}
          fill="#94a3b8"
          letterSpacing="0.05em"
        >
          CM
        </text>

        {/* Ground tick */}
        <line
          x1={RULER_X - 6}
          y1={GROUND_Y}
          x2={RULER_X + 6}
          y2={GROUND_Y}
          stroke="#94a3b8"
          strokeWidth={1.5}
        />
        <text
          x={RULER_X - 10}
          y={GROUND_Y + 3.5}
          textAnchor="end"
          fontSize={10}
          fontWeight={500}
          fill="#64748b"
        >
          0
        </text>

        {/* Top tick (165 cm) */}
        <line
          x1={RULER_X - 6}
          y1={PERSON_TOP}
          x2={RULER_X + 6}
          y2={PERSON_TOP}
          stroke="#94a3b8"
          strokeWidth={1.5}
        />
        <text
          x={RULER_X - 10}
          y={PERSON_TOP + 3.5}
          textAnchor="end"
          fontSize={10.5}
          fontWeight={600}
          fill="#475569"
        >
          165
        </text>

        {/* Depth ticks & labels */}
        {FLOOD_DEPTH_OPTIONS.map((s) => {
          const y = depthY(s.centimeters);
          const active = hoveredDepth === s.id;
          return (
            <g key={s.id}>
              <line
                x1={active ? RULER_X - 8 : RULER_X - 5}
                y1={y}
                x2={active ? RULER_X + 9 : RULER_X + 5}
                y2={y}
                stroke={active ? color : "#cbd5e1"}
                strokeWidth={active ? 2 : 1}
              />
              <text
                x={RULER_X - 10}
                y={y + 3.5}
                textAnchor="end"
                fontSize={active ? 11.5 : 9.5}
                fill={active ? color : "#64748b"}
                fontWeight={active ? 800 : 500}
              >
                {Math.round(s.centimeters)}
              </text>
            </g>
          );
        })}

        {/* ── Ground baseline (solid grounded floor) ── */}
        <line
          x1={RULER_X}
          y1={GROUND_Y}
          x2={280}
          y2={GROUND_Y}
          stroke="#cbd5e1"
          strokeWidth={1.5}
          strokeDasharray="4 3"
        />

        {/* ── Person silhouette (natural, bulky standing commuter) ── */}
        <path
          d={MODERN_PERSON_PATH}
          fill="#e2e8f0"
          stroke="#cbd5e1"
          strokeWidth={1}
        />

        {/* ── Animated water fill (clipped to silhouette contour) ── */}
        <g clipPath={`url(#${clipId})`}>
          <motion.g
            initial={{ y: GROUND_Y + 20 }}
            animate={{ y: waterY }}
            transition={SPRING}
          >
            <path d={WAVE} fill={`url(#grad-${uid})`} opacity={0.75} />
          </motion.g>
        </g>

        {/* ── Dashed reference line extending from ruler to callout badge ── */}
        <motion.line
          x1={RULER_X}
          x2={BUBBLE_X}
          y1={0}
          y2={0}
          initial={{ y: GROUND_Y + 20, opacity: 0 }}
          animate={{ y: waterY, opacity: spec ? 0.85 : 0 }}
          transition={{ y: SPRING, opacity: { duration: 0.2 } }}
          stroke={color}
          strokeWidth={1.75}
          strokeDasharray="5 3"
        />

        {/* ── Pointer dot connecting water line to the badge ── */}
        <motion.circle
          cx={BUBBLE_X}
          cy={0}
          r={3.5}
          initial={{ y: GROUND_Y + 20, opacity: 0 }}
          animate={{ y: waterY, opacity: spec ? 1 : 0 }}
          transition={{ y: SPRING, opacity: { duration: 0.2 } }}
          fill={color}
        />

        {/* ── Depth Callout Badge (Large, Clear & Readable) ── */}
        <motion.g
          initial={{ y: GROUND_Y + 20, opacity: 0 }}
          animate={{ y: waterY, opacity: spec ? 1 : 0 }}
          transition={{ y: SPRING, opacity: { duration: 0.2 } }}
        >
          {/* Card background with shadow */}
          <rect
            x={BUBBLE_X}
            y={-BUBBLE_H / 2}
            width={BUBBLE_W}
            height={BUBBLE_H}
            rx={8}
            fill="white"
            stroke={color}
            strokeWidth={1.75}
            filter={`url(#badge-shadow-${uid})`}
          />
          {/* Severity category bar on left edge of badge */}
          <rect
            x={BUBBLE_X}
            y={-BUBBLE_H / 2}
            width={4}
            height={BUBBLE_H}
            rx={2}
            fill={color}
          />
          {/* Label Title (e.g. "Tires", "Knee", "Neck & Above") */}
          <text
            x={BUBBLE_X + BUBBLE_W / 2 + 2}
            y={-4}
            textAnchor="middle"
            fontSize={12.5}
            fontWeight={700}
            fill={color}
          >
            {spec?.label ?? ""}
          </text>
          {/* Depth Measurement (e.g. "26\" (0.66m)") */}
          <text
            x={BUBBLE_X + BUBBLE_W / 2 + 2}
            y={12}
            textAnchor="middle"
            fontSize={11}
            fontWeight={600}
            fill="#1e293b"
          >
            {spec?.formatted ?? ""}
          </text>
        </motion.g>
      </svg>

      {/* Idle prompt */}
      {!spec && (
        <p className="text-xs text-slate-400 text-center mt-2 font-medium">
          <span className="hidden lg:inline">Hover</span>
          <span className="lg:hidden">Tap</span>
          {" a depth level to see the flood line"}
        </p>
      )}

      {/* Disclaimer badge */}
      <div className="mt-2.5 text-center">
        <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-500 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-xs">
          📏 165 cm (5′5″) reference · DOST-FNRI standard
        </span>
      </div>
    </div>
  );
}
