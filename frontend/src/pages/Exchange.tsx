import React, { useMemo, useState } from 'react';
import { AlertCircle, BadgePercent, CheckCircle2, Coins, Gem, Loader2, RefreshCw, Repeat2 } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useApi } from '../hooks/useApi';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { Card } from '../components/ui/Card';
import { useToast } from '../components/ui/Toast';
import { useUser } from '../context/UserContext';
import { cn, formatNumber } from '../utils';

type ExchangeMode = 'shards_to_zenith' | 'zenith_to_shards';

interface ExchangeData {
  balance: number;
  zenith: number;
  rate: number;
  minimum_shards: number;
  minimum_zenith: number;
}

const Metric = ({
  icon: Icon,
  label,
  value,
  tone = 'neutral',
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  tone?: 'neutral' | 'accent' | 'success';
}) => (
  <div className="min-w-0 rounded-lg border border-white/5 bg-brand-deep px-3 py-2.5">
    <div className="flex items-center gap-1.5 text-[10px] font-semibold text-neutral-500">
      <Icon
        size={12}
        className={cn(
          tone === 'accent' && 'text-brand-accent',
          tone === 'success' && 'text-emerald-400',
          tone === 'neutral' && 'text-neutral-600'
        )}
      />
      <span className="truncate">{label}</span>
    </div>
    <p className="mt-1 truncate text-sm font-bold text-white tabular-nums">{value}</p>
  </div>
);

