import { type ReactNode, useEffect } from "react";
import { cn } from "@/lib/utils";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: "sm" | "md";
}

export function Modal({ isOpen, onClose, title, children, size = "md" }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div className={cn(
        "relative z-10 w-full bg-white text-gray-900 rounded-xl shadow-2xl transform scale-100 transition-all",
        size === "sm" ? "max-w-[18rem] p-4" : "max-w-md p-6"
      )}>
        <div className={cn("flex items-center justify-between", size === "sm" ? "mb-3" : "mb-4")}>
          <h2 className={cn("font-bold text-gray-900", size === "sm" ? "text-lg" : "text-xl")}>{title}</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 transition"
          >
            ✕
          </button>
        </div>
        <div>
          {children}
        </div>
      </div>
    </div>
  );
}
