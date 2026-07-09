import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import { Egg, Timer, CheckCircle2, Loader2, ArrowRight, Zap } from 'lucide-react';
import { cn } from '../utils';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

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
            <Card key={egg.id || egg.index} className={cn(
                "p-4 flex items-center justify-between group",
                egg.isReady && "border-emerald-500/30 bg-emerald-500/5 shadow-[0_0_20px_rgba(16,185,129,0.05)]"
            )}>
                <div className="flex items-center gap-4 min-w-0">
                    <div className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center border shrink-0 transition-transform duration-500 group-hover:scale-110",
                        egg.isReady ? "bg-emerald-500/10 border-emerald-500/20" : "bg-brand-surface border-white/5"
                    )}>
                        <Egg className={cn(
                            "w-6 h-6 transition-all",
                            egg.isReady ? "text-emerald-500 animate-bounce" : "text-neutral-500"
                        )} />
                    </div>
                    <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm font-black text-white uppercase tracking-tight truncate">{egg.name}</p>
                            <Badge variant="secondary" size="xs" className="rounded-md px-1 py-0">{tierLabel}</Badge>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                            {egg.isIncubating && !egg.isReady && (
                                <Badge variant="primary" icon={Timer} size="xs" className="rounded-lg">
                                    {egg.remainingMins}M REMAINING
                                </Badge>
                            )}
                            {egg.isReady && (
                                <Badge variant="success" icon={CheckCircle2} size="xs" className="rounded-lg animate-pulse">
                                    READY TO HATCH
                                </Badge>
                            )}
                            {egg.isFresh && (
                                <Badge variant="secondary" icon={Timer} size="xs" className="rounded-lg">
                                    {waitMin > 0 ? `${waitMin}M CYCLE` : 'FRESH'}
                                </Badge>
                            )}
                            {isBoosted && (
                                <Badge variant="purple" icon={Zap} size="xs" className="rounded-lg">BOOSTED</Badge>
                            )}
                        </div>
                    </div>
                </div>

                <div className="shrink-0 ml-4">
                    {egg.isFresh && (
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleIncubate(egg.id)}
                            isLoading={actionId === egg.id}
                            disabled={!hasEggId}
                            className="rounded-xl px-4 py-2 text-[10px] uppercase font-black tracking-widest border-white/10"
                        >
                            Start <ArrowRight size={14} className="ml-1.5" />
                        </Button>
                    )}

                    {egg.isIncubating && !egg.isReady && (
                        <div className="w-8 h-8 rounded-full border-2 border-brand-accent/20 flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-pulse" />
                        </div>
                    )}

                    {egg.isReady && (
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleHatch(egg.id)}
                            isLoading={actionId === egg.id}
                            disabled={!hasEggId}
                            className="bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl px-6 py-2 text-[10px] uppercase font-black tracking-widest"
                        >
                            Hatch
                        </Button>
                    )}
                </div>
            </Card>
        );
    };

    const renderSection = (title: string, sectionEggs: any[]) => (
        sectionEggs.length > 0 ? (
            <section className="space-y-4">
                <h2 className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] px-1">{title}</h2>
                <div className="space-y-3">
                    {sectionEggs.map(renderEgg)}
                </div>
            </section>
        ) : null
    );

    return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
            <header className="space-y-1">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                        <Egg className="text-brand-accent" size={22} />
                   </div>
                   <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Incubator</h1>
                </div>
                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
                    Manage your active biological containers and unlock new seals.
                </p>
            </header>

            <section className="grid grid-cols-3 gap-3">
                <Card className="p-3">
                    <p className="text-[9px] font-black text-neutral-500 uppercase tracking-widest mb-1">Slots</p>
                    <p className="text-sm font-black text-white tabular-nums uppercase">{activeIncubations} / {incubationSlots}</p>
                </Card>
                <Card className="p-3">
                    <p className="text-[9px] font-black text-neutral-500 uppercase tracking-widest mb-1">Status</p>
                    <p className={cn("text-sm font-black tabular-nums uppercase", readyEggs.length > 0 ? "text-emerald-500" : "text-white")}>
                        {readyEggs.length} READY
                    </p>
                </Card>
                <Card className="p-3">
                    <p className="text-[9px] font-black text-neutral-500 uppercase tracking-widest mb-1">Access</p>
                    <p className="text-sm font-black text-brand-accent uppercase truncate">{passType} PASS</p>
                </Card>
            </section>

            {eggs.length > 0 ? (
                <div className="space-y-10">
                    {renderSection('Operational Ready', readyEggs)}
                    {renderSection('Active Incubation', incubatingEggs)}
                    {renderSection('Pending Start', freshEggs)}
                    {renderSection('Other Assets', otherEggs)}
                </div>
            ) : (
                <div className="py-16 flex flex-col items-center justify-center text-center space-y-4 bg-brand-deep/30 rounded-3xl border border-dashed border-white/10">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center">
                        <Egg size={32} className="text-neutral-700" />
                    </div>
                    <div className="space-y-1">
                        <p className="text-white font-black uppercase tracking-tight">No Eggs Detected</p>
                        <p className="text-xs font-bold text-neutral-500 uppercase tracking-widest">AQUAIRE EGGS FROM THE SHOP OR MISSIONS.</p>
                    </div>
                </div>
            )}
        </div>
    );
};
