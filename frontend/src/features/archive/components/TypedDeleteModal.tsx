"use client";

import React, { useState, useEffect } from "react";
import { AlertTriangle, Trash2, X, Loader2 } from "lucide-react";
import { Button, Input, Modal } from "@/shared/ui";

interface TypedDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading?: boolean;
  title: string;
  itemName: string;
  itemType?: string;
  expectedWord?: string;
}

export function TypedDeleteModal({
  isOpen,
  onClose,
  onConfirm,
  isLoading = false,
  title,
  itemName,
  itemType = "record",
  expectedWord = "DELETE",
}: TypedDeleteModalProps) {
  const [typedInput, setTypedInput] = useState("");

  useEffect(() => {
    if (isOpen) {
      setTypedInput("");
    }
  }, [isOpen]);

  const isMatch = typedInput.trim().toUpperCase() === expectedWord.toUpperCase();

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && isMatch && !isLoading) {
      e.preventDefault();
      onConfirm();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="space-y-4 text-gray-700">
        <div className="flex items-start gap-3 p-3.5 bg-red-50 rounded-xl border border-red-200 text-red-800 text-sm">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-red-900">Permanent and Irreversible Action</p>
            <p className="text-xs text-red-700 leading-relaxed">
              This action cannot be undone. This {itemType} will be permanently purged from the database and will no longer be recoverable.
            </p>
          </div>
        </div>

        <p className="text-sm">
          You are about to permanently delete <strong>{itemName}</strong>.
        </p>

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider">
            Type <span className="font-mono text-red-600 font-bold">{expectedWord}</span> to confirm:
          </label>
          <Input
            value={typedInput}
            onChange={(e) => setTypedInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={expectedWord}
            autoFocus
            className="font-mono text-sm uppercase tracking-wider border-gray-300 focus:border-red-500 focus:ring-red-500"
          />
        </div>

        <div className="flex justify-end gap-2.5 pt-3 border-t border-gray-100">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-xl"
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={onConfirm}
            disabled={!isMatch || isLoading}
            className="rounded-xl gap-1.5 font-semibold"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
            Permanently Delete
          </Button>
        </div>
      </div>
    </Modal>
  );
}
