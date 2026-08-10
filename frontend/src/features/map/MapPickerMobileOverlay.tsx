import { Check, X } from "lucide-react";

interface MapPickerMobileOverlayProps {
  onCancel: () => void;
  onConfirm: () => void;
  confirmText: string;
}

export function MapPickerMobileOverlay({ onCancel, onConfirm, confirmText }: MapPickerMobileOverlayProps) {
  return (
    <div className="absolute inset-0 pointer-events-none z-40 flex flex-col justify-between">
      <div className="p-4 pointer-events-auto">
        <button
          onClick={onCancel}
          className="flex items-center justify-center w-12 h-12 bg-white rounded-full shadow-md text-gray-900 hover:bg-gray-100 border border-gray-300"
        >
          <X className="w-6 h-6" />
        </button>
      </div>
      
      <div className="p-4 pointer-events-auto flex justify-center pb-24">
        <button
          onClick={onConfirm}
          className="flex items-center justify-center gap-2 bg-blue-600 text-white rounded-full px-6 py-3 shadow-lg font-bold text-base border border-blue-500 hover:bg-blue-700 transition-all min-w-[200px]"
        >
          <Check className="w-5 h-5" />
          {confirmText}
        </button>
      </div>
    </div>
  );
}
