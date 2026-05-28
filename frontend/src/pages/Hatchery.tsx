import React, { useState } from 'react';
import { useUser, Pet } from '../context/UserContext';
import { Sparkles, Timer, Zap, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';
import { cn } from '../utils';
import { apiFetch } from '../api/client';
import { useToast } from '../components/ui/Toast';

interface HatcheryProps {
    onPetClick?: (pet: Pet) => void;
}

export const Hatchery = ({ onPetClick }: HatcheryProps) => {
    const { user, triggerRefresh } = useUser();
    const { addToast } = useToast();
    const [actionId, setActionId] = useState<string | null>(null);

    const handleHatch = async (eggId: string) => {
        setActionId(eggId);
        try {
            const result = await apiFetch(`/eggs/hatch/${eggId}`, { method: 'POST' });
            addToast(`Hatched! You found ${result.character.name}!`, 'success');
            triggerRefresh();
        } catch (err: any) {
            addToast(err.message || 'Hatching failed', 'error');
        } finally {
            setActionId(null);
        }
    };

    const handleIncubate = async (eggId: string) => {
        setActionId(eggId);
        try {
            await apiFetch(`/eggs/incubate/${eggId}`, { method: 'POST' });
            addToast('Incubation started!', 'success');
            triggerRefresh();
        } catch (err: any) {
            addToast(err.message || 'Incubation failed', 'error');
        } finally {
            setActionId(null);
        }
    };

    return (
        <div className="px-4 py-8 pb-20 max-w-2xl mx-auto space-y-8">
            <header className="border-b border-white/5 pb-4">
                <h1 className="text-xl font-bold text-white tracking-tight mb-1">Incubation</h1>
                <p className="text-sm font-medium text-neutral-400">Accelerate the birth of new legends</p>
            </header>

            <section>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold text-neutral-300">Inventory Eggs</h2>
                    <span className="bg-brand-deep border border-white/10 px-2.5 py-1 rounded-md text-xs font-bold text-white shadow-sm">{user?.eggs?.length || 0} Total</span>
                </div>

                <div className="space-y-3">
                    {user?.eggs && user.eggs.length > 0 ? user.eggs.map((egg: any, i) => {
                        const isIncubating = egg.status === 'incubating';
                        const isReady = egg.status === 'incubating' && egg.remaining_mins <= 0;
                        const isFresh = egg.status === 'fresh';

                        return (
                            <div key={egg.id || i} className={cn(
                                "p-4 rounded-xl border transition-all flex items-center justify-between shadow-sm",
                                isReady ? "border-emerald-500/30 bg-emerald-500/5" : "border-white/5 bg-brand-deep"
                            )}>
                                <div className="flex items-center gap-4">
                                    <div className={cn(
                                        "w-12 h-12 rounded-lg flex items-center justify-center border",
                                        isReady ? "bg-emerald-500/10 border-emerald-500/20" : "bg-brand-midnight border-white/5"
                                    )}>
                                        <Sparkles className={isReady ? "text-emerald-500 animate-pulse" : "text-neutral-500"} size={20} />
                                    </div>
                                    <div>
                                        <p className="text-base font-bold text-white leading-none mb-1.5">{egg.name}</p>
                                        <div className="flex items-center gap-2">
                                            {isIncubating && !isReady && (
                                                <>
                                                    <Timer size={14} className="text-brand-accent" />
                                                    <span className="text-xs font-semibold text-brand-accent">{egg.remaining_mins}m Left</span>
                                                </>
                                            )}
                                            {isReady && (
                                                <>
                                                    <CheckCircle2 size={14} className="text-emerald-500" />
                                                    <span className="text-xs font-bold text-emerald-500">Ready to Hatch</span>
                                                </>
                                            )}
                                            {isFresh && (
                                                <>
                                                    <Zap size={14} className="text-neutral-500" />
                                                    <span className="text-xs font-medium text-neutral-500">Fresh Egg</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {isFresh && (
                                    <button
                                        onClick={() => handleIncubate(egg.id)}
                                        disabled={!!actionId}
                                        className="bg-white/5 hover:bg-white/10 text-white text-xs font-bold px-4 py-2 rounded-lg active:scale-95 transition-all flex items-center gap-1.5 disabled:opacity-50"
                                    >
                                        {actionId === egg.id ? <Loader2 size={14} className="animate-spin" /> : <>Start <ArrowRight size={14} /></>}
                                    </button>
                                )}

                                {isIncubating && !isReady && (
                                    <div className="bg-brand-accent/10 text-brand-accent text-xs font-bold px-4 py-2 rounded-lg">
                                        Incubating
                                    </div>
                                )}

                                {isReady && (
                                    <button
                                        onClick={() => handleHatch(egg.id)}
                                        disabled={!!actionId}
                                        className="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold px-4 py-2 rounded-lg active:scale-95 transition-all shadow-sm disabled:opacity-50"
                                    >
                                        {actionId === egg.id ? <Loader2 size={14} className="animate-spin" /> : 'Hatch'}
                                    </button>
                                )}
                            </div>
                        );
                    }) : (
                        <div className="bg-brand-deep p-8 rounded-xl border border-white/5 text-center flex flex-col items-center shadow-sm">
                            <Zap size={24} className="text-neutral-700 mb-3" />
                            <p className="text-neutral-500 text-sm font-medium">
                                No eggs detected in your inventory.
                            </p>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};
