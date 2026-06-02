import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Loader2, Heart, Zap, X, Swords, Wind, Sparkles, Check, Lock } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { apiFetch, getErrorMessage } from '../../api/client';
import { cn } from '../../utils';
import { useUser } from '../../context/UserContext';

const StatBox = ({ icon: Icon, label, value, colorClass }) => (
    <div className="bg-white/[0.03] border border-white/5 p-4 rounded-2xl flex items-center space-x-3">
        <div className={`p-2 rounded-xl bg-black/20 ${colorClass}`}>
            <Icon size={16} />
        </div>
        <div>
            <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">{label}</p>
            <p className="text-[12px] font-black text-white">{value}</p>
        </div>
    </div>
);

export const PetActionModal = ({ selectedPet, setSelectedPet, user }) => {
    const { addToast } = useToast();
    const { triggerRefresh, liteMode } = useUser();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [syncStage, setSyncStage] = useState('idle');

    useEffect(() => {
        if (!selectedPet) {
            setPurchaseStage('idle');
            setSyncStage('idle');
        }
    }, [selectedPet]);

    if (!selectedPet) return null;

    const ownedPets = user?.pets || [];
    const selectedRef = selectedPet.id || selectedPet.name;
    const isOwned = ownedPets.some(p => (p.id || p.name) === selectedRef || p.name === selectedPet.name);
    const isActive = (user?.current_pet?.id || user?.current_pet?.name) === selectedRef;
    const isLocked = (user?.stats?.level || 0) < (selectedPet.req_level || 0);
    const zenithBalance = user?.stats?.zenith ?? user?.zenith ?? 0;
    const canAfford = zenithBalance >= (selectedPet.zenith_price || 0);

    const handleBuy = async () => {
        setPurchaseStage('buying');
        try {
            await apiFetch(`/shop/buy/pet/${selectedPet.shopIndex}`, { method: 'POST' });
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            addToast(`Acquired ${selectedPet.name}!`, 'success');
            triggerRefresh();
            setSelectedPet(null);
        } catch (err) {
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
            addToast(getErrorMessage(err), 'error');
            setPurchaseStage('idle');
        }
    };

    const handleSync = async () => {
        setSyncStage('syncing');
        try {
            await apiFetch(`/pets/set_active/${encodeURIComponent(selectedRef)}`, { method: 'POST' });
            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
            addToast(`${selectedPet.name} is now active`, 'success');
            triggerRefresh();
            setSelectedPet(null);
        } catch (err) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setSyncStage('idle');
        }
    };

    return (
        <div className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center p-0 sm:p-4">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedPet(null)}
                className={cn(
                    "absolute inset-0 bg-brand-midnight/90",
                    !liteMode && "backdrop-blur-2xl"
                )}
            />

            <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={liteMode 
                    ? { duration: 0.2 }
                    : { type: "spring", damping: 25, stiffness: 200 }
                }
                className="relative w-full max-w-[500px] bg-brand-midnight border-t sm:border border-white/10 rounded-t-2xl sm:rounded-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
                <div className="p-8 overflow-y-auto no-scrollbar">
                    <div className="flex justify-between items-start mb-8">
                        <div className="w-24 h-24 rounded-xl overflow-hidden border-2 border-brand-accent/20 bg-black/40 shadow-2xl">
                            <img src={selectedPet.img} alt={selectedPet.name} className="w-full h-full object-cover" />
                        </div>
                        <button
                            onClick={() => setSelectedPet(null)}
                            className="w-10 h-10 rounded-2xl bg-white/5 flex items-center justify-center text-slate-500"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="mb-8">
                        <div className="flex items-center gap-3 mb-2 min-w-0">
                            <h2 className="text-3xl font-black text-white italic tracking-tighter uppercase truncate min-w-0">{selectedPet.name}</h2>
                            <span className="px-2 py-0.5 rounded-lg bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[8px] font-black uppercase tracking-widest shrink-0">
                                {selectedPet.rarity || 'Pet'}
                            </span>
                        </div>
                        <p className="text-xs font-semibold text-slate-500">Companion pet</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-10">
                        <StatBox icon={Swords} label="Ability" value={selectedPet.ability || 'None'} colorClass="text-brand-accent" />
                        <StatBox icon={Heart} label="Affection" value={`${selectedPet.affection ?? 0}%`} colorClass="text-red-500" />
                        <StatBox icon={Wind} label="Speed" value={selectedPet.spd ?? 0} colorClass="text-blue-400" />
                        <StatBox icon={Activity} label="Level" value={selectedPet.level || 1} colorClass="text-emerald-400" />
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center space-x-2 text-brand-accent mb-4">
                            <Sparkles size={12} className="text-brand-accent" />
                            <span className="text-[10px] font-black uppercase tracking-widest">Active Ability</span>
                        </div>
                        <p className="text-[12px] text-slate-300 leading-relaxed font-medium">
                            {selectedPet.desc || `${selectedPet.name} gives you a practical bonus while it is your active pet.`}
                        </p>
                    </div>
                </div>

                <div className="p-8 pt-0 mt-auto">
                    {isActive ? (
                         <div className="w-full py-5 rounded-xl bg-brand-accent/10 text-brand-accent border border-brand-accent/20 font-bold text-sm flex items-center justify-center gap-3">
                             <Check size={16} />
                             <span>Currently active</span>
                         </div>
                    ) : isOwned ? (
                        <button
                            onClick={handleSync}
                            disabled={syncStage === 'syncing'}
                            className="w-full py-5 rounded-xl bg-white text-brand-midnight font-bold text-sm shadow-xl active:scale-95 transition-all flex items-center justify-center gap-3"
                        >
                            {syncStage === 'syncing' ? <Loader2 size={16} className="animate-spin" /> : 'Set active pet'}
                        </button>
                    ) : isLocked ? (
                        <div className="w-full py-5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm font-bold flex items-center justify-center gap-3">
                            <Lock size={16} />
                            <span>Requires Level {selectedPet.req_level}</span>
                        </div>
                    ) : (
                        <div className="w-full">
                            {purchaseStage === 'idle' ? (
                                <button
                                    onClick={() => {
                                        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                                        setPurchaseStage('confirm');
                                    }}
                                    disabled={!canAfford}
                                    className="w-full py-5 rounded-xl bg-brand-accent text-brand-midnight font-bold text-sm shadow-xl shadow-brand-accent/20 active:scale-95 transition-all flex items-center justify-center gap-3"
                                >
                                    {canAfford ? `Buy for ${selectedPet.zenith_price} Zenith` : `${Math.max(0, (selectedPet.zenith_price || 0) - zenithBalance)} more Zenith needed`} <Zap size={16} />
                                </button>
                            ) : (
                                <div className="p-1 glass-panel rounded-xl border border-brand-accent/20 flex space-x-1">
                                    <button
                                        onClick={() => setPurchaseStage('idle')}
                                        className="flex-1 py-4 text-sm font-bold text-slate-500"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleBuy}
                                        disabled={purchaseStage === 'buying'}
                                        className="flex-[2] py-4 bg-brand-accent text-brand-midnight rounded-lg text-sm font-bold flex items-center justify-center gap-2"
                                    >
                                        {purchaseStage === 'buying' ? <Loader2 size={16} className="animate-spin" /> : 'Confirm purchase'}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};
