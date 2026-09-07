"use client";

import React, { useState, useRef, useEffect, forwardRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { ChevronDown, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export interface SelectOption {
  label: string;
  value: string | number;
}

export interface SelectProps {
  options: SelectOption[];
  value: string | number;
  onChange: (e: { target: { value: string | number } }) => void;
  label?: string;
  error?: string;
  placeholder?: string;
  className?: string;
}

export const Select = forwardRef<HTMLDivElement, SelectProps>(
  ({ options, value, onChange, label, error, placeholder, className = "" }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dropdownRect, setDropdownRect] = useState<DOMRect | null>(null);

    const selectedOption = options.find((opt) => opt.value === value);

    const updateRect = useCallback(() => {
      if (containerRef.current) {
        setDropdownRect(containerRef.current.getBoundingClientRect());
      }
    }, []);

    useEffect(() => {
      if (isOpen) {
        updateRect();
        window.addEventListener("scroll", updateRect, true); // capture phase to handle inner scrolls
        window.addEventListener("resize", updateRect);
        return () => {
          window.removeEventListener("scroll", updateRect, true);
          window.removeEventListener("resize", updateRect);
        };
      }
    }, [isOpen, updateRect]);

    // Handle click outside to close
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          containerRef.current && 
          !containerRef.current.contains(event.target as Node) &&
          !(event.target as HTMLElement).closest('[data-portal="select-dropdown"]')
        ) {
          setIsOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSelect = (optionValue: string | number) => {
      onChange({ target: { value: optionValue } });
      setIsOpen(false);
    };

    return (
      <div className={cn("flex flex-col gap-1 w-full", className)} ref={containerRef}>
        {label && (
          <label className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        
        <div className="relative w-full" ref={ref}>
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className={`
              w-full flex items-center justify-between rounded-lg border bg-white px-3 py-2 text-sm text-gray-900 
              shadow-sm outline-none transition-all duration-200
              focus:border-blue-500 focus:ring-2 focus:ring-blue-100
              ${isOpen ? "border-blue-500 ring-2 ring-blue-100" : "border-gray-200 hover:border-gray-300"}
              ${error ? "border-red-500 focus:border-red-500 focus:ring-red-100 ring-red-100" : ""}
            `}
          >
            <span className={selectedOption && selectedOption.value !== "" ? "text-gray-900 font-medium" : "text-gray-400"}>
              {selectedOption ? selectedOption.label : placeholder || "Select..."}
            </span>
            <ChevronDown 
              className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180 text-blue-500" : ""}`} 
            />
          </button>
          
          {isOpen && typeof document !== "undefined" && createPortal(
              <div
                data-portal="select-dropdown"
                className="fixed mt-1 rounded-lg border border-gray-100 bg-white shadow-xl overflow-hidden py-1"
                style={{
                  zIndex: 99999,
                  top: dropdownRect ? dropdownRect.bottom : 0,
                  left: dropdownRect ? dropdownRect.left : 0,
                  width: dropdownRect ? dropdownRect.width : 0,
                }}
              >
                <div className="max-h-60 overflow-y-auto overflow-x-hidden scrollbar-thin">
                  {options.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => handleSelect(option.value)}
                      className={`
                        w-full flex items-center justify-between px-3 py-2 text-sm transition-colors text-left
                        ${value === option.value ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"}
                      `}
                    >
                      <span className="truncate">{option.label}</span>
                      {value === option.value && (
                        <Check className="h-4 w-4 text-blue-600 shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              </div>,
              document.body
            )}
        </div>

        {error && (
          <p className="text-xs text-red-500 font-medium mt-0.5">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = "Select";
