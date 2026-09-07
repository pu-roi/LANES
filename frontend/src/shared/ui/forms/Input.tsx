import React, { InputHTMLAttributes, forwardRef, ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  containerClassName?: string;
  labelClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, containerClassName, labelClassName, label, error, leftIcon, rightIcon, type = "text", ...props }, ref) => {
    return (
      <div className={cn("w-full flex flex-col gap-1", containerClassName)}>
        {label && (
          <label className={cn("text-sm font-medium text-gray-700", labelClassName)}>
            {label.includes("(Optional)") ? (
              <>
                {label.replace("(Optional)", "").trim()}
                <span className="text-gray-400 font-normal ml-1">(Optional)</span>
              </>
            ) : (
              label
            )}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        
        <div className="relative w-full">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none text-gray-500">
              {leftIcon}
            </div>
          )}
          
          <input
            type={type}
            className={cn(
              "flex w-full rounded-lg border bg-white px-3 py-2 text-sm text-gray-900",
              "placeholder:text-gray-400 shadow-sm outline-none transition-all duration-200",
              "focus:border-blue-500 focus:ring-2 focus:ring-blue-100",
              "disabled:cursor-not-allowed disabled:opacity-50",
              error ? "border-red-500 focus:border-red-500 focus:ring-red-100 ring-red-100" : "border-gray-200 hover:border-gray-300",
              leftIcon ? "pl-10" : "",
              rightIcon ? "pr-10" : "",
              className
            )}
            ref={ref}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center text-gray-500">
              {rightIcon}
            </div>
          )}
        </div>

        {error && (
          <p className="text-xs text-red-500 font-medium mt-0.5">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
