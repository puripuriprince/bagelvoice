/**
 * SourcesPanel.tsx
 *
 * The left panel component that displays sources added to the notebook.
 * It shows a header with title, add button, and the list of sources.
 * When no sources are added, it displays an empty state with instructions.
 */
"use client";

import { Button } from "@/components/ui/button";
import { Plus, Upload, File } from "lucide-react";
import { Card } from "@/components/ui/card";
import EmptyState from "@/components/common/EmptyState";

export default function SourcesPanel() {
  return (
    <div className="h-full flex flex-col">
      {/* Panel header with title and add button */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <h2 className="text-sm font-medium text-zinc-200">Sources</h2>
        <Button variant="ghost" size="sm" className="h-8 px-2">
          <Plus size={16} className="mr-1" />
          <span className="text-xs">Add source</span>
        </Button>
      </div>

      {/* Panel content - empty state */}
      <div className="flex-1 p-4">
        <EmptyState
          icon={<File size={48} className="text-zinc-600" />}
          title="Saved sources will appear here"
          description="Click Add source above to add PDFs, websites, text, videos, or audio files. Or import a file directly from Google Drive."
        />

        {/* Upload source button */}
        <div className="mt-4">
          <Button
            variant="outline"
            className="w-full border-zinc-700 text-black hover:bg-zinc-800 hover:text-zinc-100"
          >
            <Upload size={16} className="mr-2" />
            Upload a source
          </Button>
        </div>
      </div>
    </div>
  );
}
