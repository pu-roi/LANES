import React, { ReactNode } from "react";
import { Modal } from "./Modal";
import { Button } from "../forms/Button";
import { Loader2 } from "lucide-react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: "default" | "destructive";
  isLoading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  variant = "default",
  isLoading = false,
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title}>
      <div className="space-y-4">
        <div className="text-gray-700">
          {message}
        </div>
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-100">
          <Button 
            variant="outline" 
            onClick={onCancel} 
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button 
            variant={variant === "destructive" ? "danger" : "primary"} 
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
