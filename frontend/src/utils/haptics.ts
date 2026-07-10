/**
 * Utility for Telegram WebApp Haptic Feedback
 */

export const haptics = {
  /**
   * Triggers a light impact haptic feedback
   */
  light: () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
  },

  /**
   * Triggers a medium impact haptic feedback
   */
  medium: () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
  },

  /**
   * Triggers a heavy impact haptic feedback
   */
  heavy: () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('heavy');
  },

  /**
   * Triggers a rigid impact haptic feedback
   */
  rigid: () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('rigid');
  },

  /**
   * Triggers a soft impact haptic feedback
   */
  soft: () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('soft');
  },

  /**
   * Triggers a notification haptic feedback
   */
  notification: (type: 'error' | 'success' | 'warning') => {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  },

  /**
   * Triggers a selection changed haptic feedback
   */
  selection: () => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
  }
};
