"use client";

import React, { useState, useRef, useEffect, forwardRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { ChevronDown, Check, Pin } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MultiSelectOption {
  label: string;
  value: string | number;
  isPinned?: boolean;
}

export interface MultiSelectProps {
  options: MultiSelectOption[];
  value: (string | number)[];
  onChange: (value: (string | number)[]) => void;
  label?: string;
  error?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export const MultiSelect = forwardRef<HTMLDivElement, MultiSelectProps>(
  ({ options, value, onChange, label, error, placeholder, className = "", disabled = false }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dropdownRect, setDropdownRect] = useState<DOMRect | null>(null);

    const [searchQuery, setSearchQuery] = useState("");

    const updateRect = useCallback(() => {
      if (containerRef.current) {
        setDropdownRect(containerRef.current.getBoundingClientRect());
      }
    }, []);

    useEffect(() => {
      if (isOpen) {
        updateRect();
        window.addEventListener("scroll", updateRect, true);
        window.addEventListener("resize", updateRect);
        return () => {
          window.removeEventListener("scroll", updateRect, true);
          window.removeEventListener("resize", updateRect);
        };
      } else {
        setSearchQuery(""); // reset search when closed
      }
    }, [isOpen, updateRect]);

    // Handle click outside to close
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          containerRef.current && 
          !containerRef.current.contains(event.target as Node) &&
          !(event.target as HTMLElement).closest('[data-portal="multi-select-dropdown"]')
        ) {
          setIsOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const toggleOption = (optionValue: string | number) => {
      if (value.includes(optionValue)) {
        onChange(value.filter((v) => v !== optionValue));
      } else {
        onChange([...value, optionValue]);
      }
    };

    const displayText = value.length > 0 
      ? `${value.length} selected`
      : placeholder || "Select...";

    const filteredOptions = options.filter(opt => 
      opt.label.toLowerCase().includes(searchQuery.toLowerCase())
    );

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
            onClick={() => !disabled && setIsOpen(!isOpen)}
            disabled={disabled}
            className={`
              w-full flex items-center justify-between rounded-lg border px-3 py-2 text-sm transition-all duration-200 outline-none
              ${disabled 
                ? "bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed" 
                : isOpen 
                  ? "bg-white border-blue-500 ring-2 ring-blue-100" 
                  : "bg-white border-gray-200 hover:border-gray-300 text-gray-900"}
              ${error ? "border-red-500 focus:border-red-500 focus:ring-red-100 ring-red-100" : ""}
            `}
          >
            <span className={value.length > 0 && !disabled ? "font-medium" : ""}>
              {displayText}
            </span>
            <ChevronDown 
              className={`h-4 w-4 transition-transform duration-200 ${isOpen ? "rotate-180 text-blue-500" : "text-gray-400"}`} 
            />
          </button>
          
          {isOpen && typeof document !== "undefined" && createPortal(
              <div
                data-portal="multi-select-dropdown"
                className="fixed mt-1 rounded-lg border border-gray-100 bg-white shadow-xl overflow-hidden py-1 flex flex-col"
                style={{
                  zIndex: 99999,
                  top: dropdownRect ? dropdownRect.bottom : 0,
                  left: dropdownRect ? dropdownRect.left : 0,
                  minWidth: dropdownRect ? dropdownRect.width : 0,
                  width: "max-content",
                  maxWidth: "350px",
                  maxHeight: "300px",
                }}
              >
                <div className="p-2 border-b border-gray-100 shrink-0">
                  <input
                    type="text"
                    autoFocus
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-md outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div className="overflow-y-auto overflow-x-hidden scrollbar-thin flex-1">
                  {filteredOptions.length === 0 ? (
                    <div className="px-3 py-4 text-sm text-gray-500 text-center">No results found</div>
                  ) : (
                    filteredOptions.map((option) => {
                      const isSelected = value.includes(option.value);
                      return (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => toggleOption(option.value)}
                          className={`
                            w-full flex items-center gap-3 px-3 py-2 text-sm transition-colors text-left
                            hover:bg-gray-50 hover:text-gray-900
                          `}
                        >
                          <div className={`
                            w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors
                            ${isSelected ? "bg-blue-600 border-blue-600 text-white" : "border-gray-300 bg-white"}
                          `}>
                            {isSelected && <Check className="w-3 h-3" />}
                          </div>
                          <span className={`truncate ${isSelected ? "text-gray-900 font-medium" : "text-gray-700"} flex-1 text-left`}>
                            {option.label}
                          </span>
                          {option.isPinned && (
                            <Pin className="w-3 h-3 text-blue-500 shrink-0 ml-1" />
                          )}
                        </button>
                      );
                    })
                  )}
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

MultiSelect.displayName = "MultiSelect";
