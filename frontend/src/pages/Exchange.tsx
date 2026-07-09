import React, { useMemo, useState } from 'react';
import { AlertCircle, BadgePercent, CheckCircle2, Coins, Gem, Loader2, RefreshCw, Repeat2, Target, Zap, ArrowRight, TrendingUp } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useApi } from '../hooks/useApi';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { Card } from '../components/ui/Card';
import { useToast } from '../components/ui/Toast';
import { useUser } from '../context/UserContext';
import { cn, formatNumber } from '../utils';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { motion, AnimatePresence } from 'framer-motion';

type ExchangeMode = 'shards_to_zenith' | 'zenith_to_shards';

interface ExchangeData {
  balance: number;
  zenith: number;
  rate: number;
  minimum_shards: number;
  minimum_zenith: number;
}

const getModeCopy = (mode: ExchangeMode) => {
  if (mode === 'shards_to_zenith') {
    return {
      inputLabel: 'CREDIT SHARDS',
      outputLabel: 'ZENITH ASSETS',
      activeText: 'Shards to Zenith',
    };
  }

  return {
    inputLabel: 'ZENITH ASSETS',
    outputLabel: 'CREDIT SHARDS',
    activeText: 'Zenith to Shards',
  };
};

const toPositiveNumber = (value: unknown, fallback: number) => {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) && numberValue > 0 ? numberValue : fallback;
};

