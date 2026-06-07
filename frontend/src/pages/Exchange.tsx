import React, { useMemo, useState } from 'react';
import { AlertCircle, BadgePercent, CheckCircle2, Coins, Gem, Loader2, RefreshCw, Repeat2 } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useApi } from '../hooks/useApi';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
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
  const afterShardBalance = canExchange
    ? (isShardMode ? shardBalance - amountNumber : shardBalance + outputAmount)
    : shardBalance;
  const afterZenithBalance = canExchange
    ? (isShardMode ? zenithBalance + outputAmount : zenithBalance - amountNumber)
    : zenithBalance;
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
      <div className="px-4 py-6 pb-20 max-w-3xl mx-auto">
        <div className="mb-6 border-b border-white/5 pb-5">
          <Skeleton className="h-6 w-44 rounded-lg mb-3" />
          <Skeleton className="h-4 w-64 rounded-lg" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-6">
          {[1, 2, 3].map((item) => <Skeleton key={item} className="h-16 rounded-lg" />)}
        </div>
        <Skeleton className="h-72 rounded-lg" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="px-4 py-8 max-w-2xl mx-auto">
        <ErrorState message={error} onAction={fetchExchange} />
      </div>
    );
  }

  return (
    <div className="pb-20 pt-4 max-w-3xl mx-auto">
      <header className="px-4 pb-5 mb-5 border-b border-white/5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Repeat2 size={18} className="text-brand-accent shrink-0" />
              <h1 className="text-lg font-bold text-white tracking-tight">Exchange</h1>
            </div>
            <p className="text-sm font-medium text-neutral-400 leading-snug">
              Convert balances between Shards and Zenith.
            </p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={loading || exchanging}
            className="p-2.5 rounded-lg bg-brand-deep border border-white/5 text-neutral-400 hover:text-white hover:bg-white/5 disabled:opacity-60 transition-colors active:scale-95 shrink-0"
            aria-label="Refresh exchange"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
          <Metric icon={Coins} label="Shards" value={formatNumber(shardBalance)} />
          <Metric icon={Gem} label="Zenith" value={formatNumber(zenithBalance)} tone="accent" />
          <Metric icon={BadgePercent} label="Rate" value={`${formatNumber(rate)}:1`} tone="success" />
        </div>

        {error && data && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-500/15 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-200">
            <AlertCircle size={14} className="mt-0.5 shrink-0" />
            <span>Showing the latest loaded exchange data. Refresh again if balances look out of date.</span>
          </div>
        )}
      </header>

      <section className="px-4">
        <div className="rounded-lg border border-white/5 bg-brand-deep p-4 sm:p-5">
          <div className="mb-4 grid grid-cols-2 gap-2">
            <button
              onClick={() => handleModeChange('shards_to_zenith')}
              className={cn(
                'h-11 rounded-lg border text-xs font-bold transition-all active:scale-[0.98]',
                mode === 'shards_to_zenith'
                  ? 'bg-white text-brand-midnight border-white'
                  : 'bg-brand-midnight text-neutral-400 border-white/5 hover:text-neutral-200'
              )}
            >
              Shards to Zenith
            </button>
            <button
              onClick={() => handleModeChange('zenith_to_shards')}
              className={cn(
                'h-11 rounded-lg border text-xs font-bold transition-all active:scale-[0.98]',
                mode === 'zenith_to_shards'
                  ? 'bg-white text-brand-midnight border-white'
                  : 'bg-brand-midnight text-neutral-400 border-white/5 hover:text-neutral-200'
              )}
            >
              Zenith to Shards
            </button>
          </div>

          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 xs:gap-3 mb-5">
            <div className="min-w-0 rounded-lg border border-white/5 bg-brand-midnight px-3 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500">{copy.inputLabel}</p>
              <p className="mt-1 truncate text-lg font-bold text-white tabular-nums">{formatNumber(amountNumber)}</p>
              <p className="mt-1 truncate text-[10px] font-semibold text-neutral-600 tabular-nums">
                Balance {formatNumber(isShardMode ? shardBalance : zenithBalance)}
              </p>
            </div>
            <button
              type="button"
              onClick={handleSwapMode}
              className="h-9 w-9 rounded-lg border border-white/5 bg-brand-midnight flex items-center justify-center text-brand-accent transition-colors hover:bg-white/5 active:scale-95"
              aria-label="Switch exchange direction"
            >
              <Repeat2 size={16} />
            </button>
            <div className="min-w-0 rounded-lg border border-brand-accent/20 bg-brand-accent/10 px-3 py-3 text-right">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-brand-accent/80">{copy.outputLabel}</p>
              <p className="mt-1 truncate text-lg font-bold text-white tabular-nums">{formatNumber(outputAmount)}</p>
              <p className="mt-1 truncate text-[10px] font-semibold text-brand-accent/60 tabular-nums">
                Balance {formatNumber(isShardMode ? zenithBalance : shardBalance)}
              </p>
            </div>
          </div>

          <label className="mb-2 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
            Amount
          </label>
          <div className="grid grid-cols-1 xs:grid-cols-[minmax(0,1fr)_72px_112px] gap-2">
            <input
              type="text"
              min={isShardMode ? minimumShards : minimumZenith}
              step={isShardMode ? rate : 1}
              value={amount}
              onChange={(event) => handleAmountChange(event.target.value)}
              className="h-12 min-w-0 flex-1 rounded-lg border border-white/5 bg-brand-midnight px-3 text-sm font-bold text-white outline-none focus:border-brand-accent/50"
              inputMode="numeric"
              pattern="[0-9]*"
              aria-label={`${copy.inputLabel} amount`}
            />
            <button
              type="button"
              onClick={() => setPreset(maxInputAmount)}
              disabled={!canUseMax}
              className={cn(
                'h-12 rounded-lg border text-xs font-bold transition-all active:scale-95',
                canUseMax
                  ? 'border-white/10 bg-brand-midnight text-neutral-300 hover:text-white hover:bg-white/5'
                  : 'border-white/5 bg-brand-midnight text-neutral-700'
              )}
            >
              Max
            </button>
            <button
              onClick={handleExchange}
              disabled={!canExchange || exchanging}
              className={cn(
                'h-12 px-4 rounded-lg text-xs font-bold min-w-[104px] flex items-center justify-center gap-2 transition-all active:scale-95',
                canExchange
                  ? 'bg-brand-accent text-white'
                  : 'bg-brand-midnight text-neutral-600 border border-white/5'
              )}
            >
              {exchanging ? <Loader2 size={16} className="animate-spin" /> : <Repeat2 size={15} />}
              <span>Exchange</span>
            </button>
          </div>

          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
            {presetOptions.map(({ label, amount: presetAmount }) => {
              const isDisabled = presetAmount < minimumInputAmount || presetAmount > maxInputAmount;
              const isActive = presetAmount === amountNumber;

              return (
                <button
                  key={presetAmount}
                  onClick={() => setPreset(presetAmount)}
                  disabled={isDisabled}
                  className={cn(
                    'h-11 rounded-lg bg-brand-midnight border px-2 text-left transition-colors',
                    isActive
                      ? 'border-brand-accent/50 text-white'
                      : 'border-white/5 text-neutral-400 hover:text-neutral-200',
                    isDisabled && 'opacity-45 hover:text-neutral-400'
                  )}
                >
                  <span className="block text-[10px] font-bold leading-none">{label}</span>
                  <span className="mt-1 block truncate text-[11px] font-semibold tabular-nums">{formatNumber(presetAmount)}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2">
            <div className="min-w-0 rounded-lg border border-white/5 bg-brand-midnight px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Shards after</p>
              <p className="mt-1 truncate text-sm font-bold text-white tabular-nums">{formatNumber(afterShardBalance)}</p>
            </div>
            <div className="min-w-0 rounded-lg border border-white/5 bg-brand-midnight px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Zenith after</p>
              <p className="mt-1 truncate text-sm font-bold text-white tabular-nums">{formatNumber(afterZenithBalance)}</p>
            </div>
          </div>

          <div
            className={cn(
              'mt-4 flex items-start gap-2 rounded-lg border px-3 py-2 text-xs font-medium',
              validationMessage
                ? 'border-amber-500/15 bg-amber-500/10 text-amber-200'
                : 'border-emerald-500/15 bg-emerald-500/10 text-emerald-200'
            )}
          >
            {validationMessage ? <AlertCircle size={14} className="mt-0.5 shrink-0" /> : <CheckCircle2 size={14} className="mt-0.5 shrink-0" />}
            <span>
              {validationMessage || `${copy.activeText}: ${formatNumber(amountNumber)} ${copy.inputLabel} to ${formatNumber(outputAmount)} ${copy.outputLabel}`}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
};
