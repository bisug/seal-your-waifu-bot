import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility for combining Tailwind classes cleanly with conflict resolution.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Format large numbers with commas.
 */
export function formatNumber(num) {
  return new Intl.NumberFormat().format(num || 0);
}
