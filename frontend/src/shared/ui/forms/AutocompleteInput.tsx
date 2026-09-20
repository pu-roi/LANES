"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Check } from "lucide-react";
import { Input, type InputProps } from "./Input";
import { cn } from "@/lib/utils";

export interface AutocompleteInputProps extends Omit<InputProps, "onChange" | "value" | "onSelect" | "onFocus" | "onKeyDown"> {
  value: string;
  onChange: (value: string) => void;
  options: string[];
  onSelect?: (value: string) => void;
  maxSuggestions?: number;
}

/** Shared suggestion input for searchable staff filters and form fields. */
export function AutocompleteInput({
  value,
  onChange,
  onSelect,
  options,
  maxSuggestions = 8,
  className,
  ...inputProps
}: AutocompleteInputProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const filteredOptions = useMemo(() => {
    const query = value.trim().toLowerCase();
    return [...new Set(options)]
      .filter((option) => !query || option.toLowerCase().includes(query))
      .slice(0, maxSuggestions);
  }, [maxSuggestions, options, value]);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const selectOption = (option: string) => {
    onChange(option);
    onSelect?.(option);
    setIsOpen(false);
    setHighlightIndex(-1);
  };

  return (
    <div ref={containerRef} className="relative">
      <Input
        {...inputProps}
        value={value}
        className={cn("pr-8", className)}
        autoComplete="off"
        onChange={(event) => {
          onChange(event.target.value);
          setIsOpen(true);
          setHighlightIndex(-1);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(event) => {
          if (!isOpen || filteredOptions.length === 0) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setHighlightIndex((previous) => (previous + 1) % filteredOptions.length);
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setHighlightIndex((previous) => (previous <= 0 ? filteredOptions.length - 1 : previous - 1));
          } else if (event.key === "Enter" && highlightIndex >= 0) {
            event.preventDefault();
            selectOption(filteredOptions[highlightIndex]);
          } else if (event.key === "Escape") {
            setIsOpen(false);
          }
        }}
      />
      {isOpen && filteredOptions.length > 0 && (
        <div role="listbox" className="absolute left-0 right-0 top-full z-40 mt-1 max-h-60 overflow-y-auto rounded-lg border border-gray-100 bg-white py-1 shadow-xl">
          {filteredOptions.map((option, index) => (
            <button
              key={option}
              type="button"
              role="option"
              aria-selected={highlightIndex === index}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => selectOption(option)}
              className={cn(
                "flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors",
                highlightIndex === index ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
              )}
            >
              <span className="truncate">{option}</span>
              {value === option && <Check className="h-4 w-4 shrink-0 text-blue-600" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
