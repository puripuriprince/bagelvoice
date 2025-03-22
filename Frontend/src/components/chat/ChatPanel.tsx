/**
 * ChatPanel.tsx
 *
 * The central panel component that displays the chat interface.
 * It shows a header with title and options, and the main chat area.
 * When no sources are added, it displays an empty state with instructions to add a source.
 */
'use client';

import { Button } from '@/components/ui/button';
import { Download, Filter, SlidersHorizontal } from 'lucide-react';
import EmptyState from '@/components/common/EmptyState';

export default function ChatPanel() {
  // This would be determined by whether sources have been added
  const hasNoSources = true;

  return (
    <div className="h-full flex flex-col">
      {/* Panel header with title and options */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <h2 className="text-sm font-medium text-zinc-200">Chat</h2>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <SlidersHorizontal size={16} />
            <span className="sr-only">Options</span>
          </Button>
        </div>
      </div>

      {/* Panel content */}
      <div className="flex-1 p-4 flex flex-col justify-center items-center">
        {hasNoSources ? (
          // Empty state when no sources added
          <div className="max-w-md mx-auto">
            <EmptyState
              icon={<Download size={48} className="text-zinc-600" />}
              title="Add a source to get started"
              description="Upload a file or add a website to have a conversation about it."
            />
          </div>
        ) : (
          // Chat interface would go here when sources are added
          <div className="w-full h-full flex flex-col">
            {/* Chat messages would go here */}
            <div className="flex-1">
              {/* Messages would be rendered here */}
            </div>

            {/* Input area */}
            <div className="p-4 border-t border-zinc-800">
              <div className="flex items-center p-2 border border-zinc-700 rounded-lg bg-zinc-800">
                <input
                  type="text"
                  placeholder="Upload a source to get started..."
                  disabled={hasNoSources}
                  className="flex-1 bg-transparent outline-none text-zinc-300 placeholder-zinc-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
