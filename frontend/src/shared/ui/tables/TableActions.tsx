import React from "react";
import { Button, ButtonProps } from "../forms/Button";
import { Trash2, Edit2, Download, RefreshCw, CheckCircle, XCircle, UserCheck, UserX, ShieldOff } from "lucide-react";

export type ActionVariant = "delete" | "edit" | "download" | "restore" | "approve" | "reject" | "enable" | "disable" | "default";

interface TableActionButtonProps extends Omit<ButtonProps, "variant"> {
  actionVariant: ActionVariant;
  icon?: React.ElementType;
}

export function TableActionButton({ actionVariant, icon: Icon, className = "", children, ...props }: TableActionButtonProps) {
  let defaultIcon: React.ElementType | null = null;
  let variantClasses = "";

  switch (actionVariant) {
    case "delete":
    case "reject":
      defaultIcon = actionVariant === "delete" ? Trash2 : XCircle;
      variantClasses = "text-red-600 border-red-100 hover:bg-red-50 hover:border-red-200 hover:text-red-700";
      break;
    case "approve":
    case "enable":
      defaultIcon = actionVariant === "approve" ? CheckCircle : UserCheck;
      variantClasses = "text-emerald-600 border-emerald-100 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700";
      break;
    case "edit":
      defaultIcon = Edit2;
      variantClasses = "text-blue-600 border-blue-100 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700";
      break;
    case "download":
      defaultIcon = Download;
      variantClasses = "text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300 hover:text-slate-800";
      break;
    case "restore":
      defaultIcon = RefreshCw;
      variantClasses = "text-amber-600 border-amber-100 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700";
      break;
    case "disable":
      defaultIcon = actionVariant === "disable" ? UserX : ShieldOff;
      variantClasses = "text-amber-600 border-amber-100 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700";
      break;
    default:
      variantClasses = "text-slate-600 border-slate-200 hover:bg-slate-50";
  }

  const DisplayIcon = Icon || defaultIcon;

  return (
    <Button
      variant="outline"
      size="sm"
      className={`text-xs px-2.5 py-1.5 h-auto font-medium flex items-center gap-1.5 shadow-sm transition-colors ${variantClasses} ${className}`}
      {...props}
    >
      {DisplayIcon && <DisplayIcon className="w-3.5 h-3.5" />}
      {children}
    </Button>
  );
}

export function TableActionGroup({ children, className = "" }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={`flex items-center justify-end gap-2 ${className}`}>
      {children}
    </div>
  );
}
