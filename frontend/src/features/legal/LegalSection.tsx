import type { ReactNode } from "react";

export function LegalSection({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-heading`} className="space-y-3">
      <h3 id={`${id}-heading`} className="text-base font-semibold text-slate-950 sm:text-lg">{title}</h3>
      {children}
    </section>
  );
}
