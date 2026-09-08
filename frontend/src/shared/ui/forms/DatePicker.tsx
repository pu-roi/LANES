"use client";

import React, { useState, useRef, useEffect, forwardRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { ChevronLeft, ChevronRight, ChevronDown, Calendar as CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DatePickerProps {
  label?: string;
  value: string; // YYYY-MM-DD format expected
  onChange: (e: { target: { value: string } }) => void;
  className?: string;
  disabled?: boolean;
  required?: boolean;
  labelClassName?: string;
  align?: "left" | "right";
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const MONTH_ABBRS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

// Custom date input — renders typed digits dark, placeholder chars light gray
function DateDisplay({ digits }: { digits: string }) {
  const ph = (char: string, slot: number) => (
    <span key={`ph-${slot}`} className="text-gray-400">{char}</span>
  );
  const ch = (char: string, slot: number) => (
    <span key={`ch-${slot}`} className="text-gray-900">{char}</span>
  );

  const slots: React.ReactNode[] = [];
  const placeholders = ['m','m','/','d','d','/','y','y','y','y'];
  let digitIdx = 0;

  for (let slot = 0; slot < 10; slot++) {
    if (slot === 2 || slot === 5) {
      slots.push(<span key={`slash-${slot}`} className="text-gray-400">/</span>);
    } else {
      const digit = digits[digitIdx];
      slots.push(digit ? ch(digit, slot) : ph(placeholders[slot], slot));
      digitIdx++;
    }
  }

  return (
    <div className="flex items-center text-sm select-none">
      {slots}
    </div>
  );
}

// Build the string value for the overlay input so the native caret sits at the right position
// e.g. digits="06" → "06/" so caret is after the slash
function getCursorValue(digits: string): string {
  let result = '';
  for (let i = 0; i < digits.length; i++) {
    result += digits[i];
    if (i === 1 || i === 3) result += '/';
  }
  return result;
}

export const DatePicker = forwardRef<HTMLDivElement, DatePickerProps>(
  ({ label, value, onChange, className, disabled, required, labelClassName, align = "left" }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const hiddenInputRef = useRef<HTMLInputElement>(null);
    const [isFocused, setIsFocused] = useState(false);

    // Date logic
    const parsedDate = value ? new Date(value + "T12:00:00Z") : null;
    const today = new Date();

    const [currentMonth, setCurrentMonth] = useState(parsedDate ? parsedDate.getMonth() : today.getMonth());
    const [currentYear, setCurrentYear] = useState(parsedDate ? parsedDate.getFullYear() : today.getFullYear());
    const [viewMode, setViewMode] = useState<"days" | "years" | "months">("days");
    const [placement, setPlacement] = useState<"bottom" | "top">("bottom");
    const yearListRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to selected year when year view opens
    useEffect(() => {
      if (viewMode === "years" && yearListRef.current) {
        const selectedBtn = yearListRef.current.querySelector('[data-selected-year="true"]') as HTMLElement | null;
        if (selectedBtn) {
          selectedBtn.scrollIntoView({ block: "center" });
        }
      }
    }, [viewMode]);

    // Digit state — up to 8 numeric characters
    const [digits, setDigits] = useState<string>(() => {
      if (value) {
        const d = new Date(value + "T12:00:00Z");
        if (!isNaN(d.getTime())) {
          const m = (d.getMonth() + 1).toString().padStart(2, "0");
          const day = d.getDate().toString().padStart(2, "0");
          const y = d.getFullYear().toString();
          return m + day + y;
        }
      }
      return "";
    });

    // Sync digits when parent value changes (e.g. calendar selection or clear)
    useEffect(() => {
      if (value) {
        const d = new Date(value + "T12:00:00Z");
        if (!isNaN(d.getTime())) {
          const m = (d.getMonth() + 1).toString().padStart(2, "0");
          const day = d.getDate().toString().padStart(2, "0");
          const y = d.getFullYear().toString();
          setDigits(m + day + y);
          return;
        }
      }
      setDigits("");
    }, [value]);

    // Fire onChange when digits reaches 8
    const commitDigits = useCallback((d: string) => {
      if (d.length === 8) {
        const m = parseInt(d.substring(0, 2), 10);
        const day = parseInt(d.substring(2, 4), 10);
        const y = parseInt(d.substring(4, 8), 10);
        const date = new Date(y, m - 1, day);
        if (!isNaN(date.getTime()) && date.getFullYear() === y && date.getMonth() === m - 1 && date.getDate() === day) {
          const dateString = `${y}-${m.toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;
          onChange({ target: { value: dateString } });
          setCurrentMonth(date.getMonth());
          setCurrentYear(date.getFullYear());
          return;
        }
      }
      onChange({ target: { value: "" } });
    }, [onChange]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (disabled) return;

      if (e.key === "Backspace") {
        e.preventDefault();
        // Compute next outside the updater to avoid calling onChange inside setDigits
        const next = digits.slice(0, -1);
        setDigits(next);
        commitDigits(next);
        return;
      }

      if (e.key === "Delete") {
        e.preventDefault();
        setDigits("");
        onChange({ target: { value: "" } });
        return;
      }

      if (/^\d$/.test(e.key)) {
        e.preventDefault();
        if (digits.length >= 8) return;
        const next = digits + e.key;
        setDigits(next);
        commitDigits(next);
        return;
      }
    };

    // Placement logic
    const [rect, setRect] = useState<DOMRect | null>(null);

    const updatePosition = useCallback(() => {
      if (isOpen && containerRef.current) {
        const newRect = containerRef.current.getBoundingClientRect();
        setRect(newRect);
        
        const spaceBelow = window.innerHeight - newRect.bottom;
        const spaceAbove = newRect.top;
        if (spaceBelow < 310 && spaceAbove > spaceBelow) {
          setPlacement("top");
        } else {
          setPlacement("bottom");
        }
      }
    }, [isOpen]);

    useEffect(() => {
      if (isOpen) {
        updatePosition();
        window.addEventListener("scroll", updatePosition, true);
        window.addEventListener("resize", updatePosition);
        return () => {
          window.removeEventListener("scroll", updatePosition, true);
          window.removeEventListener("resize", updatePosition);
        };
      }
    }, [isOpen, updatePosition]);

    useEffect(() => {
      if (value) {
        const d = new Date(value + "T12:00:00Z");
        if (!isNaN(d.getTime())) {
          setCurrentMonth(d.getMonth());
          setCurrentYear(d.getFullYear());
        }
      }
    }, [value]);

    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        const target = event.target as HTMLElement | null;
        if (
          containerRef.current &&
          !containerRef.current.contains(target as Node) &&
          !target?.closest('[data-portal="datepicker-popup"]')
        ) {
          setIsOpen(false);
          setViewMode("days");
          setIsFocused(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleDayClick = (day: number) => {
      const newDate = new Date(Date.UTC(currentYear, currentMonth, day));
      const dateString = newDate.toISOString().split("T")[0];
      onChange({ target: { value: dateString } });
      setViewMode("days");
      setIsOpen(false);
    };

    const handleClear = () => {
      onChange({ target: { value: "" } });
      setDigits("");
      setViewMode("days");
      setIsOpen(false);
    };

    const handleToday = () => {
      const now = new Date();
      const dateString = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())).toISOString().split("T")[0];
      onChange({ target: { value: dateString } });
      setCurrentMonth(now.getMonth());
      setCurrentYear(now.getFullYear());
      setViewMode("days");
      setIsOpen(false);
    };

    const stepMonth = (dir: 1 | -1) => {
      let newMonth = currentMonth + dir;
      let newYear = currentYear;
      if (newMonth > 11) { newMonth = 0; newYear += 1; }
      else if (newMonth < 0) { newMonth = 11; newYear -= 1; }
      setCurrentMonth(newMonth);
      setCurrentYear(newYear);
    };

    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
    const days: (number | null)[] = [];
    for (let i = 0; i < firstDayOfMonth; i++) days.push(null);
    for (let i = 1; i <= daysInMonth; i++) days.push(i);

    const handleContainerClick = () => {
      if (!disabled) {
        hiddenInputRef.current?.focus();
        setIsFocused(true);
        if (!isOpen) {
          setIsOpen(true);
        }
      }
    };

    return (
      <div className={cn("relative w-full", className)} ref={containerRef}>
        {/* Label */}
        {label && (
          <label className={cn("block text-sm font-medium text-gray-700 mb-1", labelClassName)}>
            {label.includes("(Optional)") ? (
              <>
                {label.replace("(Optional)", "").trim()}
                <span className="text-gray-400 font-normal ml-1">(Optional)</span>
              </>
            ) : label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        {/* Custom input display */}
        <div
          onClick={handleContainerClick}
          className={cn(
            "flex w-full items-center rounded-lg border bg-white px-3 py-2 shadow-sm transition-all duration-200 cursor-text",
            isFocused ? "border-blue-500 ring-2 ring-blue-100" : "border-gray-200 hover:border-gray-300",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          <div className="flex-1 relative">
            {/* Display layer — colored digits + gray placeholders */}
            <DateDisplay digits={digits} />
            {/* Overlay input — transparent text, native dark caret */}
            <input
              ref={hiddenInputRef}
              type="text"
              inputMode="numeric"
              value={getCursorValue(digits)}
              onChange={() => {}}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => { if (!isOpen) setIsFocused(false); }}
              disabled={disabled}
              style={{
                position: 'absolute',
                inset: 0,
                opacity: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'transparent',
                caretColor: '#111827',
                fontSize: '0.875rem',
                letterSpacing: '0.025em',
                width: '100%',
                cursor: 'text',
                padding: 0,
              }}
            />
          </div>
          <CalendarIcon
            className="w-4 h-4 text-gray-400 cursor-pointer flex-shrink-0 ml-2"
            onClick={(e) => {
              e.stopPropagation();
              if (!disabled) {
                setIsOpen(prev => !prev);
                hiddenInputRef.current?.focus();
                setIsFocused(true);
              }
            }}
          />
        </div>


        {/* Calendar popup */}
        {isOpen && typeof document !== "undefined" && createPortal(
          <div 
            data-portal="datepicker-popup"
            data-lenis-prevent
            onMouseDown={(e) => e.stopPropagation()}
            className="fixed z-[99999] w-72 bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden"
            style={{
              top: placement === "bottom" && rect ? rect.bottom + 4 : undefined,
              bottom: placement === "top" && rect ? window.innerHeight - rect.top + 4 : undefined,
              left: align === "left" && rect ? rect.left : undefined,
              right: align === "right" && rect ? window.innerWidth - rect.right : undefined,
            }}
          >

            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-gray-100">
              <button
                type="button"
                onClick={() => setViewMode(prev => prev === "days" ? "years" : "days")}
                className="font-semibold text-gray-800 hover:bg-gray-100 px-2 py-1 rounded-md transition-colors flex items-center gap-1.5"
              >
                {viewMode === "years" ? (
                  <span>Select Year</span>
                ) : viewMode === "months" ? (
                  <span>{currentYear} &bull; Select Month</span>
                ) : (
                  <>
                    <span>{MONTHS[currentMonth]} {currentYear}</span>
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  </>
                )}
              </button>

              {viewMode === "days" && (
                <div className="flex items-center gap-1">
                  <button 
                    type="button" 
                    onClick={() => stepMonth(-1)} 
                    className="p-1.5 hover:bg-gray-100 rounded-md text-gray-600 transition-colors"
                    aria-label="Previous Month"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button 
                    type="button" 
                    onClick={() => stepMonth(1)} 
                    className="p-1.5 hover:bg-gray-100 rounded-md text-gray-600 transition-colors"
                    aria-label="Next Month"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* View Modes */}
            {viewMode === "years" ? (
              /* Dedicated Year Grid (covers up to 125 years back to 1901) */
              <div 
                ref={yearListRef}
                className="p-3 grid grid-cols-4 gap-2 h-[260px] overflow-y-auto"
                style={{ scrollbarWidth: "thin" }}
              >
                {Array.from({ length: 126 }, (_, i) => today.getFullYear() - i).map(y => {
                  const isSelectedYear = currentYear === y;
                  return (
                    <button
                      key={y}
                      type="button"
                      data-selected-year={isSelectedYear ? "true" : "false"}
                      onClick={() => {
                        setCurrentYear(y);
                        setViewMode("months"); // Next step: pick the month for this year
                      }}
                      className={cn(
                        "py-2 rounded-lg text-sm font-medium transition-all text-center",
                        isSelectedYear
                          ? "bg-blue-600 text-white shadow-sm font-semibold ring-2 ring-blue-200"
                          : "hover:bg-blue-50 text-gray-700 hover:text-blue-600"
                      )}
                    >
                      {y}
                    </button>
                  );
                })}
              </div>
            ) : viewMode === "months" ? (
              /* Month Selector Grid: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug... */
              <div className="p-4 grid grid-cols-3 gap-2.5 h-[260px] flex items-center content-center">
                {MONTH_ABBRS.map((abbr, idx) => {
                  const isSelectedMonth = currentMonth === idx;
                  return (
                    <button
                      key={abbr}
                      type="button"
                      onClick={() => {
                        setCurrentMonth(idx);
                        setViewMode("days"); // Return to original datepicker calendar grid!
                      }}
                      className={cn(
                        "py-3 rounded-lg text-sm font-medium transition-all text-center",
                        isSelectedMonth
                          ? "bg-blue-600 text-white shadow-sm font-semibold ring-2 ring-blue-200"
                          : "bg-slate-50 hover:bg-blue-50 text-gray-700 hover:text-blue-600 border border-slate-100"
                      )}
                    >
                      {abbr}
                    </button>
                  );
                })}
              </div>
            ) : (
              <>
                {/* Days Header */}
                <div className="grid grid-cols-7 gap-1 p-3 pb-2 text-center">
                  {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map(day => (
                    <div key={day} className="text-xs font-medium text-gray-500">{day}</div>
                  ))}
                </div>

                {/* Days Grid */}
                <div className="grid grid-cols-7 gap-1 px-3 pb-3">
                  {days.map((day, idx) => {
                    if (!day) return <div key={`empty-${idx}`} className="w-8 h-8" />;
                    const isSelected = parsedDate &&
                      parsedDate.getDate() === day &&
                      parsedDate.getMonth() === currentMonth &&
                      parsedDate.getFullYear() === currentYear;
                    const isToday =
                      today.getDate() === day &&
                      today.getMonth() === currentMonth &&
                      today.getFullYear() === currentYear;
                    return (
                      <button
                        key={day}
                        onClick={() => handleDayClick(day)}
                        className={cn(
                          "w-8 h-8 flex items-center justify-center rounded-md text-sm transition-colors",
                          isSelected
                            ? "bg-blue-600 text-white font-semibold shadow-md"
                            : "hover:bg-gray-100 text-gray-700",
                          !isSelected && isToday && "text-blue-600 font-bold bg-blue-50"
                        )}
                      >
                        {day}
                      </button>
                    );
                  })}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-3 border-t border-gray-100 bg-gray-50/50">
                  <button onClick={handleClear} className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors">
                    Clear
                  </button>
                  <button onClick={handleToday} className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors">
                    Today
                  </button>
                </div>
              </>
            )}
          </div>,
          document.body
        )}
      </div>
    );
  }
);

DatePicker.displayName = "DatePicker";
