import Image from "next/image";
import { cn } from "../../lib/utils";

export interface LogoProps {
  /** Size of the logo */
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  /** Theme context: dark background uses white logo, light background uses original colored logo */
  theme?: "dark" | "light";
  className?: string;
  textClassName?: string;
}

export function Logo({ size = "md", theme = "light", className, textClassName }: LogoProps) {
  const sizeMap = {
    xs: { img: 24, text: "text-lg", ml: "-ml-0.5" },
    sm: { img: 32, text: "text-2xl", ml: "-ml-0.5" },
    md: { img: 40, text: "text-3xl", ml: "-ml-1" },
    lg: { img: 56, text: "text-4xl", ml: "-ml-1" },
    xl: { img: 64, text: "text-5xl", ml: "-ml-1" },
  };

  const currentSize = sizeMap[size];

  return (
    <div className={cn("flex items-center", className)}>
      <Image 
        src="/lanes-logo/lanes-logo.svg" 
        alt="LANES Logo" 
        width={currentSize.img} 
        height={currentSize.img} 
        priority
        className={cn(
          "object-contain drop-shadow-sm", 
          theme === "dark" && "brightness-0 invert drop-shadow-md"
        )} 
      />
      <span 
        className={cn(
          "font-bold tracking-tight",
          currentSize.ml,
          currentSize.text,
          theme === "dark" ? "text-white drop-shadow-md" : "text-slate-900",
          textClassName
        )}
      >
        ANES
      </span>
    </div>
  );
}
