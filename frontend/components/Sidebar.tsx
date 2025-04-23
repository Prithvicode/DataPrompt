"use client";

import { ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

interface SidebarProps {
  children: ReactNode;
  isOpen: boolean;
  onClose: () => void;
  header?: ReactNode;
  className?: string;
  defaultSize?: number; // percentage (e.g. 30 = 30% of screen)
}

export function Sidebar({
  children,
  isOpen,
  onClose,
  header,
  className,
  defaultSize = 50,
}: SidebarProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed top-0 right-0 h-full w-full z-50 flex">
      <ResizablePanelGroup direction="horizontal" className="dark">
        {/* Empty left space so sidebar is on the right */}
        <ResizablePanel
          defaultSize={100 - defaultSize}
          minSize={0}
          maxSize={100 - defaultSize}
        />

        {/* Drag handle between spacer and sidebar */}
        <ResizableHandle withHandle />

        {/* Sidebar panel */}
        <ResizablePanel
          defaultSize={defaultSize}
          minSize={20}
          maxSize={90}
          className={cn(
            "h-full flex flex-col bg-gray-900 border-l border-gray-800 shadow-lg",
            className
          )}
        >
          <div className="border-b border-gray-800 p-4 flex justify-between items-center bg-gray-900">
            {header || <div />}
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5 text-gray-300" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-gray-900">
            {children}
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
