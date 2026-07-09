import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import { Egg, Timer, CheckCircle2, Loader2, ArrowRight, Zap, Target, Sparkles, Activity } from 'lucide-react';
import { cn } from '../utils';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { motion, AnimatePresence } from 'framer-motion';

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
        const tierLabel = String(egg.tier || 'COMMON').toUpperCase();

        return (
            <motion.div
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={egg.id || egg.index}
            >
                <Card variant="tactical" className={cn(
                    "p-5 flex items-center justify-between group transition-all duration-500",
                    egg.isReady && "border-emerald-500/30 bg-emerald-500/[0.03] shadow-[0_0_25px_rgba(16,185,129,0.1)]"
                )}>
                    <div className="flex items-center gap-5 min-w-0">
                        <div className="relative">
                            <div className={cn(
                                "w-14 h-14 rounded-2xl flex items-center justify-center border shrink-0 transition-all duration-700 relative z-10",
                                egg.isReady ? "bg-emerald-500/10 border-emerald-500/30" : "bg-brand-midnight border-white/[0.05]"
                            )}>
                                <Egg className={cn(
                                    "w-7 h-7 transition-all duration-500",
                                    egg.isReady ? "text-emerald-400 scale-110 drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "text-neutral-700 group-hover:text-neutral-400"
                                )} />
                                {egg.isReady && (
                                    <div className="absolute inset-0 bg-emerald-500/20 rounded-2xl animate-ping opacity-20" />
                                )}
                            </div>
                        </div>
                        <div className="min-w-0 space-y-1.5">
                            <div className="flex items-center gap-2.5">
                                <p className="text-[13px] font-black text-white uppercase tracking-tight truncate">{egg.name}</p>
                                <Badge variant="secondary" size="xs" className="rounded-md font-mono">{tierLabel}</Badge>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                {egg.isIncubating && !egg.isReady && (
                                    <Badge variant="primary" icon={Timer} size="xs" className="rounded-lg font-black tracking-widest bg-brand-accent/5 border-brand-accent/20">
                                        {egg.remainingMins} MINS REMAINING
                                    </Badge>
                                )}
                                {egg.isReady && (
                                    <Badge variant="success" icon={CheckCircle2} size="xs" className="rounded-lg font-black tracking-widest animate-pulse">
                                        EXTRACTION READY
                                    </Badge>
                                )}
                                {egg.isFresh && (
                                    <Badge variant="tactical" icon={Target} size="xs" className="rounded-lg font-black opacity-60">
                                        {waitMin > 0 ? `${waitMin}M CYCLE` : 'STANDBY'}
                                    </Badge>
                                )}
                                {isBoosted && (
                                    <Badge variant="epic" icon={Zap} size="xs" className="rounded-lg animate-in">BOOSTED</Badge>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="shrink-0 ml-4">
                        {egg.isFresh && (
                            <Button
                                variant="tactical"
                                size="sm"
                                onClick={() => handleIncubate(egg.id)}
                                isLoading={actionId === egg.id}
                                disabled={!hasEggId || activeIncubations >= incubationSlots}
                                className="rounded-xl px-5 h-10 text-[10px] uppercase font-black tracking-[0.2em]"
                            >
                                START <ArrowRight size={14} className="ml-2 group-hover:translate-x-1 transition-transform" />
                            </Button>
                        )}

                        {egg.isIncubating && !egg.isReady && (
                            <div className="w-10 h-10 rounded-full border-2 border-brand-accent/10 flex items-center justify-center relative">
                                <div className="absolute inset-0 rounded-full border-t-2 border-brand-accent animate-spin" />
                                <div className="w-1.5 h-1.5 rounded-full bg-brand-accent shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                            </div>
                        )}

                        {egg.isReady && (
                            <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleHatch(egg.id)}
                                isLoading={actionId === egg.id}
                                disabled={!hasEggId}
                                className="bg-emerald-500 hover:bg-emerald-400 text-black rounded-xl px-7 h-10 text-[10px] uppercase font-black tracking-[0.2em] shadow-[0_0_20px_rgba(16,185,129,0.3)] active:scale-95"
                            >
                                HATCH
                            </Button>
                        )}
                    </div>
                </Card>
            </motion.div>
        );
    };

    const renderSection = (title: string, sectionEggs: any[]) => (
        sectionEggs.length > 0 ? (
            <section className="space-y-4">
                <div className="flex items-center gap-2 px-1">
                    <h2 className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.3em]">{title}</h2>
                    <div className="h-px flex-1 bg-white/[0.03]" />
                </div>
                <div className="space-y-3">
                    <AnimatePresence mode="popLayout">
                        {sectionEggs.map(renderEgg)}
                    </AnimatePresence>
                </div>
            </section>
        ) : null
    );

    return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10">
            <header className="space-y-2">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                        <Egg className="text-brand-accent" size={26} />
                   </div>
                   <div className="flex flex-col gap-1">
                      <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Incubator</h1>
                      <div className="flex items-center gap-2">
                         <Activity size={11} className="text-neutral-600" />
                         <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                            BIOLOGICAL ASSET EXTRACTION TERMINAL
                         </p>
                      </div>
                   </div>
                </div>
            </header>

            <section className="grid grid-cols-3 gap-4">
                {[
                    { label: 'ACTIVE_SLOTS', value: `${activeIncubations} / ${incubationSlots}`, color: 'text-white' },
                    { label: 'EXTRACTION_READY', value: `${readyEggs.length} READY`, color: readyEggs.length > 0 ? 'text-success' : 'text-neutral-500' },
                    { label: 'ACCESS_CLEARANCE', value: `${passType.toUpperCase()} PASS`, color: 'text-brand-accent' },
                ].map((stat, i) => (
                    <Card key={i} variant="tactical" className="p-4 border-white/[0.04] bg-white/[0.01]">
                        <p className="text-[8px] font-black text-neutral-600 uppercase tracking-[0.2em] mb-2">{stat.label}</p>
                        <p className={cn("text-xs font-black tabular-nums uppercase leading-none font-mono", stat.color)}>{stat.value}</p>
                    </Card>
                ))}
            </section>

            {eggs.length > 0 ? (
                <div className="space-y-12">
                    {renderSection('READY FOR EXTRACTION', readyEggs)}
                    {renderSection('ACTIVE INCUBATION', incubatingEggs)}
                    {renderSection('PENDING ASSETS', freshEggs)}
                    {renderSection('UNRESTRICTED LOGS', otherEggs)}
                </div>
            ) : (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="py-24 flex flex-col items-center justify-center text-center space-y-6 bg-white/[0.01] rounded-[32px] border border-dashed border-white/[0.08]"
                >
                    <div className="relative">
                        <div className="w-20 h-20 rounded-full bg-white/[0.02] flex items-center justify-center border border-white/[0.05]">
                            <Egg size={32} className="text-neutral-800" />
                        </div>
                        <div className="absolute -inset-4 bg-brand-accent/5 blur-3xl rounded-full" />
                    </div>
                    <div className="space-y-2 px-6">
                        <p className="text-white font-black uppercase tracking-[0.2em] text-sm">No Eggs Detected</p>
                        <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest max-w-[240px] mx-auto leading-relaxed">
                            AQUIRE BIOLOGICAL CONTAINERS FROM THE GACHA MARKET OR STRATEGIC MISSIONS TO START INCUBATION.
                        </p>
                    </div>
                    <Button variant="outline" size="sm" className="rounded-xl border-white/5 text-[9px] px-6">
                       ACCESS MARKET <ArrowRight size={12} className="ml-2" />
                    </Button>
                </motion.div>
            )}
        </div>
    );
};
