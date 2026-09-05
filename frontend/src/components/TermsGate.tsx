import { ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { apiFetch } from '../api/client';
import { useUser } from '../context/UserContext';
import { Button } from './ui/Button';

const TERMS_SUMMARY = [
  {
    title: 'Digital Goods',
    body: 'Battle Pass purchases are digital items delivered in this bot. Paid passes not delivered within 48 hours are refundable via /paysupport.',
  },
  {
    title: 'Virtual Currency',
    body: 'Coins and Prisms are in-game currency with no real-money value. They cannot be purchased, sold, or exchanged for money.',
  },
  {
    title: 'Your Data',
    body: 'We store your Telegram ID, name, gameplay progress, and per-chat activity counts — never message content. You can erase everything anytime with /delete.',
  },
  {
    title: 'Fair Play',
    body: 'One account per person. Alt-account farming, automation, and exploiting bugs may result in a ban from the bot.',
  },
];

export const TermsGate = () => {
  const { user, refreshUser } = useUser();
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user?.terms_accepted) return null;

  const accept = async () => {
    setAccepting(true);
    setError(null);
    try {
      await apiFetch('/terms/accept', { method: 'POST' });
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('success');
      await refreshUser();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Could not save acceptance. Check your connection and try again.',
      );
    } finally {
      setAccepting(false);
    }
  };

  const decline = () => {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('error');
    try {
      window.Telegram?.WebApp?.close();
    } catch {
      // Outside Telegram (browser preview) there is nothing to close.
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm px-4 select-none">
      <div className="w-full max-w-sm rounded-lg border border-white/10 bg-zinc-900 shadow-2xl overflow-hidden max-h-[92svh] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.06] bg-white/[0.02] shrink-0">
          <div className="w-9 h-9 rounded-md bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shrink-0">
            <ShieldCheck size={16} className="text-brand-accent" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[13px] font-black text-zinc-100 uppercase tracking-wider leading-none">
              Welcome to SEAL
            </span>
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mt-1">
              Accept terms to continue
            </span>
          </div>
        </div>

        {/* Terms list */}
        <div className="overflow-y-auto overscroll-contain px-5 py-4 space-y-4 flex-1">
          {TERMS_SUMMARY.map((item) => (
            <div key={item.title} className="flex flex-col gap-1.5">
              <span className="text-[10px] font-black text-zinc-200 uppercase tracking-widest">
                {item.title}
              </span>
              <span className="text-[11px] text-zinc-400 leading-relaxed">{item.body}</span>
            </div>
          ))}
          <p className="text-[9px] text-zinc-600 leading-relaxed pt-1">
            Full terms: /terms in the bot. Privacy: /privacy. Copyright reports: /dmca.
          </p>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-white/[0.06] bg-white/[0.02] shrink-0 space-y-2">
          {error && <p className="text-[10px] text-red-400 font-medium">{error}</p>}
          <Button
            variant="accent"
            className="w-full h-11"
            onClick={accept}
            isLoading={accepting}
            disabled={accepting}
          >
            Accept & Continue
          </Button>
          <Button
            variant="ghost"
            className="w-full h-9"
            onClick={decline}
            disabled={accepting}
          >
            Decline & Close
          </Button>
          <p className="text-[8px] text-zinc-600 text-center uppercase tracking-widest font-bold">
            Required to use the app
          </p>
        </div>
      </div>
    </div>
  );
};
