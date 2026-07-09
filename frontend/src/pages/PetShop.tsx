import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useUser, Pet } from '../context/UserContext';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { formatNumber, cn } from '../utils';
import { Bone, Lock, CheckCircle2, Loader2, PawPrint, Sparkles, Gem } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

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
        <div className={cn(className, 'flex items-center justify-center text-neutral-800 bg-brand-surface')}>
            <PawPrint size={32} />
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
            `SECURE ${pet.name.toUpperCase()}? THIS WILL SET IT AS YOUR ACTIVE COMPANION.`,
            async (confirmed) => {
                if (confirmed) {
                    setBuying(petRef);
                    try {
                        await apiFetch(`/shop/buy/pet/${encodeURIComponent(petRef)}`, { method: 'POST' });
                        addToast(`Successfully acquired ${pet.name}.`, 'success');
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
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-4">
            <Skeleton className="h-8 w-48 rounded-lg" />
            {[1,2,3].map(i => <Skeleton key={i} className="h-32 rounded-2xl" />)}
        </div>
    );

    if (error && !shopData) return (
        <div className="px-4 py-12 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchPets} />
        </div>
    );

    const pets = shopData?.pets || [];
    const ownedIds = shopData?.owned_ids || [];
    const currentLevel = shopData?.current_level || 0;
    const zenithBalance = user?.stats?.zenith ?? user?.zenith ?? 0;

    return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
            <header className="space-y-1">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                        <Bone className="text-brand-accent" size={22} />
                   </div>
                   <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Pet Breeder</h1>
                </div>
                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
                    Acquire powerful companions to enhance your journey.
                </p>
            </header>

            <div className="grid grid-cols-1 gap-4">
                {pets.map((pet, i) => {
                    const petRef = getPetRef(pet);
                    const reqLevel = pet.req_level || 0;
                    const price = pet.zenith_price || 0;
                    const isOwned = ownedIds.includes(petRef) || ownedIds.includes(pet.id) || (shopData?.owned || []).includes(pet.name);
                    const isLocked = !isOwned && currentLevel < reqLevel;
                    const canAfford = zenithBalance >= price;

                    return (
                        <Card
                            key={pet.id || pet.name}
                            variant={isOwned ? "outline" : "default"}
                            onClick={() => onPetClick?.({ ...pet, shopIndex: i })}
                            className={cn(
                                "p-4 flex gap-5 items-center group cursor-pointer relative",
                                isOwned && "border-emerald-500/30 bg-emerald-500/5",
                                isLocked && "opacity-60"
                            )}
                        >
                            <div className="relative shrink-0">
                                <div className={cn(
                                    "w-24 h-24 sm:w-28 sm:h-28 rounded-2xl overflow-hidden border-2 bg-brand-midnight shadow-xl group-hover:scale-105 transition-all duration-500",
                                    isOwned ? "border-emerald-500/40" : "border-white/10"
                                )}>
                                    <PetShopImage pet={pet} className="w-full h-full object-cover" />
                                </div>
                                {isOwned && (
                                    <div className="absolute -top-2 -right-2 bg-emerald-500 text-white p-1.5 rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.5)] border border-emerald-400 z-10">
                                        <CheckCircle2 size={16} strokeWidth={3} />
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 min-w-0 space-y-3">
                                <div>
                                    <h2 className="text-xl font-black text-white truncate uppercase tracking-tight">{pet.name}</h2>
                                    <div className="flex items-center gap-1.5 mt-1">
                                        <Sparkles size={12} className="text-brand-accent shrink-0" />
                                        <p className="text-[11px] font-bold text-brand-accent uppercase tracking-wider truncate">{pet.ability}</p>
                                    </div>
                                </div>

                                <div className="flex items-end justify-between gap-4">
                                    <div className="space-y-1">
                                        <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest block">Cost</span>
                                        <div className="flex items-center gap-1.5">
                                            <Gem size={14} className="text-brand-accent" />
                                            <span className="text-sm font-black text-white tabular-nums">{formatNumber(price)}</span>
                                        </div>
                                    </div>

                                    {!isOwned && !isLocked && (
                                        <Button
                                            variant={canAfford ? "primary" : "secondary"}
                                            size="sm"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleBuy(pet);
                                            }}
                                            isLoading={buying === petRef}
                                            disabled={!canAfford}
                                            className="px-6 rounded-xl uppercase tracking-widest text-[10px] font-black"
                                        >
                                            {canAfford ? 'Acquire' : 'Insufficient'}
                                        </Button>
                                    )}

                                    {isOwned && (
                                        <Badge variant="success" className="py-1.5 px-4 rounded-xl font-black tracking-widest uppercase">
                                            Secured
                                        </Badge>
                                    )}

                                    {isLocked && (
                                        <div className="flex flex-col items-end gap-1">
                                            <Badge variant="secondary" icon={Lock} className="py-1.5 px-4 rounded-xl font-black tracking-widest uppercase">
                                                Locked
                                            </Badge>
                                            <span className="text-[9px] font-black text-neutral-600 uppercase">REACH LVL {reqLevel}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
};
