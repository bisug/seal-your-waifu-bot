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

export function cleanRarityLabel(rarity: string) {
  return rarity
    .replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '')
    .trim();
}
