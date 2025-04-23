// components/ui/Card.tsx
"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  clickable?: boolean;
  bordered?: boolean;
  onClick?: () => void;
}

export function Card({
  children,
  className,
  hoverable = false,
  clickable = false,
  bordered = true,
  onClick,
}: CardProps) {
  return (
    <div
      className={cn(
        "p-3 rounded-lg",
        bordered && "border border-gray-800",
        hoverable && "hover:border-blue-500 hover:bg-gray-900 transition-all",
        clickable && "cursor-pointer",
        className
      )}
      onClick={clickable ? onClick : undefined}
      role={clickable ? "button" : undefined}
    >
      {children}
    </div>
  );
}
