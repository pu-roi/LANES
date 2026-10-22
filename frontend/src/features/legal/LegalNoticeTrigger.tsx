"use client";

import { useCallback, useState, type ReactNode } from "react";
import { RecordDetailsDialog } from "@/shared/ui/feedback/RecordDetailsDialog";
import { PrivacyContent } from "./PrivacyContent";
import { TermsContent } from "./TermsContent";

type Notice = "privacy" | "terms";

export function LegalNoticeTrigger({ notice, children, className }: { notice: Notice; children: ReactNode; className?: string }) {
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);
  const title = notice === "privacy" ? "Privacy Policy" : "Terms of Service";

  return (
    <>
      <button type="button" className={className} onClick={(event) => {
        // Touch activation does not consistently focus buttons. The shared
        // dialog restores document.activeElement when it closes.
        event.currentTarget.focus({ preventScroll: true });
        setOpen(true);
      }}>
        {children}
      </button>
      {open && (
        <RecordDetailsDialog
          title={title}
          subtitle={`Last updated: 15 October 2026`}
          closeLabel={`Close ${title}`}
          onClose={close}
        >
          <p className="text-sm leading-6 text-slate-600">
            {notice === "privacy"
              ? "This notice explains what personal data LANES collects, why it is used, who may receive it, and how you can exercise your rights."
              : "These terms explain how to use LANES and the limits of its flood information and route guidance."}
          </p>
          {notice === "privacy" ? <PrivacyContent /> : <TermsContent />}
        </RecordDetailsDialog>
      )}
    </>
  );
}
