import { type ReactNode } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: "sm" | "md";
  blurBackdrop?: boolean;
  bare?: boolean;
}

export function Modal({ isOpen, onClose, title, children, size = "md", blurBackdrop = true, bare = false }: ModalProps) {
  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className={cn("absolute inset-0 bg-black/50 transition-opacity", blurBackdrop && "backdrop-blur-sm")}
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div className={cn(
        "relative z-10 w-full text-gray-900 transform scale-100 transition-all",
        bare ? "max-w-md" : "bg-white rounded-xl shadow-2xl",
        !bare && (size === "sm" ? "max-w-[18rem] p-4" : "max-w-md p-6")
      )}>
        {!bare && (
          <div className={cn("flex items-center justify-between", size === "sm" ? "mb-3" : "mb-4")}>
            <h2 className={cn("font-bold text-gray-900", size === "sm" ? "text-lg" : "text-xl")}>{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-700 transition"
            >
              ✕
            </button>
          </div>
        )}
        <div>
          {children}
        </div>
      </div>
    </div>,
    document.body,
  );
}
