"use client";

import { useId } from "react";
import { motion } from "framer-motion";
import { FLOOD_DEPTH_SPECS, FLOOD_DEPTH_OPTIONS } from "@/lib/floodDepth";

/* ─── SVG Coordinate System ───────────────────────────
 *  viewBox : 0 0 320 450
 *  Person  : head-top y=40, feet y=400 → 360 SVG units = 165 cm
 *  Ruler   : x ≈ 5–42 (left edge)
 *  Person  : centred at x = 160
 * ──────────────────────────────────────────────────── */
const SVG_W = 320;
const SVG_H = 450;
const PERSON_TOP = 40;
const GROUND_Y = 400;
const PERSON_H = GROUND_Y - PERSON_TOP; // 360
const REF_CM = 165;
const SCALE = PERSON_H / REF_CM; // ≈ 2.182 SVG-units / cm
const RULER_X = 42;

/* Silhouette geometry (gender-neutral, bathroom-sign style) */
const HEAD = { cx: 160, cy: 57, r: 17 };

const TORSO =
  "M 152,74 L 127,92 Q 122,164 137,236 L 183,236 Q 198,164 193,92 L 168,74 Z";
const L_ARM = "M 127,96 L 113,100 L 104,232 L 114,236 L 123,104 Z";
const R_ARM = "M 193,96 L 207,100 L 216,232 L 206,236 L 197,104 Z";
const L_LEG = "M 137,235 L 154,235 L 150,400 L 126,400 Z";
const R_LEG = "M 166,235 L 183,235 L 194,400 L 170,400 Z";
const ALL_BODY = [TORSO, L_ARM, R_ARM, L_LEG, R_LEG];

/* Wavy water-surface path (coords relative to the motion group) */
const WAVE =
  "M 0,0 Q 20,-4 40,0 Q 60,4 80,0 Q 100,-4 120,0 Q 140,4 160,0 " +
  "Q 180,-4 200,0 Q 220,4 240,0 Q 260,-4 280,0 Q 300,4 320,0 " +
  "L 320,500 L 0,500 Z";

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
        className="w-full max-h-[300px] lg:max-h-[420px]"
        role="img"
        aria-label="Flood depth gauge — 165 cm reference person"
      >
        {/* ── Defs ── */}
        <defs>
          <clipPath id={clipId}>
            <circle cx={HEAD.cx} cy={HEAD.cy} r={HEAD.r} />
            {ALL_BODY.map((d, i) => (
              <path key={i} d={d} />
            ))}
          </clipPath>
        </defs>

        {/* ── Ruler ── */}
        <line
          x1={RULER_X}
          y1={PERSON_TOP - 4}
          x2={RULER_X}
          y2={GROUND_Y}
          stroke="#e2e8f0"
          strokeWidth={1}
        />
        {/* Ground tick */}
        <line
          x1={RULER_X - 5}
          y1={GROUND_Y}
          x2={RULER_X + 4}
          y2={GROUND_Y}
          stroke="#cbd5e1"
          strokeWidth={1}
        />
        <text
          x={RULER_X - 7}
          y={GROUND_Y + 4}
          textAnchor="end"
          fontSize={7}
          fill="#94a3b8"
        >
          0
        </text>
        {/* Top (165 cm) */}
        <text
          x={RULER_X - 7}
          y={PERSON_TOP + 3}
          textAnchor="end"
          fontSize={7}
          fill="#94a3b8"
        >
          165cm
        </text>

        {/* Depth ticks */}
        {FLOOD_DEPTH_OPTIONS.map((s) => {
          const y = depthY(s.centimeters);
          const active = hoveredDepth === s.id;
          return (
            <g key={s.id}>
              <line
                x1={RULER_X - 5}
                y1={y}
                x2={RULER_X + 4}
                y2={y}
                stroke={active ? color : "#cbd5e1"}
                strokeWidth={active ? 1.5 : 0.75}
              />
              <text
                x={RULER_X - 7}
                y={y + 3}
                textAnchor="end"
                fontSize={7}
                fill={active ? color : "#b0b8c4"}
                fontWeight={active ? 600 : 400}
              >
                {Math.round(s.centimeters)}
              </text>
            </g>
          );
        })}

        {/* ── Person silhouette (slate grey) ── */}
        <circle
          cx={HEAD.cx}
          cy={HEAD.cy}
          r={HEAD.r}
          fill="#cbd5e1"
        />
        {ALL_BODY.map((d, i) => (
          <path key={i} d={d} fill="#cbd5e1" />
        ))}

        {/* ── Animated water fill (clipped to person) ── */}
        <g clipPath={`url(#${clipId})`}>
          <motion.g
            initial={{ y: GROUND_Y + 20 }}
            animate={{ y: waterY }}
            transition={SPRING}
          >
            <path d={WAVE} fill={color} opacity={0.4} />
          </motion.g>
        </g>

        {/* ── Dashed reference line at water surface ── */}
        <motion.line
          x1={RULER_X}
          x2={208}
          y1={0}
          y2={0}
          initial={{ y: GROUND_Y + 20, opacity: 0 }}
          animate={{ y: waterY, opacity: spec ? 0.6 : 0 }}
          transition={{ y: SPRING, opacity: { duration: 0.2 } }}
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray="6 3"
        />

        {/* ── Depth label bubble ── */}
        <motion.g
          initial={{ y: GROUND_Y + 20, opacity: 0 }}
          animate={{ y: waterY, opacity: spec ? 1 : 0 }}
          transition={{ y: SPRING, opacity: { duration: 0.2 } }}
        >
          <rect
            x={210}
            y={-24}
            width={98}
            height={30}
            rx={6}
            fill="white"
            stroke={color}
            strokeWidth={1.5}
            opacity={0.95}
          />
          <text
            x={259}
            y={-9}
            textAnchor="middle"
            fontSize={10}
            fontWeight={600}
            fill={color}
          >
            {spec?.label ?? ""}
          </text>
          <text
            x={259}
            y={5}
            textAnchor="middle"
            fontSize={8}
            fill="#64748b"
          >
            {spec?.formatted ?? ""}
          </text>
        </motion.g>
      </svg>

      {/* Idle prompt (below SVG so Tailwind responsive classes work) */}
      {!spec && (
        <p className="text-[11px] text-slate-400 text-center mt-1">
          <span className="hidden lg:inline">Hover</span>
          <span className="lg:hidden">Tap</span>
          {" a depth level to see the flood line"}
        </p>
      )}

      {/* Disclaimer badge */}
      <div className="mt-2 text-center">
        <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 bg-slate-50 px-2.5 py-1 rounded-full border border-slate-100">
          📏 165 cm (5′5″) reference · DOST-FNRI standard
        </span>
      </div>
    </div>
  );
}
