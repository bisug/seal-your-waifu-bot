import { useEffect, useState } from 'react';

const WS_PATH = `/api/${import.meta.env.VITE_API_PREFIX ?? 'v1_7b82'}/ws/leaderboard`;

/**
 * Shared WebSocket liveness probe. Connects to the leaderboard WS channel
 * (same channel Leaderboard.tsx uses) purely to detect backend reachability.
 * Reconnects every 10s on drop; auto-cleans on unmount.
 */
export const useLiveStatus = () => {
  const [live, setLive] = useState(false);

  useEffect(() => {
    const token = sessionStorage.getItem('auth_token');
    if (!token) return;

    const apiBase = import.meta.env.VITE_API_URL ?? '';
    const wsUrl = `${apiBase.replace(/^http/, 'ws')}${WS_PATH}`;

    let ws: WebSocket | null = null;
    let closedByUs = false;
    let reconnectTimer: number | undefined;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl, [`seal-token.${token}`]);
      } catch {
        return;
      }
      ws.onopen = () => setLive(true);
      ws.onclose = () => {
        setLive(false);
        if (!closedByUs) reconnectTimer = window.setTimeout(connect, 10000);
      };
      ws.onerror = () => ws?.close();
    };

    connect();

    return () => {
      closedByUs = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  return live;
};
