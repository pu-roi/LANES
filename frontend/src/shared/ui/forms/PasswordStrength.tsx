import React from "react";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface PasswordStrengthProps {
  password?: string;
  className?: string;
}

export function PasswordStrength({ password = "", className }: PasswordStrengthProps) {
  const requirements = [
    {
      id: "length",
      text: "At least 6 characters long",
      met: password.length >= 6,
    },
    {
      id: "no-spaces",
      text: "No spaces allowed",
      met: password.length > 0 && !/\s/.test(password),
    },
    {
      id: "cases",
      text: "One uppercase & one lowercase letter",
      met: /(?=.*[a-z])(?=.*[A-Z])/.test(password),
    },
    {
      id: "special",
      text: "One number & one special character",
      met: /(?=.*\d)(?=.*[^a-zA-Z\d\s])/.test(password),
    },
  ];

  if (!password) {
    return null;
  }

  return (
    <div className={cn("mt-2 flex flex-col gap-1.5 p-3 bg-slate-50 border border-slate-100 rounded-lg", className)}>
      <p className="text-xs font-semibold text-slate-600 mb-1">Password Requirements:</p>
      {requirements.map((req) => (
        <div 
          key={req.id} 
          className={cn(
            "flex items-center gap-2 text-xs transition-colors duration-300",
            req.met ? "text-emerald-600 font-medium" : "text-slate-500"
          )}
        >
          {req.met ? (
            <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
          ) : (
            <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          )}
          <span>{req.text}</span>
        </div>
      ))}
    </div>
  );
}
