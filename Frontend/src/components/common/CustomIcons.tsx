/**
 * CustomIcons.tsx
 *
 * Contains custom icon components that aren't available in Lucide.
 * These are built as SVG components following the same pattern as Lucide icons.
 */
import { LucideProps } from 'lucide-react';

export function NotepadText(props: LucideProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M8 2v4" />
      <path d="M12 2v4" />
      <path d="M16 2v4" />
      <rect width="16" height="18" x="4" y="4" rx="2" />
      <path d="M8 10h8" />
      <path d="M8 14h4" />
      <path d="M8 18h2" />
    </svg>
  );
}

export function MicVocal(props: LucideProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="8" r="4" />
      <path d="M12 16v4" />
      <path d="M8 22h8" />
      <path d="M18 8c0 4.56-1.48 8.4-3.5 10" />
      <path d="M6 8c0 4.56 1.48 8.4 3.5 10" />
    </svg>
  );
}
