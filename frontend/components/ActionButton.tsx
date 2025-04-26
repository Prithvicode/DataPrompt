"use client";

import { LucideIcon } from "lucide-react";
import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: LucideIcon;
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  iconOnly?: boolean;
  label?: string;
}

export function ActionButton({
  icon: Icon,
  variant = "primary",
  size = "md",
  iconOnly = true,
  label,
  className,
  ...props
}: ActionButtonProps) {
  const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
    secondary:
      "bg-gray-800 text-white hover:bg-gray-700 focus:ring-gray-500 ring-2 ring-gray-400",
    outline:
      "border border-gray-300 text-gray-900 hover:bg-gray-100 focus:ring-blue-500",
    ghost: "text-gray-900 hover:bg-gray-200 focus:ring-blue-500",
  };

  const sizeStyles = {
    sm: iconOnly ? "p-2" : "px-3 py-2 text-sm",
    md: iconOnly ? "p-3" : "px-4 py-3",
    lg: iconOnly ? "p-4" : "px-5 py-4 text-lg",
  };

  const iconSizeStyles = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
  };

  return (
    <button
      className={cn(
        "rounded-full transition-all shadow-sm hover:shadow-md focus:outline-none focus:ring-2",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      aria-label={label || "Action button"}
      {...props}
    >
      <div className="flex items-center justify-center gap-2">
        <Icon className={iconSizeStyles[size]} />
        {!iconOnly && label && <span>{label}</span>}
      </div>
    </button>
  );
}