export const Exchange = () => {
  const { user, refreshUser } = useUser();
  const { addToast } = useToast();
  const { data, loading, error, execute: fetchExchange } = useApi<ExchangeData>('/shop/exchange');
  const [mode, setMode] = useState<ExchangeMode>('shards_to_zenith');
  const [amount, setAmount] = useState('10000');
  const [exchanging, setExchanging] = useState(false);

  const shardBalance = Math.max(0, Math.floor(Number(data?.balance ?? user?.balance ?? 0) || 0));
  const zenithBalance = Math.max(0, Math.floor(Number(data?.zenith ?? user?.stats?.zenith ?? user?.zenith ?? 0) || 0));
  const rate = Math.floor(toPositiveNumber(data?.rate, 10000));
  const minimumShards = Math.floor(toPositiveNumber(data?.minimum_shards, rate));
  const minimumZenith = Math.floor(toPositiveNumber(data?.minimum_zenith, 1));
  const rawAmount = amount.trim();
  const parsedAmount = Number(rawAmount);
  const hasValidAmount = rawAmount.length > 0 && Number.isFinite(parsedAmount) && parsedAmount > 0 && Number.isInteger(parsedAmount);
  const amountNumber = hasValidAmount ? parsedAmount : 0;
  const copy = getModeCopy(mode);
  const isShardMode = mode === 'shards_to_zenith';
  const outputAmount = isShardMode
    ? Math.floor(amountNumber / rate)
    : amountNumber * rate;
  const minimumInputAmount = isShardMode ? minimumShards : minimumZenith;
  const maxInputAmount = isShardMode
    ? Math.floor(shardBalance / rate) * rate
    : zenithBalance;
  const canUseMax = maxInputAmount >= minimumInputAmount;

  const validationMessage = useMemo(() => {
    if (!rawAmount) return 'Enter exchange amount';
    if (!hasValidAmount) return 'Enter a positive integer';

    if (isShardMode) {
      if (amountNumber < minimumShards) return `Minimum: ${formatNumber(minimumShards)} Shards`;
      if (amountNumber % rate !== 0) return `Multiplier: ${formatNumber(rate)} Shards`;
      if (shardBalance < amountNumber) return 'Insufficient Shards';
      return null;
    }

    if (amountNumber < minimumZenith) return `Minimum: ${formatNumber(minimumZenith)} Zenith`;
    if (zenithBalance < amountNumber) return 'Insufficient Zenith';
    return null;
  }, [amountNumber, hasValidAmount, isShardMode, minimumShards, minimumZenith, rate, rawAmount, shardBalance, zenithBalance]);

  const canExchange = !validationMessage && outputAmount > 0;
  const presetOptions = useMemo(() => {
    const baseOptions = isShardMode
      ? [
          { label: '1 ZENITH', amount: rate },
          { label: '5 ZENITH', amount: rate * 5 },
          { label: '10 ZENITH', amount: rate * 10 },
        ]
      : [
          { label: '1 ZENITH', amount: 1 },
          { label: '5 ZENITH', amount: 5 },
          { label: '10 ZENITH', amount: 10 },
        ];
    const options = [...baseOptions, { label: 'MAX ASSETS', amount: maxInputAmount }];
    const seen = new Set<number>();

    return options
      .map((option) => ({ ...option, amount: Math.floor(option.amount) }))
      .filter((option) => {
        if (!Number.isFinite(option.amount) || option.amount <= 0 || seen.has(option.amount)) return false;
        seen.add(option.amount);
        return true;
      });
  }, [isShardMode, maxInputAmount, rate]);

  const handleRefresh = async () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    await Promise.allSettled([fetchExchange(), refreshUser()]);
  };

  const handleModeChange = (nextMode: ExchangeMode) => {
    setMode(nextMode);
    setAmount(nextMode === 'shards_to_zenith' ? String(rate) : String(minimumZenith));
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
  };

  const handleSwapMode = () => {
    handleModeChange(isShardMode ? 'zenith_to_shards' : 'shards_to_zenith');
  };

  const setPreset = (presetAmount: number) => {
    setAmount(String(presetAmount));
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
  };

  const handleAmountChange = (value: string) => {
    setAmount(value.replace(/\D/g, ''));
  };

  const handleExchange = async () => {
    if (!canExchange || exchanging) return;

    setExchanging(true);
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    try {
      const result = await apiFetch(`/shop/exchange/${mode}?amount=${amountNumber}`, { method: 'POST' });
      addToast(result.message || 'Transaction executed successfully.', 'success');
      await Promise.allSettled([fetchExchange(), refreshUser()]);
      window.dispatchEvent(new Event('shop-refresh'));
    } catch (err: any) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setExchanging(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10">
        <div className="flex flex-col gap-2">
           <Skeleton className="h-10 w-48 rounded-lg" />
           <Skeleton className="h-4 w-64 rounded-lg opacity-50" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((item) => <Skeleton key={item} className="h-20 rounded-2xl" />)}
        </div>
        <Skeleton className="h-96 rounded-[32px]" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px">
        <ErrorState message={error} onAction={fetchExchange} />
      </div>
    );
  }

  return (
    <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10 select-none">
      <header className="space-y-8">
        <div className="flex items-start justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                    <Repeat2 size={26} className="text-brand-accent" />
               </div>
               <div className="flex flex-col gap-1">
                  <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Exchange</h1>
                  <div className="flex items-center gap-2">
                     <Target size={11} className="text-neutral-600" />
                     <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                       ASSET CONVERSION TERMINAL
                     </p>
                  </div>
               </div>
            </div>
          </div>

          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={loading || exchanging}
            className="w-12 h-12 p-0 rounded-2xl border-white/5 shadow-xl active:scale-95"
            aria-label="Refresh data"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </Button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[
              { icon: Coins, label: 'Shards', value: formatNumber(shardBalance), variant: 'default' },
              { icon: Gem, label: 'Zenith', value: formatNumber(zenithBalance), variant: 'primary' },
              { icon: BadgePercent, label: 'Protocol Rate', value: `${formatNumber(rate)}:1`, variant: 'success' },
          ].map((metric, i) => (
            <Card key={i} variant="tactical" className="p-4 border-white/[0.04] bg-white/[0.01]">
              <div className="flex items-center gap-2 mb-2">
                <metric.icon size={12} className={cn(
                    metric.variant === 'primary' ? 'text-brand-accent' :
                    metric.variant === 'success' ? 'text-success' : 'text-neutral-600'
                )} />
                <span className="text-[9px] font-black text-neutral-600 uppercase tracking-widest leading-none">{metric.label}</span>
              </div>
              <p className="text-sm font-black text-white stats-value tabular-nums leading-none">{metric.value}</p>
            </Card>
          ))}
        </div>

        {(error || data) && (
          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-3 p-4 rounded-2xl border border-warning/10 bg-warning/[0.03] text-[10px] font-black uppercase tracking-widest text-warning/80">
                <AlertCircle size={16} className="shrink-0" />
                <span className="leading-relaxed">LOCAL CACHE DETECTED. REFRESH TO SYNCHRONIZE PROTOCOL BALANCES.</span>
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </header>

      <section className="space-y-6">
        <Card variant="tactical" className="p-8 space-y-10 rounded-[32px] border-white/[0.06] bg-white/[0.01] shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-[0.02] pointer-events-none">
             <TrendingUp size={140} />
          </div>

          <div className="grid grid-cols-2 gap-3 p-1.5 bg-black/40 rounded-2xl border border-white/[0.03]">
            {[
              { id: 'shards_to_zenith', label: 'Shards → Zenith' },
              { id: 'zenith_to_shards', label: 'Zenith → Shards' },
            ].map(m => (
              <button
                key={m.id}
                onClick={() => handleModeChange(m.id as ExchangeMode)}
                className={cn(
                  'h-12 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300',
                  mode === m.id
                    ? 'bg-white text-black shadow-xl scale-100'
                    : 'text-neutral-600 hover:text-neutral-300'
                )}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-6 relative z-10">
            <motion.div layout className="min-w-0 rounded-2xl bg-brand-midnight border border-white/[0.05] p-5 shadow-inner group">
              <p className="text-[9px] font-black uppercase tracking-[0.2em] text-neutral-600 mb-2">{copy.inputLabel}</p>
              <div className="flex items-baseline gap-2 mb-3">
                 <p className="text-2xl font-black text-white tabular-nums leading-none font-mono truncate">{formatNumber(amountNumber)}</p>
              </div>
              <div className="h-px bg-white/[0.05] w-full mb-3" />
              <div className="flex items-center justify-between text-[9px] font-bold text-neutral-500 uppercase tracking-tighter">
                <span>RESERVE</span>
                <span className="tabular-nums font-mono">{formatNumber(isShardMode ? shardBalance : zenithBalance)}</span>
              </div>
            </motion.div>

            <button
              type="button"
              onClick={handleSwapMode}
              className="w-12 h-12 rounded-full bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center text-brand-accent transition-all hover:bg-brand-accent hover:text-black hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] active:scale-90 group"
              aria-label="Switch direction"
            >
              <Repeat2 size={20} strokeWidth={2.5} className="group-hover:rotate-180 transition-transform duration-500" />
            </button>

            <motion.div layout className="min-w-0 rounded-2xl bg-brand-accent/[0.03] border border-brand-accent/10 p-5 text-right shadow-inner">
              <p className="text-[9px] font-black uppercase tracking-[0.2em] text-brand-accent/60 mb-2">{copy.outputLabel}</p>
              <div className="flex items-baseline justify-end gap-2 mb-3">
                 <p className="text-2xl font-black text-white tabular-nums leading-none font-mono truncate">{formatNumber(outputAmount)}</p>
              </div>
              <div className="h-px bg-brand-accent/10 w-full mb-3" />
              <div className="flex items-center justify-between text-[9px] font-bold text-brand-accent/40 uppercase tracking-tighter">
                <span className="font-mono">POST-OP</span>
                <span className="tabular-nums font-mono">{formatNumber(isShardMode ? zenithBalance + outputAmount : shardBalance + outputAmount)}</span>
              </div>
            </motion.div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between px-1">
                <label className="text-[10px] font-black uppercase tracking-[0.3em] text-neutral-600">
                    TRANSACTION_AMOUNT
                </label>
                <button
                  onClick={() => setPreset(maxInputAmount)}
                  disabled={!canUseMax}
                  className="text-[9px] font-black text-brand-accent uppercase tracking-widest hover:text-white transition-colors disabled:opacity-20"
                >
                  SET MAX CLEARANCE
                </button>
            </div>
            <Input
                type="text"
                value={amount}
                onChange={(event) => handleAmountChange(event.target.value)}
                className="h-14 bg-brand-midnight text-lg font-mono px-6 rounded-2xl shadow-inner border-white/5"
                inputMode="numeric"
                placeholder="0.00"
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {presetOptions.map(({ label, amount: presetAmount }) => {
              const isDisabled = presetAmount < minimumInputAmount || (presetAmount > maxInputAmount && label !== 'MAX ASSETS');
              const isActive = presetAmount === amountNumber;

              return (
                <button
                  key={presetAmount}
                  onClick={() => setPreset(presetAmount)}
                  disabled={isDisabled}
                  className={cn(
                    'h-14 rounded-2xl bg-brand-midnight border p-3 text-left transition-all duration-300 active:scale-95 group',
                    isActive
                      ? 'border-brand-accent/40 bg-brand-accent/[0.05] shadow-[inset_0_0_10px_rgba(59,130,246,0.05)]'
                      : 'border-white/5 hover:border-white/20',
                    isDisabled && 'opacity-20'
                  )}
                >
                  <span className={cn(
                      "block text-[8px] font-black uppercase tracking-tighter mb-1 transition-colors",
                      isActive ? "text-brand-accent" : "text-neutral-600"
                  )}>{label}</span>
                  <span className="block truncate text-xs font-black text-white tabular-nums font-mono">{formatNumber(presetAmount)}</span>
                </button>
              );
            })}
          </div>

          <div className="pt-2">
            <Button
                onClick={handleExchange}
                disabled={!canExchange || exchanging}
                variant="tactical"
                className="w-full h-16 rounded-2xl uppercase tracking-[0.3em] text-[12px] font-black shadow-2xl active:scale-[0.98]"
            >
                {exchanging ? <Loader2 size={20} className="animate-spin" /> : <Repeat2 size={20} strokeWidth={2.5} />}
                <span>AUTHORIZE CONVERSION</span>
            </Button>
          </div>

          <motion.div
            layout
            className={cn(
              'flex items-center gap-4 p-5 rounded-2xl border text-[10px] font-black uppercase tracking-widest transition-all duration-500 shadow-sm',
              validationMessage
                ? 'border-warning/20 bg-warning/[0.03] text-warning'
                : 'border-success/20 bg-success/[0.03] text-success'
            )}
          >
            {validationMessage ? <AlertCircle size={18} /> : <CheckCircle2 size={18} className="animate-in" />}
            <span className="leading-tight">
              {validationMessage || `System Ready: Finalizing conversion of ${formatNumber(amountNumber)} ${copy.inputLabel}`}
            </span>
          </motion.div>
        </Card>
      </section>
    </div>
  );
};
