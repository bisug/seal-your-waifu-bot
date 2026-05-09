import { useState, useCallback } from 'react';
import { apiFetch } from '../api';
import { useUser } from '../context/UserContext';
import { useToast } from '../components/UI';

export const useEggActions = () => {
  const { refreshUser } = useUser();
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [hatchingResult, setHatchingResult] = useState(null);

  const incubateEgg = useCallback(async (eggId) => {
    const tg = window.Telegram?.WebApp;
    tg?.HapticFeedback?.impactOccurred('medium');
    setLoading(true);
    try {
      await apiFetch(`/eggs/incubate/${eggId}`, { method: 'POST' });
      addToast('Incubation Matrix Active', 'success');
      await refreshUser();
      return true;
    } catch (err) {
      tg?.HapticFeedback?.notificationOccurred('error');
      const msg = err.message || 'Calibration failure';
      if (tg?.showAlert) tg.showAlert(msg);
      else addToast(msg, 'error');
      return false;
    } finally {
      setLoading(false);
    }
  }, [refreshUser]);

  const hatchEgg = useCallback(async (eggId) => {
    const tg = window.Telegram?.WebApp;
    tg?.HapticFeedback?.impactOccurred('heavy');
    setLoading(true);
    try {
      const res = await apiFetch(`/eggs/hatch/${eggId}`, { method: 'POST' });
      if (res.status === 'success') {
        tg?.HapticFeedback?.notificationOccurred('success');
        setHatchingResult(res.character);
        addToast('Lifeform Detected', 'success');
        await refreshUser();
        return res.character;
      } else {
        tg?.HapticFeedback?.notificationOccurred('error');
        const msg = res.message || 'Incubation Failure';
        if (tg?.showAlert) tg.showAlert(msg);
        else addToast(msg, 'error');
        return null;
      }
    } catch (err) {
      tg?.HapticFeedback?.notificationOccurred('error');
      const msg = err.message || 'Hatch protocol interrupted';
      if (tg?.showAlert) tg.showAlert(msg);
      else addToast(msg, 'error');
      return null;
    } finally {
      setLoading(false);
    }
  }, [refreshUser]);

  return {
    incubateEgg,
    hatchEgg,
    loading,
    hatchingResult,
    setHatchingResult
  };
};
