import React, { InputHTMLAttributes, forwardRef, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ChevronUp, ChevronDown } from "lucide-react";

export interface NumberInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightAddon?: ReactNode;
  containerClassName?: string;
  onIncrement?: () => void;
  onDecrement?: () => void;
}

export const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(
  ({ className, containerClassName, label, error, leftIcon, rightAddon, onIncrement, onDecrement, ...props }, forwardedRef) => {
    
    const internalRef = React.useRef<HTMLInputElement>(null);
    
    const setRefs = React.useCallback(
      (node: HTMLInputElement) => {
        internalRef.current = node;
        if (typeof forwardedRef === 'function') {
          forwardedRef(node);
        } else if (forwardedRef) {
          (forwardedRef as React.MutableRefObject<HTMLInputElement | null>).current = node;
        }
      },
      [forwardedRef]
    );

    const triggerReactChange = (node: HTMLInputElement) => {
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value'
      )?.set;
      
      const currentValue = node.value;
      nativeInputValueSetter?.call(node, currentValue);
      node.dispatchEvent(new Event('input', { bubbles: true }));
    };
    
    const handleIncrement = (e: React.MouseEvent) => {
      e.preventDefault();
      if (onIncrement) {
        onIncrement();
      } else if (internalRef.current) {
        internalRef.current.stepUp();
        triggerReactChange(internalRef.current);
      }
    };
    
    const handleDecrement = (e: React.MouseEvent) => {
      e.preventDefault();
      if (onDecrement) {
        onDecrement();
      } else if (internalRef.current) {
        internalRef.current.stepDown();
        triggerReactChange(internalRef.current);
      }
    };

    return (
      <div className={cn("w-full flex flex-col gap-1", containerClassName)}>
        {label && (
          <label className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        
        <div className="flex items-center gap-2">
          <div className="relative w-full">
            {leftIcon && (
              <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none text-gray-500">
                {leftIcon}
              </div>
            )}
            
            <div className="relative flex items-center">
              <input
                type="number"
                className={cn(
                  "flex w-full rounded-lg border bg-white px-3 py-2 text-sm text-gray-900",
                  "placeholder:text-gray-400 shadow-sm outline-none transition-all duration-200",
                  "focus:border-blue-500 focus:ring-2 focus:ring-blue-100",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none",
                  error ? "border-red-500 focus:border-red-500 focus:ring-red-100 ring-red-100" : "border-gray-200 hover:border-gray-300",
                  leftIcon ? "pl-10" : "",
                  "pr-8", // Make room for custom spinners
                  className
                )}
                ref={setRefs}
                {...props}
              />
              
              {/* Custom Spin Buttons */}
              <div className="absolute right-1 flex flex-col h-full py-1">
                <button
                  type="button"
                  onClick={handleIncrement}
                  disabled={props.disabled}
                  className="flex flex-1 items-center justify-center rounded px-1 hover:bg-gray-100 text-gray-500 disabled:opacity-50"
                  tabIndex={-1}
                >
                  <ChevronUp className="h-3 w-3" />
                </button>
                <button
                  type="button"
                  onClick={handleDecrement}
                  disabled={props.disabled}
                  className="flex flex-1 items-center justify-center rounded px-1 hover:bg-gray-100 text-gray-500 disabled:opacity-50"
                  tabIndex={-1}
                >
                  <ChevronDown className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
          
          {rightAddon && (
            <div className="text-sm text-gray-600 whitespace-nowrap">
              {rightAddon}
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

NumberInput.displayName = "NumberInput";
