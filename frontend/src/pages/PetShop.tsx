import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useUser, Pet } from '../context/UserContext';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { formatNumber, cn } from '../utils';
import { Bone, Lock, CheckCircle2, Loader2, PawPrint, Sparkles } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';

interface PetShopProps {
    onPetClick?: (pet: Pet) => void;
}

interface PetShopResponse {
    pets: Pet[];
    owned: string[];
    owned_ids?: string[];
    current_level: number;
}

const getPetRef = (pet: Pet) => String(pet.petid || pet.id || pet.name || '');

const getPetImageSrc = (pet: Pet) => {
    const src = String(pet.img || pet.img_url || pet.image || pet.photo_url || '').trim();
    return /^https?:\/\//i.test(src) || src.startsWith('/') ? src : '';
};

const PetShopImage = ({ pet, className }: { pet: Pet; className?: string }) => {
    const src = getPetImageSrc(pet);
    const [imageFailed, setImageFailed] = useState(false);

    useEffect(() => {
        setImageFailed(false);
    }, [src]);

    return src && !imageFailed ? (
        <img
            key={src}
            src={src}
            alt={pet.name}
            className={className}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setImageFailed(true)}
        />
    ) : (
        <div className={cn(className, 'flex items-center justify-center text-neutral-700')}>
            <PawPrint size={22} />
        </div>
    );
};

export const PetShop = ({ onPetClick }: PetShopProps) => {
    const { user, triggerRefresh } = useUser();
    const { addToast } = useToast();
    const { data: shopData, loading, error, execute: fetchPets } = useApi<PetShopResponse>('/shop/pets');
    const [buying, setBuying] = useState<string | null>(null);

    const handleBuy = async (pet: Pet) => {
        if (buying) return;
        const petRef = getPetRef(pet);

        window.Telegram?.WebApp?.showConfirm(
            `Buy ${pet.name}? It will become your active pet.`,
            async (confirmed) => {
                if (confirmed) {
                    setBuying(petRef);
                    try {
                        await apiFetch(`/shop/buy/pet/${encodeURIComponent(petRef)}`, { method: 'POST' });
                        addToast(`Successfully bought ${pet.name}.`, 'success');
                        triggerRefresh();
                    } catch (err: any) {
                        addToast(getErrorMessage(err), 'error');
                    } finally {
                        setBuying(null);
                    }
                }
            }
        );
    };

    if (loading && !shopData) return (
        <div className="grid grid-cols-1 gap-4 px-4 py-8 max-w-2xl mx-auto">
            {[1,2,3,4].map(i => <Skeleton key={i} className="h-40 rounded-xl" />)}
        </div>
    );

    if (error && !shopData) return (
        <div className="px-4 py-8 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchPets} />
        </div>
    );

    const pets = shopData?.pets || [];
    const owned = shopData?.owned || [];
    const ownedIds = shopData?.owned_ids || [];
    const currentLevel = shopData?.current_level || 0;
    const zenithBalance = user?.stats?.zenith ?? user?.zenith ?? 0;

    return (
        <div className="px-4 py-6 pb-20 max-w-2xl mx-auto">
            <header className="mb-8 border-b border-white/5 pb-4">
                <h1 className="text-xl font-bold text-white flex items-center gap-2 mb-1">
                    <Bone className="text-brand-accent" size={20} />
                    Pet Store
                </h1>
                <p className="text-sm font-medium text-neutral-400">Buy pets and choose one to stay active.</p>
            </header>

            <div className="grid grid-cols-1 gap-4">
                {pets.map((pet, i) => {
                    const petRef = getPetRef(pet);
                    const reqLevel = pet.req_level || 0;
                    const price = pet.zenith_price || 0;
                    const isOwned = ownedIds.includes(petRef) || ownedIds.includes(pet.id) || owned.includes(pet.name);
                    const isLocked = !isOwned && currentLevel < reqLevel;
                    const canAfford = zenithBalance >= price;

                    return (
                        <div
                            key={pet.id || pet.name}
                            onClick={() => onPetClick?.({ ...pet, shopIndex: i })}
                            className={cn(
                                "p-4 rounded-xl border transition-all flex gap-4 items-center group cursor-pointer shadow-sm",
                                isOwned ? "border-emerald-500/20 bg-emerald-500/5" : "border-white/5 bg-brand-deep",
                                isLocked && "opacity-60 grayscale-[0.3]"
                            )}
                        >
                            <div className="relative shrink-0">
                                <div className={cn(
                                    "w-20 h-20 sm:w-24 sm:h-24 rounded-xl overflow-hidden border-2 bg-brand-midnight shadow-md group-hover:scale-105 transition-transform duration-300",
                                    isOwned ? "border-emerald-500/30" : "border-white/10"
                                )}>
                                    <PetShopImage pet={pet} className="w-full h-full object-cover" />
                                </div>
                                {isOwned && (
                                    <div className="absolute -top-1.5 -right-1.5 bg-emerald-500 text-white p-1 rounded-lg shadow-sm border border-emerald-400">
                                        <CheckCircle2 size={14} strokeWidth={3} />
                                    </div>
                                )}
                                {isLocked && (
                                    <div className="absolute inset-0 bg-black/60 rounded-xl flex flex-col items-center justify-center text-white/60 backdrop-blur-[2px]">
                                        <Lock size={18} className="mb-1" />
                                        <span className="text-[10px] font-bold uppercase tracking-wider">Lvl {reqLevel}</span>
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 min-w-0 py-1">
                                <h2 className="text-lg font-bold text-white mb-1 truncate">{pet.name}</h2>
                                <div className="flex items-center gap-1.5 mb-3">
                                    <Sparkles size={12} className="text-brand-accent shrink-0" />
                                    <p className="text-xs font-semibold text-brand-accent truncate">{pet.ability}</p>
                                </div>

                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex flex-col min-w-0">
                                        <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider mb-0.5">Price</span>
                                        <span className="text-sm font-bold text-white tabular-nums">{formatNumber(price)} Zenith</span>
                                    </div>

                                    {!isOwned && !isLocked && (
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleBuy(pet);
                                            }}
                                            disabled={!!buying || !canAfford}
                                            className={cn(
                                                "px-4 py-2 rounded-lg text-xs font-bold transition-all active:scale-95 shadow-sm min-w-[80px] flex justify-center",
                                                canAfford
                                                    ? "bg-white text-brand-midnight hover:bg-neutral-200"
                                                    : "bg-brand-midnight text-neutral-600 border border-white/5"
                                            )}
                                        >
                                            {buying === petRef ? <Loader2 size={14} className="animate-spin" /> : canAfford ? 'Buy' : 'Need more'}
                                        </button>
                                    )}

                                    {isOwned && (
                                        <span className="text-xs font-bold text-emerald-500 px-3 py-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">Owned</span>
                                    )}

                                    {isLocked && (
                                        <span className="text-xs font-bold text-neutral-500 px-3 py-1.5 bg-brand-midnight rounded-lg border border-white/5">Locked</span>
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