const getModeCopy = (mode: ExchangeMode) => {
  if (mode === 'shards_to_zenith') {
    return {
      inputLabel: 'Shards',
      outputLabel: 'Zenith',
      activeText: 'Shards to Zenith',
    };
  }

  return {
    inputLabel: 'Zenith',
    outputLabel: 'Shards',
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
    if (!rawAmount) return 'Enter an amount';
    if (!hasValidAmount) return 'Enter a positive whole number';

    if (isShardMode) {
      if (amountNumber < minimumShards) return `Minimum is ${formatNumber(minimumShards)} Shards`;
      if (amountNumber % rate !== 0) return `Use multiples of ${formatNumber(rate)} Shards`;
      if (shardBalance < amountNumber) return 'Not enough Shards';
      return null;
    }

    if (amountNumber < minimumZenith) return `Minimum is ${formatNumber(minimumZenith)} Zenith`;
    if (zenithBalance < amountNumber) return 'Not enough Zenith';
    return null;
  }, [amountNumber, hasValidAmount, isShardMode, minimumShards, minimumZenith, rate, rawAmount, shardBalance, zenithBalance]);

  const canExchange = !validationMessage && outputAmount > 0;
  const presetOptions = useMemo(() => {
    const baseOptions = isShardMode
      ? [
          { label: '1 Zenith', amount: rate },
          { label: '5 Zenith', amount: rate * 5 },
          { label: '10 Zenith', amount: rate * 10 },
        ]
      : [
          { label: '1 Zenith', amount: 1 },
          { label: '5 Zenith', amount: 5 },
          { label: '10 Zenith', amount: 10 },
        ];
    const options = [...baseOptions, { label: 'Max', amount: maxInputAmount }];
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
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      const result = await apiFetch(`/shop/exchange/${mode}?amount=${amountNumber}`, { method: 'POST' });
      addToast(result.message || 'Exchange complete', 'success');
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
      <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
        <div className="flex flex-col gap-2">
           <Skeleton className="h-8 w-44 rounded-lg" />
           <Skeleton className="h-4 w-64 rounded-lg" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[1, 2, 3].map((item) => <Skeleton key={item} className="h-16 rounded-xl" />)}
        </div>
        <Skeleton className="h-80 rounded-2xl" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px">
        <ErrorState message={error} onAction={fetchExchange} />
      </div>
    );
  }

  return (
    <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8 select-none">
      <header className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
               <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                    <Repeat2 size={22} className="text-brand-accent" />
               </div>
               <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Currency</h1>
            </div>
            <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
              Authorized currency conversion protocol.
            </p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={loading || exchanging}
            className="w-12 h-12 flex items-center justify-center rounded-xl bg-brand-deep border border-white/5 text-neutral-400 hover:text-white transition-all active:scale-95 shrink-0"
            aria-label="Refresh exchange"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Metric icon={Coins} label="Shards" value={formatNumber(shardBalance)} tone="neutral" />
          <Metric icon={Gem} label="Zenith" value={formatNumber(zenithBalance)} tone="accent" />
          <Metric icon={BadgePercent} label="Protocol Rate" value={`${formatNumber(rate)}:1`} tone="success" />
        </div>

        {error && data && (
          <div className="flex items-start gap-3 p-3 rounded-xl border border-amber-500/20 bg-amber-500/5 text-[10px] font-black uppercase tracking-widest text-amber-500/80">
            <AlertCircle size={14} className="shrink-0" />
            <span>Legacy data detected. Refresh to synchronize local balances.</span>
          </div>
        )}
      </header>

      <section className="space-y-4">
        <Card className="p-5 space-y-6">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleModeChange('shards_to_zenith')}
              className={cn(
                'h-12 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all active:scale-[0.98]',
                mode === 'shards_to_zenith'
                  ? 'bg-white text-brand-midnight border-white shadow-lg'
                  : 'bg-brand-midnight text-neutral-500 border-white/5 hover:text-white'
              )}
            >
              Shards to Zenith
            </button>
            <button
              onClick={() => handleModeChange('zenith_to_shards')}
              className={cn(
                'h-12 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all active:scale-[0.98]',
                mode === 'zenith_to_shards'
                  ? 'bg-white text-brand-midnight border-white shadow-lg'
                  : 'bg-brand-midnight text-neutral-500 border-white/5 hover:text-white'
              )}
            >
              Zenith to Shards
            </button>
          </div>

          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
            <div className="min-w-0 rounded-2xl bg-brand-midnight border border-white/5 p-4">
              <p className="text-[9px] font-black uppercase tracking-widest text-neutral-600 mb-1">{copy.inputLabel}</p>
              <p className="text-xl font-black text-white tabular-nums leading-none mb-2">{formatNumber(amountNumber)}</p>
              <div className="h-px bg-white/5 w-full mb-2" />
              <p className="text-[9px] font-bold text-neutral-500 uppercase tracking-tighter truncate">
                Available: {formatNumber(isShardMode ? shardBalance : zenithBalance)}
              </p>
            </div>
            <button
              type="button"
              onClick={handleSwapMode}
              className="w-10 h-10 rounded-xl bg-brand-midnight border border-white/5 flex items-center justify-center text-brand-accent transition-all hover:bg-brand-accent/10 active:scale-90"
              aria-label="Switch exchange direction"
            >
              <Repeat2 size={18} />
            </button>
            <div className="min-w-0 rounded-2xl bg-brand-accent/5 border border-brand-accent/20 p-4 text-right">
              <p className="text-[9px] font-black uppercase tracking-widest text-brand-accent/60 mb-1">{copy.outputLabel}</p>
              <p className="text-xl font-black text-white tabular-nums leading-none mb-2">{formatNumber(outputAmount)}</p>
              <div className="h-px bg-brand-accent/10 w-full mb-2" />
              <p className="text-[9px] font-bold text-brand-accent/40 uppercase tracking-tighter truncate">
                Result: {formatNumber(isShardMode ? zenithBalance + outputAmount : shardBalance + outputAmount)}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-neutral-600">
                    Input Amount
                </label>
                <button
                  onClick={() => setPreset(maxInputAmount)}
                  disabled={!canUseMax}
                  className="text-[9px] font-black text-brand-accent uppercase tracking-widest hover:underline disabled:opacity-30"
                >
                  Max Available
                </button>
            </div>
            <div className="flex gap-2">
                <input
                    type="text"
                    value={amount}
                    onChange={(event) => handleAmountChange(event.target.value)}
                    className="h-14 flex-1 rounded-2xl border border-white/5 bg-brand-midnight px-4 text-sm font-black text-white outline-none focus:border-brand-accent/40 transition-all tabular-nums"
                    inputMode="numeric"
                    placeholder="ENTER AMOUNT..."
                />
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {presetOptions.map(({ label, amount: presetAmount }) => {
              const isDisabled = presetAmount < minimumInputAmount || presetAmount > maxInputAmount;
              const isActive = presetAmount === amountNumber;

              return (
                <button
                  key={presetAmount}
                  onClick={() => setPreset(presetAmount)}
                  disabled={isDisabled}
                  className={cn(
                    'h-12 rounded-xl bg-brand-midnight border p-2 text-left transition-all active:scale-95',
                    isActive
                      ? 'border-brand-accent/40 bg-brand-accent/5'
                      : 'border-white/5 hover:border-white/20',
                    isDisabled && 'opacity-30'
                  )}
                >
                  <span className="block text-[8px] font-black text-neutral-500 uppercase tracking-tighter">{label}</span>
                  <span className="block truncate text-xs font-black text-white tabular-nums">{formatNumber(presetAmount)}</span>
                </button>
              );
            })}
          </div>

          <button
            onClick={handleExchange}
            disabled={!canExchange || exchanging}
            className={cn(
                'w-full h-14 rounded-2xl font-black uppercase tracking-[0.2em] text-[11px] flex items-center justify-center gap-3 transition-all active:scale-[0.98]',
                canExchange
                    ? 'bg-brand-accent text-white shadow-[0_10px_30px_rgba(59,130,246,0.2)]'
                    : 'bg-brand-midnight text-neutral-600 border border-white/5'
            )}
          >
            {exchanging ? <Loader2 size={18} className="animate-spin" /> : <Repeat2 size={18} />}
            <span>Execute Transaction</span>
          </button>

          <div
            className={cn(
              'flex items-center gap-3 p-4 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all',
              validationMessage
                ? 'border-amber-500/20 bg-amber-500/5 text-amber-500'
                : 'border-emerald-500/20 bg-emerald-500/5 text-emerald-500'
            )}
          >
            {validationMessage ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
            <span>
              {validationMessage || `Protocol Ready: Convert ${formatNumber(amountNumber)} ${copy.inputLabel}`}
            </span>
          </div>
        </Card>
      </section>
    </div>
  );
};
