"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";

export type ToastType = "success" | "error" | "info";

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface ToastMessage {
  id: string;
  title: string;
  message?: string;
  type: ToastType;
  action?: ToastAction;
}

interface ToastContextType {
  showToast: (title: string, message?: string, type?: ToastType, action?: ToastAction) => void;
  success: (title: string, message?: string, action?: ToastAction) => void;
  error: (title: string, message?: string, action?: ToastAction) => void;
  info: (title: string, message?: string, action?: ToastAction) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((title: string, message?: string, type: ToastType = "info", action?: ToastAction) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type, action }]);

    // Auto dismiss after 5 seconds if there's an action, else 4
    setTimeout(() => {
      removeToast(id);
    }, action ? 5000 : 4000);
  }, [removeToast]);

  const success = useCallback((title: string, message?: string, action?: ToastAction) => showToast(title, message, "success", action), [showToast]);
  const error = useCallback((title: string, message?: string, action?: ToastAction) => showToast(title, message, "error", action), [showToast]);
  const info = useCallback((title: string, message?: string, action?: ToastAction) => showToast(title, message, "info", action), [showToast]);

  const [mounted, setMounted] = useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const toastContainer = (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-3 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex w-80 shadow-lg rounded-xl overflow-hidden animate-in slide-in-from-bottom-5 fade-in duration-300
            ${toast.type === "success" ? "bg-white border border-emerald-100" : ""}
            ${toast.type === "error" ? "bg-white border border-red-100" : ""}
            ${toast.type === "info" ? "bg-white border border-blue-100" : ""}
          `}
        >
          {/* Status indicator bar */}
          <div className={`w-1.5 shrink-0
            ${toast.type === "success" ? "bg-emerald-500" : ""}
            ${toast.type === "error" ? "bg-red-500" : ""}
            ${toast.type === "info" ? "bg-blue-500" : ""}
          `} />
          
          <div className="flex p-3 w-full gap-3 items-start">
            <div className="shrink-0 mt-0.5">
              {toast.type === "success" && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
              {toast.type === "error" && <XCircle className="w-5 h-5 text-red-500" />}
              {toast.type === "info" && <Info className="w-5 h-5 text-blue-500" />}
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900">{toast.title}</p>
              {toast.message && (
                <p className="text-sm text-gray-500 mt-0.5 leading-snug">{toast.message}</p>
              )}
              {toast.action && (
                <button
                  onClick={() => {
                    toast.action!.onClick();
                    removeToast(toast.id);
                  }}
                  className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-700 focus:outline-none"
                >
                  {toast.action.label}
                </button>
              )}
            </div>
            
            <button
              onClick={() => removeToast(toast.id)}
              className="shrink-0 p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors focus:outline-none"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <ToastContext.Provider value={{ showToast, success, error, info }}>
      {children}
      {mounted ? require("react-dom").createPortal(toastContainer, document.body) : null}
    </ToastContext.Provider>
  );
}
