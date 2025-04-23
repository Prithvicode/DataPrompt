// components/ui/EmptyState.tsx
"use client";

import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  iconColor?: string;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  iconColor = "text-blue-400",
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center px-4",
        className
      )}
    >
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-4">
          <Icon className={cn("h-12 w-12 mx-auto opacity-80", iconColor)} />
          <h2 className="text-2xl font-semibold">{title}</h2>
          {description && <p className="text-gray-400 mb-8">{description}</p>}
        </div>

        {action && <div className="mt-6">{action}</div>}
      </div>
    </div>
  );
}
