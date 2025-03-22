/**
 * StudioPanel.tsx
 *
 * The right panel component that displays the audio studio options and notes.
 * It includes sections for audio overview and notes.
 * Each section can have its own functionality and empty states.
 */
'use client';

import { Button } from '@/components/ui/button';
import { Info, Plus, BookText, Headphones } from 'lucide-react';
import { NotepadText } from '@/components/common/CustomIcons';
import EmptyState from '@/components/common/EmptyState';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

export default function StudioPanel() {
  return (
    <div className="h-full flex flex-col">
      {/* Panel header with title */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <h2 className="text-sm font-medium text-zinc-200">Studio</h2>
      </div>

      {/* Panel content */}
      <div className="flex-1 overflow-y-auto">
        {/* Audio Overview Section */}
        <div className="p-4 border-b border-zinc-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-zinc-200">Audio Overview</h3>
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <Info size={14} className="text-zinc-400" />
              <span className="sr-only">Info</span>
            </Button>
          </div>

          {/* Deep Dive Conversation Card */}
          <Card className="bg-zinc-800 border-zinc-700 p-4">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-md bg-zinc-700 flex items-center justify-center">
                <Headphones size={16} className="text-zinc-300" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-zinc-100">Deep Dive conversation</h4>
                <p className="text-xs text-zinc-400 mt-1">Two hosts (English only)</p>

                <div className="grid grid-cols-2 gap-2 mt-4">
                  <Button variant="secondary" size="sm" className="h-8 text-xs">
                    Customize
                  </Button>
                  <Button size="sm" className="h-8 text-xs">
                    Generate
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Notes Section */}
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-zinc-200">Notes</h3>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="1" />
                <circle cx="12" cy="5" r="1" />
                <circle cx="12" cy="19" r="1" />
              </svg>
              <span className="sr-only">More</span>
            </Button>
          </div>

          {/* Add Note Button */}
          <Button
            variant="outline"
            className="w-full mb-4 border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
          >
            <Plus size={16} className="mr-2" />
            Add note
          </Button>

          {/* Note Type Buttons */}
          <div className="grid grid-cols-2 gap-2 mb-4">
            <Button
              variant="outline"
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 justify-start"
              size="sm"
            >
              <BookText size={14} className="mr-2" />
              <span className="text-xs">Study guide</span>
            </Button>
            <Button
              variant="outline"
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 justify-start"
              size="sm"
            >
              <NotepadText size={14} className="mr-2" />
              <span className="text-xs">Briefing doc</span>
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 justify-start"
              size="sm"
            >
              <BookText size={14} className="mr-2" />
              <span className="text-xs">FAQ</span>
            </Button>
            <Button
              variant="outline"
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 justify-start"
              size="sm"
            >
              <NotepadText size={14} className="mr-2" />
              <span className="text-xs">Timeline</span>
            </Button>
          </div>

          {/* Empty Notes State */}
          <div className="mt-8">
            <EmptyState
              icon={<BookText size={48} className="text-zinc-600" />}
              title="Saved notes will appear here"
              description="Save a chat message to create a new note, or click Add note above."
            />
          </div>
        </div>
      </div>
    </div>
  );
}
