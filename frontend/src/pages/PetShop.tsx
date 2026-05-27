import React, { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useUser, Pet } from '../context/UserContext';
import { Skeleton } from '../components/ui/Skeleton';
import { formatNumber, cn } from '../utils';
import { ShoppingBag, Lock, CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import { apiFetch } from '../api/client';
import { useToast } from '../components/ui/Toast';

interface PetShopProps {
    onPetClick?: (pet: Pet) => void;
}

interface PetShopResponse {
    pets: Pet[];
    owned: string[];
    current_level: number;
}

export const PetShop = ({ onPetClick }: PetShopProps) => {
    const { user, triggerRefresh } = useUser();
    const { addToast } = useToast();
    const { data: shopData, loading } = useApi<PetShopResponse>('/shop/pets');
    const [buying, setBuying] = useState<string | null>(null);

    const handleBuy = async (petName: string, index: number) => {
        if (buying) return;

        window.Telegram?.WebApp?.showConfirm(
            `Unlock ${petName}? This will instantly set it as your active pet.`,
            async (confirmed) => {
                if (confirmed) {
                    setBuying(petName);
                    try {
                        await apiFetch(`/shop/buy/pet/${index}`, { method: 'POST' });
                        addToast(`Successfully acquired ${petName}!`, 'success');
                        triggerRefresh();
                    } catch (err: any) {
                        addToast(err.message || 'Purchase failed', 'error');
                    } finally {
                        setBuying(null);
                    }
                }
            }
        );
    };

    if (loading && !shopData) return (
        <div className="grid grid-cols-1 gap-4 px-4 py-8">
            {[1,2,3,4].map(i => <Skeleton key={i} className="h-48 rounded-3xl" />)}
        </div>
    );

    const pets = shopData?.pets || [];
    const owned = shopData?.owned || [];
    const currentLevel = shopData?.current_level || 0;

    return (
        <div className="px-4 py-8 pb-20">
            <header className="mb-10 px-2">
                <h1 className="text-2xl font-black italic uppercase tracking-tighter text-white flex items-center gap-3">
                    <ShoppingBag className="text-brand-accent" size={24} />
                    Companion Hub
                </h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.3em] mt-1">Acquire elite pets for your journey</p>
            </header>

            <div className="grid grid-cols-1 gap-6">
                {pets.map((pet, i) => {
                    const isOwned = owned.includes(pet.name);
                    const isLocked = currentLevel < pet.req_level;
                    const canAfford = (user?.zenith || 0) >= pet.zenith_price;

                    return (
                        <div
                            key={pet.name}
                            onClick={() => onPetClick?.(pet)}
                            style={{ transitionDelay: `${Math.min(i * 0.05, 0.3)}s` }}
                            className={cn(
                                "glass-panel p-5 rounded-[2.5rem] border transition-all duration-500 flex gap-6 items-center group animate-in fade-in slide-in-from-bottom-4 fill-mode-both",
                                isOwned ? "border-brand-accent/20 bg-brand-accent/5" : "border-white/5 bg-white/5",
                                isLocked && "opacity-60 grayscale-[0.5]"
                            )}
                        >
                            <div className="relative shrink-0">
                                <div className={cn(
                                    "w-24 h-24 rounded-[1.75rem] overflow-hidden border-2 bg-black/40 shadow-xl group-hover:scale-105 transition-transform duration-500",
                                    isOwned ? "border-brand-accent/40" : "border-white/10"
                                )}>
                                    <img src={pet.img} alt={pet.name} className="w-full h-full object-cover" />
                                </div>
                                {isOwned && (
                                    <div className="absolute -top-2 -right-2 bg-brand-accent text-brand-midnight p-1.5 rounded-xl shadow-lg ring-4 ring-brand-midnight">
                                        <CheckCircle2 size={12} strokeWidth={3} />
                                    </div>
                                )}
                                {isLocked && (
                                    <div className="absolute inset-0 bg-black/60 rounded-[1.75rem] flex flex-col items-center justify-center text-white/40">
                                        <Lock size={20} />
                                        <span className="text-[8px] font-black uppercase mt-1">Lvl {pet.req_level}</span>
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl font-black text-white italic tracking-tighter leading-tight mb-0.5 truncate">{pet.name}</h2>
                                <div className="flex items-center gap-1.5 mb-3">
                                    <Sparkles size={10} className="text-brand-accent" />
                                    <p className="text-[9px] font-black text-brand-accent uppercase tracking-widest truncate">{pet.ability}</p>
                                </div>

                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex flex-col">
                                        <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">Price</span>
                                        <span className="text-[13px] font-black text-white">⧫ {formatNumber(pet.zenith_price)}</span>
                                    </div>

                                    {!isOwned && !isLocked && (
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleBuy(pet.name, i);
                                            }}
                                            disabled={!!buying || !canAfford}
                                            className={cn(
                                                "px-6 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-lg",
                                                canAfford
                                                    ? "bg-brand-accent text-brand-midnight hover:shadow-brand-accent/20"
                                                    : "bg-white/5 text-slate-600 border border-white/5"
                                            )}
                                        >
                                            {buying === pet.name ? <Loader2 size={14} className="animate-spin mx-2" /> : 'Buy Now'}
                                        </button>
                                    )}

                                    {isOwned && (
                                        <span className="text-[9px] font-black text-brand-accent/60 uppercase tracking-[0.2em] px-4 py-2 bg-brand-accent/5 rounded-xl border border-brand-accent/10">Owned</span>
                                    )}

                                    {isLocked && (
                                        <span className="text-[9px] font-black text-slate-600 uppercase tracking-[0.2em] px-4 py-2 bg-white/5 rounded-xl border border-white/5">Locked</span>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
