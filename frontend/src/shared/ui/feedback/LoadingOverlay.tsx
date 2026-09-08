import { Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  variant?: "fixed" | "absolute" | "inline";
  zIndex?: number;
}

export function LoadingOverlay({
  isVisible,
  message = "Loading...",
  variant = "fixed",
  zIndex = 100,
}: LoadingOverlayProps) {
  if (variant === "inline") {
    return (
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-center gap-2.5 px-3 py-2.5 bg-blue-50 border border-blue-100 rounded-xl"
          >
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin shrink-0" />
            <p className="text-sm text-blue-700 font-medium">{message}</p>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{ zIndex }}
          className={cn(
            variant === "fixed" ? "fixed" : "absolute",
            "inset-0 flex flex-col items-center justify-center bg-neutral-100/50 backdrop-blur-sm pointer-events-none"
          )}
        >
          <Loader2 className="w-10 h-10 text-blue-600 animate-spin mb-3" />
          <p className="text-neutral-600 font-medium animate-pulse">{message}</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
