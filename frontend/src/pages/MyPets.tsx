import React, { useState } from 'react';
import { useUser, Pet } from '../context/UserContext';
import { apiFetch } from '../api/client';
import { useToast } from '../components/ui/Toast';
import {
    PawPrint,
    Zap,
    Heart,
    Shield,
    Activity,
    Star,
    ChevronRight,
    Loader2
} from 'lucide-react';
import { cn } from '../utils';
import { ProgressBar } from '../components/ui/ProgressBar';

interface MyPetsProps {
    onPetClick?: (pet: Pet) => void;
}

export const MyPets = ({ onPetClick }: MyPetsProps) => {
    const { user, triggerRefresh } = useUser();
    const { addToast } = useToast();
    const [switching, setSwitching] = useState<string | null>(null);

    const handleSetActive = async (petName: string) => {
        if (switching) return;
        setSwitching(petName);
        try {
            await apiFetch(`/pets/set_active/${petName}`, { method: 'POST' });
            addToast(`${petName} is now your active pet!`, 'success');
            triggerRefresh();
        } catch (err: any) {
            addToast(err.message || 'Failed to switch pet', 'error');
        } finally {
            setSwitching(null);
        }
    };

    if (!user) return null;

    const pets = user.pets || [];
    const currentPet = user.current_pet;

    return (
        <div className="px-4 py-8 pb-20">
            <header className="mb-8 px-2">
                <h1 className="text-2xl font-black italic uppercase tracking-tighter text-white flex items-center gap-3">
                    <PawPrint className="text-brand-accent" size={24} />
                    My Companions
                </h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.3em] mt-1">Manage your battle-hardened pets</p>
            </header>

            {/* Active Pet Hero Card */}
            {currentPet && (
                <section className="mb-10">
                    <h2 className="px-2 text-[10px] font-black uppercase tracking-widest text-brand-accent/60 mb-4 flex items-center gap-2">
                        <Zap size={10} /> Active Partner
                    </h2>
                    <div className="glass-panel p-6 rounded-[2.5rem] border border-brand-accent/20 bg-brand-accent/5 relative overflow-hidden">
                        <div className="relative z-10 flex gap-6 items-center">
                            <div className="w-28 h-28 rounded-3xl overflow-hidden border-2 border-brand-accent/30 bg-black/40 shadow-2xl">
                                <img src={currentPet.img} alt={currentPet.name} className="w-full h-full object-cover" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-2xl font-black text-white italic tracking-tighter leading-none mb-1">{currentPet.name}</h3>
                                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-brand-accent/20 border border-brand-accent/20 mb-3">
                                    <Star size={10} className="text-brand-accent fill-brand-accent" />
                                    <span className="text-[9px] font-black text-brand-accent uppercase tracking-widest">Level {currentPet.level}</span>
                                </div>

                                <div className="grid grid-cols-2 gap-3 mb-4">
                                    <div className="flex items-center gap-2">
                                        <div className="p-1.5 rounded-lg bg-red-500/10 text-red-500 border border-red-500/10">
                                            <Heart size={12} fill="currentColor" />
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-[8px] font-bold text-slate-500 uppercase">HP</span>
                                            <span className="text-xs font-black text-white">{currentPet.hp}</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-500 border border-blue-500/10">
                                            <Shield size={12} />
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-[8px] font-bold text-slate-500 uppercase">Ability</span>
                                            <span className="text-[10px] font-black text-white leading-tight">{currentPet.ability}</span>
                                        </div>
                                    </div>
                                </div>

                                <ProgressBar
                                    current={currentPet.xp}
                                    total={currentPet.xp_needed}
                                    compact
                                />
                            </div>
                        </div>
                        {/* Background Decoration */}
                        <PawPrint className="absolute -bottom-6 -right-6 text-brand-accent/5 w-32 h-32 rotate-12" />
                    </div>
                </section>
            )}

            {/* Pets List */}
            <section>
                <div className="flex items-center justify-between px-2 mb-4">
                    <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Your Collection</h2>
                    <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">{pets.length} Owned</span>
                </div>

                <div className="space-y-3">
                    {pets.length > 0 ? (
                        pets.map((pet) => {
                            const isActive = currentPet?.name === pet.name;
                            return (
                                <div
                                    key={pet.name}
                                    onClick={() => onPetClick?.(pet)}
                                    className={cn(
                                        "glass-panel p-4 rounded-2xl border transition-all flex items-center gap-4 active:scale-[0.98]",
                                        isActive ? "border-brand-accent/30 bg-brand-accent/5" : "border-white/5 bg-white/5"
                                    )}
                                >
                                    <div className="w-14 h-14 rounded-xl overflow-hidden border border-white/10 bg-black/20 shrink-0">
                                        <img src={pet.img} alt={pet.name} className="w-full h-full object-cover" />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <h4 className="text-[13px] font-black text-white uppercase italic tracking-tight truncate">{pet.name}</h4>
                                        <div className="flex items-center gap-3 mt-0.5">
                                            <div className="flex items-center gap-1">
                                                <Activity size={10} className="text-slate-500" />
                                                <span className="text-[9px] font-bold text-slate-500 uppercase">Lv.{pet.level}</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Heart size={10} className="text-brand-accent" />
                                                <span className="text-[9px] font-bold text-slate-500 uppercase">{pet.affection}%</span>
                                            </div>
                                        </div>
                                    </div>

                                    {!isActive && (
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleSetActive(pet.name);
                                            }}
                                            disabled={!!switching}
                                            className="px-4 py-2 bg-white/5 border border-white/10 text-[9px] font-black text-white uppercase tracking-widest rounded-xl hover:bg-brand-accent hover:text-brand-midnight hover:border-brand-accent transition-all disabled:opacity-50"
                                        >
                                            {switching === pet.name ? <Loader2 size={12} className="animate-spin" /> : 'Activate'}
                                        </button>
                                    )}
                                    {isActive && (
                                        <div className="p-2 text-brand-accent">
                                            <CheckCircle2 size={18} />
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    ) : (
                        <div className="glass-panel p-12 rounded-[2.5rem] border border-white/5 text-center flex flex-col items-center">
                            <PawPrint size={40} className="text-slate-800 mb-4" />
                            <h3 className="text-sm font-black text-white uppercase tracking-widest mb-2">Lonely Journey</h3>
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-relaxed">
                                You don't have any pets yet.<br/>Visit the Pet Store to find a partner.
                            </p>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};

const CheckCircle2 = ({ size, className }: { size?: number, className?: string }) => (
    <svg
        width={size || 24}
        height={size || 24}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="M20 6 9 17l-5-5" />
    </svg>
);
