import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import { Sparkles, Timer, Zap, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';
import { cn } from '../utils';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';

function getRemainingMinutes(egg: any, now: number | null) {
    if (egg.hatch_time && now !== null) {
        const hatchAt = new Date(egg.hatch_time).getTime();
        if (Number.isFinite(hatchAt)) {
            return Math.max(0, Math.ceil((hatchAt - now) / 60000));
        }
    }
    return Math.max(0, Number(egg.remaining_mins || 0));
}

export const Hatchery = () => {
    const { user, triggerRefresh } = useUser();
    const { addToast } = useToast();
    const [actionId, setActionId] = useState<string | null>(null);
    const [now, setNow] = useState<number | null>(null);

    useEffect(() => {
        setNow(Date.now());
        const timer = window.setInterval(() => setNow(Date.now()), 30000);
        return () => window.clearInterval(timer);
    }, []);

    const handleHatch = async (eggId: string) => {
        setActionId(eggId);
        try {
            const result = await apiFetch(`/eggs/hatch/${eggId}`, { method: 'POST' });
            addToast(result?.character?.name ? `Hatched! You found ${result.character.name}.` : 'Egg hatched successfully.', 'success');
            triggerRefresh();
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setActionId(null);
        }
    };

    const handleIncubate = async (eggId: string) => {
        setActionId(eggId);
        try {
            await apiFetch(`/eggs/incubate/${eggId}`, { method: 'POST' });
            addToast('Incubation started.', 'success');
            triggerRefresh();
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setActionId(null);
        }
    };

    const eggs = (user?.eggs || []).map((egg: any, index: number) => {
        const remainingMins = getRemainingMinutes(egg, now);
        const isIncubating = egg.status === 'incubating';
        const isReady = isIncubating && remainingMins <= 0;
        const isFresh = egg.status === 'fresh';
        return { ...egg, index, remainingMins, isIncubating, isReady, isFresh };
    });

    const readyEggs = eggs.filter(egg => egg.isReady);
    const incubatingEggs = eggs.filter(egg => egg.isIncubating && !egg.isReady);
    const freshEggs = eggs.filter(egg => egg.isFresh);
    const otherEggs = eggs.filter(egg => !egg.isReady && !egg.isIncubating && !egg.isFresh);
    const incubationSlots = Number(user?.stats?.incubation_slots || 1);
    const activeIncubations = incubatingEggs.length + readyEggs.length;
    const passType = user?.stats?.pass_type || 'free';

    const renderEgg = (egg: any) => {
        const hasEggId = Boolean(egg.id);
        const waitMin = Number(egg.wait_min || egg.incubation_minutes || 0);
        const baseWaitMin = Number(egg.base_wait_min || egg.incubation_base_minutes || waitMin);
        const isBoosted = waitMin > 0 && baseWaitMin > waitMin;
        const tierLabel = String(egg.tier || 'common');

        return (
            <div key={egg.id || egg.index} className={cn(
                "p-4 rounded-xl border transition-all flex items-center justify-between shadow-sm",
                egg.isReady ? "border-emerald-500/30 bg-emerald-500/5" : "border-white/5 bg-brand-deep"
            )}>
                <div className="flex items-center gap-4 min-w-0">
                    <div className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center border shrink-0",
                        egg.isReady ? "bg-emerald-500/10 border-emerald-500/20" : "bg-brand-midnight border-white/5"
                    )}>
                        <Sparkles className={egg.isReady ? "text-emerald-500 animate-pulse" : "text-neutral-500"} size={20} />
                    </div>
                    <div className="min-w-0">
                        <p className="text-base font-bold text-white leading-none mb-1.5 truncate">{egg.name}</p>
                        <div className="flex flex-wrap items-center gap-2">
                            <span className="text-[10px] font-bold uppercase tracking-wide text-neutral-500 bg-brand-midnight border border-white/5 rounded px-1.5 py-0.5">
                                {tierLabel}
                            </span>
                            {egg.isIncubating && !egg.isReady && (
                                <>
                                    <Timer size={14} className="text-brand-accent" />
                                    <span className="text-xs font-semibold text-brand-accent">{egg.remainingMins}m left</span>
                                </>
                            )}
                            {egg.isReady && (
                                <>
                                    <CheckCircle2 size={14} className="text-emerald-500" />
                                    <span className="text-xs font-bold text-emerald-500">Ready to hatch</span>
                                </>
                            )}
                            {egg.isFresh && (
                                <>
                                    <Zap size={14} className="text-neutral-500" />
                                    <span className="text-xs font-medium text-neutral-500">
                                        {waitMin > 0 ? `${waitMin}m incubation` : 'Fresh egg'}
                                    </span>
                                </>
                            )}
                            {isBoosted && (
                                <span className="text-xs font-semibold text-emerald-400">
                                    {baseWaitMin}m base
                                </span>
                            )}
                            {!hasEggId && (
                                <span className="text-xs font-semibold text-red-500">Unavailable</span>
                            )}
                        </div>
                    </div>
                </div>

                {egg.isFresh && (
                    <button
                        onClick={() => handleIncubate(egg.id)}
                        disabled={!!actionId || !hasEggId}
                        className="bg-white/5 hover:bg-white/10 text-white text-xs font-bold px-4 py-2 rounded-lg active:scale-95 transition-all flex items-center gap-1.5 disabled:opacity-50"
                    >
                        {actionId === egg.id ? <Loader2 size={14} className="animate-spin" /> : <>Incubate <ArrowRight size={14} /></>}
                    </button>
                )}

                {egg.isIncubating && !egg.isReady && (
                    <div className="bg-brand-accent/10 text-brand-accent text-xs font-bold px-4 py-2 rounded-lg">
                        Incubating
                    </div>
                )}

                {egg.isReady && (
                    <button
                        onClick={() => handleHatch(egg.id)}
                        disabled={!!actionId || !hasEggId}
                        className="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold px-4 py-2 rounded-lg active:scale-95 transition-all shadow-sm disabled:opacity-50"
                    >
                        {actionId === egg.id ? <Loader2 size={14} className="animate-spin" /> : 'Hatch'}
                    </button>
                )}
            </div>
        );
    };

    const renderSection = (title: string, sectionEggs: any[]) => (
        sectionEggs.length > 0 ? (
            <section className="space-y-3">
                <h2 className="text-sm font-bold text-neutral-300">{title}</h2>
                {sectionEggs.map(renderEgg)}
            </section>
        ) : null
    );

    return (
        <div className="px-4 py-8 pb-20 max-w-2xl mx-auto space-y-8">
            <header className="border-b border-white/5 pb-4">
                <h1 className="text-xl font-bold text-white tracking-tight mb-1">Incubation</h1>
                <p className="text-sm font-medium text-neutral-400">Incubate eggs and hatch new characters.</p>
            </header>

            <section className="grid grid-cols-3 gap-2">
                <div className="rounded-lg border border-white/5 bg-brand-deep px-3 py-2.5">
                    <p className="text-[10px] font-semibold text-neutral-500">Slots</p>
                    <p className="mt-1 text-sm font-bold text-white tabular-nums">{activeIncubations}/{incubationSlots}</p>
                </div>
                <div className="rounded-lg border border-white/5 bg-brand-deep px-3 py-2.5">
                    <p className="text-[10px] font-semibold text-neutral-500">Ready</p>
                    <p className="mt-1 text-sm font-bold text-emerald-400 tabular-nums">{readyEggs.length}</p>
                </div>
                <div className="rounded-lg border border-white/5 bg-brand-deep px-3 py-2.5">
                    <p className="text-[10px] font-semibold text-neutral-500">Pass</p>
                    <p className="mt-1 text-sm font-bold text-brand-accent capitalize truncate">{passType}</p>
                </div>
            </section>

            <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-neutral-300">Your eggs</h2>
                <span className="bg-brand-deep border border-white/10 px-2.5 py-1 rounded-md text-xs font-bold text-white shadow-sm">{eggs.length} total</span>
            </div>

            {eggs.length > 0 ? (
                <div className="space-y-8">
                    {renderSection('Ready to hatch', readyEggs)}
                    {renderSection('Incubating', incubatingEggs)}
                    {renderSection('Fresh eggs', freshEggs)}
                    {renderSection('Other eggs', otherEggs)}
                </div>
            ) : (
                <div className="bg-brand-deep p-8 rounded-xl border border-white/5 text-center flex flex-col items-center shadow-sm">
                    <Zap size={24} className="text-neutral-700 mb-3" />
                    <p className="text-neutral-500 text-sm font-medium">
                        You do not have any eggs yet.
                    </p>
                </div>
            )}
        </div>
    );
};
