"use client";

import { useState } from "react";
import { X, Check, RotateCcw } from "lucide-react";

interface ColorPickerProps {
  initialColor: string;
  defaultColor?: string;
  onSave: (color: string) => void;
  onCancel: () => void;
}

export function ColorPicker({ initialColor, defaultColor = "#3b82f6", onSave, onCancel }: ColorPickerProps) {
  const [color, setColor] = useState(initialColor || defaultColor);

  return (
    <div className="absolute top-full right-0 mt-2 bg-white rounded-xl shadow-xl border border-slate-200 p-4 z-50 w-64 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-800">Select Cover Color</h3>
        <button type="button" onClick={onCancel} className="text-slate-400 hover:text-slate-600 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <div className="mb-4 flex items-center gap-3">
        <div className="w-16 border border-slate-200 p-1 rounded-lg shrink-0">
          <input 
            type="color" 
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="w-full h-10 rounded cursor-pointer border-0 p-0 block bg-transparent"
          />
        </div>
        <div className="flex-1">
          <input 
            type="text" 
            value={color.toUpperCase()}
            onChange={(e) => setColor(e.target.value)}
            className="w-full h-12 px-3 text-sm font-mono border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
            placeholder="#000000"
          />
        </div>
      </div>

      <div className="flex gap-2">
        <button 
          type="button"
          onClick={() => onSave(color)}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg flex items-center justify-center gap-1 transition-colors"
        >
          <Check className="w-4 h-4" /> Save
        </button>
        <button 
          type="button"
          onClick={() => setColor(defaultColor)}
          className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium py-2 rounded-lg flex items-center justify-center gap-1 transition-colors"
        >
          <RotateCcw className="w-4 h-4" /> Reset
        </button>
      </div>
    </div>
  );
}
