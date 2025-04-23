// components/ui/Header.tsx
"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  leftContent: ReactNode;
  rightContent?: ReactNode;
  className?: string;
  borderBottom?: boolean;
}

export function Header({
  leftContent,
  rightContent,
  className,
  borderBottom = true,
}: HeaderProps) {
  return (
    <div
      className={cn(
        "py-3 px-4 flex items-center justify-between bg-gray-950",
        borderBottom && "border-b border-gray-800",
        className
      )}
    >
      <div className="flex items-center gap-2">{leftContent}</div>
      {rightContent && <div className="flex items-center">{rightContent}</div>}
    </div>
  );
}
