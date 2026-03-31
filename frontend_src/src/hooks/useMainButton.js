import { useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for managing the Telegram WebApp MainButton.
 * Handles visibility, text, color, and tap events with automatic cleanup.
 */
export const useMainButton = () => {
  const handlerRef = useRef(null);

  const getButton = () => window.Telegram?.WebApp?.MainButton;
  const getTg = () => window.Telegram?.WebApp;

  const show = useCallback((text, onClick, color = '#00f2ff', textColor = '#080a12') => {
    const mainButton = getButton();
    if (!mainButton) return;

    try {
      // Clean up previous handler before adding new one
      if (handlerRef.current) {
        mainButton.offClick(handlerRef.current);
      }

      const handleClick = () => {
        getTg()?.HapticFeedback?.impactOccurred('medium');
        if (onClick) onClick();
      };

      handlerRef.current = handleClick;
      mainButton.setText(text.toUpperCase());
      mainButton.setParams({
        color,
        text_color: textColor,
        is_visible: true,
        is_active: true,
      });
      mainButton.onClick(handleClick);
    } catch (e) {
      console.warn('MainButton error:', e.message);
    }
  }, []);

  const hide = useCallback(() => {
    const mainButton = getButton();
    if (!mainButton) return;
    try {
      if (handlerRef.current) {
        mainButton.offClick(handlerRef.current);
        handlerRef.current = null;
      }
      mainButton.hide();
    } catch (e) {
      console.warn('MainButton hide error:', e.message);
    }
  }, []);

  const setProgress = useCallback((isLoading) => {
    const mainButton = getButton();
    if (!mainButton) return;
    try {
      if (isLoading) mainButton.showProgress(false);
      else mainButton.hideProgress();
    } catch (e) {
      console.warn('MainButton progress error:', e.message);
    }
  }, []);

  // Comprehensive cleanup on unmount
  useEffect(() => {
    return () => {
      const mainButton = getButton();
      if (!mainButton) return;
      try {
        if (handlerRef.current) mainButton.offClick(handlerRef.current);
        mainButton.hide();
        mainButton.hideProgress();
      } catch (e) {
        // ignore
      }
    };
  }, []);

  return { show, hide, setProgress, isVisible: getButton()?.isVisible };
};
