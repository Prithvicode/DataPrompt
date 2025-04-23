// components/ui/IconHeader.tsx
"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface IconHeaderProps {
  icon: LucideIcon;
  text: string;
  iconColor?: string;
  className?: string;
}

export function IconHeader({
  icon: Icon,
  text,
  iconColor = "text-blue-400",
  className,
}: IconHeaderProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Icon className={cn("h-5 w-5", iconColor)} />
      <h2 className="font-semibold text-lg">{text}</h2>
    </div>
  );
}
