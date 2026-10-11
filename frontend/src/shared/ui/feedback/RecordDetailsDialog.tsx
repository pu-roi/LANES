"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "../forms/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../layout/Card";

export function RecordDetailsDialog({ title, subtitle, closeLabel, onClose, children, footer, placement = "center", size = "default", bodyLayout = "flow" }: { title: string; subtitle?: string; closeLabel: string; onClose: () => void; children: ReactNode; footer?: ReactNode; placement?: "center" | "drawer"; size?: "default" | "wide"; bodyLayout?: "flow" | "panels" }) {
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButton.current?.focus({ preventScroll: true });
    const handleKey = (event: KeyboardEvent) => {
      if (document.querySelector("[data-media-viewer]")) return;
      if (event.key === "Escape") { event.preventDefault(); onClose(); }
      if (event.key !== "Tab") return;
      const inside = Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), summary, [tabindex="0"]') ?? []);
      const openSelect = dialog.current?.querySelector('button[data-select-trigger="true"][aria-expanded="true"]');
      const options = openSelect ? Array.from(document.querySelectorAll<HTMLElement>('[data-portal="select-dropdown"] button:not([disabled])')) : [];
      const nodes = [...inside, ...options].filter((node) => node.getClientRects().length > 0);
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener("keydown", handleKey);
    return () => {
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", handleKey);
      opener?.focus({ preventScroll: true });
    };
  }, [onClose]);
  return createPortal(<motion.div className={`fixed inset-0 z-[100] flex bg-slate-950/60 backdrop-blur-xs ${placement === "drawer" ? "items-stretch justify-end" : "items-center justify-center p-3 sm:p-4"}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <motion.div className={`w-full ${placement === "drawer" ? "max-w-3xl" : size === "wide" ? "max-w-5xl" : "max-w-2xl"}`} initial={placement === "drawer" ? { x: 40, opacity: 0 } : { scale: 0.97, y: 12 }} animate={{ scale: 1, x: 0, y: 0, opacity: 1 }} transition={{ duration: 0.18 }}>
      <Card ref={dialog} role="dialog" aria-modal="true" aria-labelledby={titleId} className={`flex flex-col shadow-2xl ${placement === "drawer" ? "h-dvh rounded-none" : bodyLayout === "panels" ? "h-[min(54rem,calc(100dvh-1.5rem))] sm:h-[min(54rem,90dvh)]" : "max-h-[calc(100dvh-1.5rem)] sm:max-h-[90dvh]"}`}>
        <CardHeader className="flex shrink-0 items-start justify-between gap-3 p-4 sm:px-6">
          <div className="min-w-0"><CardTitle id={titleId}>{title}</CardTitle>{subtitle && <p className="mt-1 break-words text-xs text-gray-500">{subtitle}</p>}</div>
          <span ref={(node) => { closeButton.current = node?.querySelector("button") ?? null; }}><Button variant="ghost" size="sm" aria-label={closeLabel} onClick={onClose} className="min-h-11 min-w-11 px-2"><X className="size-5" aria-hidden="true" /></Button></span>
        </CardHeader>
        <CardContent className={`min-h-0 p-4 sm:p-6 ${footer ? "" : "pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] sm:pb-[calc(1.5rem+env(safe-area-inset-bottom))]"} ${bodyLayout === "panels" ? "flex flex-1 flex-col overflow-hidden" : "space-y-5 overflow-y-auto"}`}>{children}</CardContent>
        {footer && <div className="shrink-0 border-t border-slate-100 bg-slate-50/80 px-4 py-3 pb-[calc(0.75rem+var(--bottom-nav-height)+env(safe-area-inset-bottom))] sm:px-6 sm:pb-[calc(0.75rem+env(safe-area-inset-bottom))]">{footer}</div>}
      </Card>
    </motion.div>
  </motion.div>, document.body);
}
