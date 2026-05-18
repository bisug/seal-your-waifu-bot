import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility for combining Tailwind classes cleanly with conflict resolution.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format large numbers with commas.
 */
export function formatNumber(num: number | string | null | undefined) {
  const value = typeof num === 'string' ? parseFloat(num) : num;
  return new Intl.NumberFormat().format(value || 0);
}
