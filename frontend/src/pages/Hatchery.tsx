import React, { useState, useEffect } from 'react';
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
        <div className="px-6 py-10 pb-20 space-y-12">
            <header>
                <h1 className="text-3xl font-black italic uppercase tracking-tighter text-white">Incubation</h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.4em] mt-1">Accelerate the birth of new legends</p>
            </header>

            <section>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Inventory Eggs</h2>
                    <span className="bg-white/5 border border-white/10 px-3 py-1 rounded-full text-[9px] font-black text-white">{user?.eggs?.length || 0} Total</span>
                </div>

                <div className="space-y-4">
                    {user?.eggs && user.eggs.length > 0 ? user.eggs.map((egg: any, i) => {
                        const isIncubating = egg.status === 'incubating';
                        const isReady = egg.status === 'incubating' && egg.remaining_mins <= 0;
                        const isFresh = egg.status === 'fresh';

                        return (
                            <div key={egg.id || i} className={cn(
                                "glass-panel p-5 rounded-[2.5rem] border transition-all flex items-center justify-between",
                                isReady ? "border-brand-accent/40 bg-brand-accent/5 shadow-lg shadow-brand-accent/5" : "border-white/5 bg-white/5"
                            )}>
                                <div className="flex items-center gap-4">
                                    <div className={cn(
                                        "w-14 h-14 rounded-2xl flex items-center justify-center border",
                                        isReady ? "bg-brand-accent/10 border-brand-accent/20" : "bg-black/20 border-white/10"
                                    )}>
                                        <Sparkles className={isReady ? "text-brand-accent animate-pulse" : "text-slate-600"} size={20} />
                                    </div>
                                    <div>
                                        <p className="text-white font-black uppercase italic tracking-tighter text-base leading-none mb-1">{egg.name}</p>
                                        <div className="flex items-center gap-2">
                                            {isIncubating && !isReady && (
                                                <>
                                                    <Timer size={10} className="text-brand-accent" />
                                                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{egg.remaining_mins}m Left</span>
                                                </>
                                            )}
                                            {isReady && (
                                                <>
                                                    <CheckCircle2 size={10} className="text-brand-accent" />
                                                    <span className="text-[9px] font-black text-brand-accent uppercase tracking-widest">Ready to Hatch</span>
                                                </>
                                            )}
                                            {isFresh && (
                                                <>
                                                    <Zap size={10} className="text-slate-600" />
                                                    <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Fresh Egg</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {isFresh && (
                                    <button
                                        onClick={() => handleIncubate(egg.id)}
                                        disabled={!!actionId}
                                        className="bg-white/5 border border-white/10 text-white text-[9px] font-black px-5 py-2.5 rounded-xl uppercase tracking-widest active:scale-95 transition-all flex items-center gap-2"
                                    >
                                        {actionId === egg.id ? <Loader2 size={12} className="animate-spin" /> : <>Start <ArrowRight size={12} /></>}
                                    </button>
                                )}

                                {isIncubating && !isReady && (
                                    <div className="bg-brand-accent/5 border border-brand-accent/10 text-brand-accent text-[9px] font-black px-5 py-2.5 rounded-xl uppercase tracking-widest opacity-60">
                                        Incubating
                                    </div>
                                )}

                                {isReady && (
                                    <button
                                        onClick={() => handleHatch(egg.id)}
                                        disabled={!!actionId}
                                        className="bg-brand-accent text-brand-midnight text-[9px] font-black px-6 py-2.5 rounded-xl uppercase tracking-widest active:scale-95 transition-all shadow-lg shadow-brand-accent/20"
                                    >
                                        {actionId === egg.id ? <Loader2 size={12} className="animate-spin" /> : 'Hatch'}
                                    </button>
                                )}
                            </div>
                        );
                    }) : (
                        <div className="glass-panel p-10 rounded-[2.5rem] border border-white/5 text-center flex flex-col items-center">
                            <Zap size={32} className="text-slate-800 mb-4" />
                            <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest leading-relaxed">
                                No eggs detected in your inventory.<br/>Hunt in the matrix to find them.
                            </p>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};
