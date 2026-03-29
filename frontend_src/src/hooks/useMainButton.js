import { useEffect, useCallback } from 'react';

/**
 * Custom hook for managing the Telegram WebApp MainButton.
 * Handles visibility, text, color, and tap events with automatic cleanup.
 */
export const useMainButton = (options = {}) => {
  const tg = window.Telegram?.WebApp;
  const mainButton = tg?.MainButton;

  const show = useCallback((text, onClick, color = '#00f2ff', textColor = '#080a12') => {
    if (!mainButton) return;

    mainButton.setText(text.toUpperCase());
    mainButton.setParams({
      color: color,
      text_color: textColor,
      is_visible: true,
      is_active: true
    });

    // Handle click with global event listener to avoid stale closure issues
    const handleClick = () => {
      tg.HapticFeedback?.impactOccurred('medium');
      if (onClick) onClick();
    };

    mainButton.onClick(handleClick);
    
    return () => {
      mainButton.offClick(handleClick);
    };
  }, [mainButton, tg]);

  const hide = useCallback(() => {
    if (!mainButton) return;
    mainButton.hide();
  }, [mainButton]);

  const setProgress = useCallback((isLoading) => {
    if (!mainButton) return;
    if (isLoading) {
      mainButton.showProgress(false);
    } else {
      mainButton.hideProgress();
    }
  }, [mainButton]);

  // Comprehensive Cleanup on unmount or route change
  useEffect(() => {
    return () => {
      if (mainButton) {
        mainButton.hide();
        mainButton.hideProgress();
      }
    };
  }, [mainButton]);

  return { show, hide, setProgress, isVisible: mainButton?.isVisible };
};
