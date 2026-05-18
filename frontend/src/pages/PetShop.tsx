import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { formatNumber } from '../utils';

interface PetShopProps {
    onPetClick?: (pet: any) => void;
}

export const PetShop = ({ onPetClick }: PetShopProps) => {
    const { data: pets, loading } = useApi<any[]>('/shop/pets');

    if (loading) return (
        <div className="grid grid-cols-2 gap-4 px-4 py-8">
            {[1,2,3,4].map(i => <Skeleton key={i} className="h-48 rounded-3xl" />)}
        </div>
    );

    return (
        <div className="px-4 py-8">
            <h1 className="text-2xl font-black italic uppercase tracking-tighter text-white mb-8 px-2">Companion Hub</h1>
            <div className="grid grid-cols-1 gap-6">
                {pets?.map((pet, i) => (
                    <div
                        key={pet.name}
                        onClick={() => onPetClick?.(pet)}
                        style={{ transitionDelay: `${Math.min(i * 0.05, 0.3)}s` }}
                        className="glass-panel p-6 rounded-[2.5rem] border border-white/5 flex gap-6 items-center animate-in fade-in slide-in-from-bottom-4 duration-500"
                    >
                        <div className="w-24 h-24 rounded-3xl overflow-hidden border-2 border-brand-accent/20 bg-black/40">
                            <img src={pet.img} alt={pet.name} className="w-full h-full object-cover" />
                        </div>
                        <div className="flex-1">
                            <h2 className="text-xl font-black text-white italic tracking-tighter">{pet.name}</h2>
                            <p className="text-[10px] font-bold text-brand-accent uppercase tracking-widest mb-3">{pet.ability}</p>
                            <div className="flex items-center gap-2">
                                <span className="text-[12px] font-black text-white">⧫ {formatNumber(pet.zenith_price)}</span>
                                <button className="px-4 py-1.5 bg-brand-accent text-brand-midnight text-[10px] font-black rounded-full uppercase tracking-widest active:scale-95 transition-all">Buy</button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
