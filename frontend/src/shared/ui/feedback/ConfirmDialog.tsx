import React, { ReactNode } from "react";
import { Modal } from "./Modal";
import { Button } from "../forms/Button";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "danger" | "ghost";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
  secondaryVariant?: ButtonVariant;
  confirmVariant?: ButtonVariant;
  variant?: "default" | "destructive";
  isLoading?: boolean;
  size?: "sm" | "md";
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  secondaryLabel,
  onSecondary,
  secondaryVariant = "outline",
  confirmVariant,
  variant = "default",
  isLoading = false,
  size = "md",
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title} size={size}>
      <div className={size === "sm" ? "space-y-3" : "space-y-4"}>
        <div className={size === "sm" ? "text-sm leading-relaxed text-gray-700" : "text-gray-700"}>
          {message}
        </div>
        <div className={cn("flex flex-nowrap justify-end gap-2 border-t border-gray-100", size === "sm" ? "pt-3" : "gap-3 pt-4")}>
          <Button 
            variant="outline" 
            onClick={onCancel} 
            disabled={isLoading}
            size={size === "sm" ? "sm" : "md"}
            className="shrink-0 whitespace-nowrap"
          >
            {cancelLabel}
          </Button>
          <Button 
            variant={confirmVariant ?? (variant === "destructive" ? "danger" : "primary")}
            onClick={onConfirm}
            disabled={isLoading}
            size={size === "sm" ? "sm" : "md"}
            className="shrink-0 whitespace-nowrap"
          >
            {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            {confirmLabel}
          </Button>
          {secondaryLabel && onSecondary ? (
            <Button
              variant={secondaryVariant}
              onClick={onSecondary}
              disabled={isLoading}
              size={size === "sm" ? "sm" : "md"}
              className="shrink-0 whitespace-nowrap"
            >
              {secondaryLabel}
            </Button>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}
