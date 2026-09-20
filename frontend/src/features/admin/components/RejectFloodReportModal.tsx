"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { Button, Modal, Select } from "@/shared/ui";
import type { FloodReport, RejectFloodReportPayload } from "../adminApi";

interface RejectFloodReportModalProps {
  report: FloodReport | null;
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (payload: RejectFloodReportPayload) => void;
}

const REJECTION_REASONS = [
  { value: "insufficient_evidence", label: "Insufficient evidence" },
  { value: "incorrect_location_or_details", label: "Incorrect location or details" },
  { value: "false_spam_or_malicious", label: "False, spam, or malicious" },
  { value: "outside_coverage_area", label: "Outside coverage area" },
  { value: "withdrawn", label: "Withdrawn" },
  { value: "other", label: "Other — explain below" },
];

export function RejectFloodReportModal({
  report,
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
}: RejectFloodReportModalProps) {
  const [reason, setReason] = useState<RejectFloodReportPayload["reason"]>("insufficient_evidence");
  const [internalNote, setInternalNote] = useState("");
  const requiresNote = reason === "other";

  useEffect(() => {
    if (isOpen) {
      setReason("insufficient_evidence");
      setInternalNote("");
    }
  }, [isOpen, report?.id]);

  const canSubmit = !requiresNote || internalNote.trim().length > 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Reject Flood Report" size="md">
      <div className="space-y-4">
        <div className="flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
          <p>
            Report #{report?.id} will leave the live moderation queue. Its original evidence remains available to authorized staff and is excluded from Flood Event analytics. The reporter will receive the selected reason in their notification bell; internal notes remain private to staff.
          </p>
        </div>

        <Select
          label="Rejection reason"
          value={reason}
          onChange={(event) => setReason(event.target.value as RejectFloodReportPayload["reason"])}
          options={REJECTION_REASONS}
        />

        <div className="flex flex-col gap-1">
          <label htmlFor="rejection-note" className="text-sm font-medium text-gray-700">
            Internal note{requiresNote ? <span className="ml-1 text-red-500">*</span> : <span className="ml-1 font-normal text-gray-400">(optional)</span>}
          </label>
          <textarea
            id="rejection-note"
            value={internalNote}
            onChange={(event) => setInternalNote(event.target.value)}
            maxLength={1000}
            rows={3}
            placeholder={requiresNote ? "Explain why this report cannot be accepted." : "Optional context for other staff."}
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>Cancel</Button>
          <Button
            type="button"
            variant="primary"
            onClick={() => onSubmit({ reason, internal_note: internalNote.trim() || undefined })}
            disabled={isSubmitting || !canSubmit}
            className="bg-rose-600 hover:bg-rose-700"
          >
            {isSubmitting ? "Rejecting…" : "Confirm rejection"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
