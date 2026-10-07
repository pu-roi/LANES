"use client";

import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: ReactNode;
  description?: ReactNode;
  containerClassName?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, id, className, containerClassName, disabled, "aria-describedby": describedBy, ...props }, ref) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const descriptionId = description ? `${inputId}-description` : undefined;

    return (
      <div className={cn("flex items-start gap-3", disabled && "opacity-60", containerClassName)}>
        <input
          {...props}
          ref={ref}
          id={inputId}
          type="checkbox"
          disabled={disabled}
          aria-describedby={[describedBy, descriptionId].filter(Boolean).join(" ") || undefined}
          className={cn("mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded border-gray-300 accent-blue-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 disabled:cursor-not-allowed", className)}
        />
        <div className="min-w-0 text-sm">
          <label htmlFor={inputId} className={cn("font-medium text-gray-900", disabled ? "cursor-not-allowed" : "cursor-pointer")}>{label}</label>
          {description && <p id={descriptionId} className="mt-1 leading-relaxed text-gray-500">{description}</p>}
        </div>
      </div>
    );
  }
);

Checkbox.displayName = "Checkbox";
