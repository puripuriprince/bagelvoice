/**
 * EmptyState.tsx
 *
 * A reusable empty state component used across the application.
 * It displays an icon, title, and description for empty areas.
 * Used in various panels when no content is available.
 */
import { ReactNode } from 'react';

type EmptyStateProps = {
  icon: ReactNode;
  title: string;
  description: string;
};

export default function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-8">
      <div className="mb-4">
        {icon}
      </div>
      <h3 className="text-sm font-medium text-zinc-100 mb-2">{title}</h3>
      <p className="text-xs text-zinc-400 max-w-xs">{description}</p>
    </div>
  );
}
