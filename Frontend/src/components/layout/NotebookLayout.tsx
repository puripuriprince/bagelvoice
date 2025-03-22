/**
 * NotebookLayout.tsx
 *
 * Main layout component that structures the entire NotebookLM interface.
 * It divides the screen into three main panels (Sources, Chat, and Studio)
 * and implements the header with controls.
 */
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Settings, Share, BarChart2, Plus, Menu } from 'lucide-react';
import dynamic from 'next/dynamic';

// Use dynamic imports to resolve circular dependencies
const SourcesPanel = dynamic(() => import('@/components/sources/SourcesPanel'), { ssr: false });
const ChatPanel = dynamic(() => import('@/components/chat/ChatPanel'), { ssr: false });
const StudioPanel = dynamic(() => import('@/components/studio/StudioPanel'), { ssr: false });

export default function NotebookLayout() {
  // State for responsive design (mobile view control)
  const [mobilePanel, setMobilePanel] = useState<'sources' | 'chat' | 'studio'>('chat');

  return (
    <div className="flex flex-col h-screen">
      {/* Header with title and controls */}
      <header className="flex items-center px-4 py-2 bg-zinc-900 border-b border-zinc-800">
        {/* Logo and title area */}
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
            +
          </div>
          <h1 className="font-medium text-zinc-100">Untitled notebook</h1>
        </div>

        {/* Controls on the right side */}
        <div className="ml-auto flex items-center space-x-2">
          <Button variant="ghost" size="icon">
            <BarChart2 size={18} className="text-zinc-400" />
            <span className="sr-only">Analytics</span>
          </Button>
          <Button variant="ghost" size="icon">
            <Share size={18} className="text-zinc-400" />
            <span className="sr-only">Share</span>
          </Button>
          <Button variant="ghost" size="icon">
            <Settings size={18} className="text-zinc-400" />
            <span className="sr-only">Settings</span>
          </Button>
          <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white">
            L
          </div>
        </div>
      </header>

      {/* Mobile panel selector - only visible on small screens */}
      <div className="md:hidden flex border-b border-zinc-800">
        <button
          className={`flex-1 p-2 text-center ${mobilePanel === 'sources' ? 'border-b-2 border-blue-500' : ''}`}
          onClick={() => setMobilePanel('sources')}
        >
          Sources
        </button>
        <button
          className={`flex-1 p-2 text-center ${mobilePanel === 'chat' ? 'border-b-2 border-blue-500' : ''}`}
          onClick={() => setMobilePanel('chat')}
        >
          Chat
        </button>
        <button
          className={`flex-1 p-2 text-center ${mobilePanel === 'studio' ? 'border-b-2 border-blue-500' : ''}`}
          onClick={() => setMobilePanel('studio')}
        >
          Studio
        </button>
      </div>

      {/* Main three-panel layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Sources */}
        <div className={`w-80 border-r border-zinc-800 overflow-y-auto panel-scroll
                        ${mobilePanel === 'sources' ? 'block' : 'hidden'} md:block`}>
          <SourcesPanel />
        </div>

        {/* Middle panel - Chat */}
        <div className={`flex-1 overflow-y-auto panel-scroll
                        ${mobilePanel === 'chat' ? 'block' : 'hidden'} md:block`}>
          <ChatPanel />
        </div>

        {/* Right panel - Studio */}
        <div className={`w-80 border-l border-zinc-800 overflow-y-auto panel-scroll
                        ${mobilePanel === 'studio' ? 'block' : 'hidden'} md:block`}>
          <StudioPanel />
        </div>
      </div>
    </div>
  );
}
