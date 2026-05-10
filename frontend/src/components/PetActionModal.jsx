import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Loader2, Heart, Zap, X, Swords, Wind, Sparkles, Check, Lock } from 'lucide-react';
import { useToast } from './UI';
import { apiFetch } from '../api';
import { cn } from '../utils';

const StatBox = ({ icon: Icon, label, value, colorClass }) => (
    <div className="bg-white/[0.03] border border-white/5 p-4 rounded-2xl flex items-center space-x-3">
        <div className={cn("p-2 rounded-xl bg-opacity-10", colorClass.replace('text-', 'bg-'))}>
            <Icon size={16} className={colorClass} />
        </div>
        <div>
            <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">{label}</p>
            <p className="text-sm font-black text-white font-mono">{value}</p>
        </div>
    </div>
);

export const PetActionModal = ({ selectedPet, setSelectedPet, user, onPurchaseSuccess }) => {
    const { addToast } = useToast();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [setStage, setSetStage] = useState('idle');

    useEffect(() => {
        let mounted = true;
        if (!selectedPet && mounted) {
            // Wrap in microtask to avoid cascading render warning
            Promise.resolve().then(() => {
                if (mounted) {
                    setPurchaseStage('idle');
                    setSetStage('idle');
                }
            });
            document.body.classList.remove('no-scroll');
        } else if (mounted) {
            document.body.classList.add('no-scroll');
        }
        return () => { mounted = false; };
    }, [selectedPet]);

    if (!selectedPet) return null;

    const isOwned = selectedPet.owned;
    const isActive = user?.current_pet?.name === selectedPet.name;
    const isLocked = !isOwned && (user?.stats?.level || 1) < selectedPet.req_level;

    const handleSetPet = async () => {
        setSetStage('setting');
        try {
            await apiFetch(`/pets/set_active/${selectedPet.name}`, { method: 'POST' });
            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
            addToast(`${selectedPet.name} Synced to Core`, 'success');
            window.dispatchEvent(new CustomEvent('user-data-refresh'));
            setSelectedPet(null);
        } catch (err) {
            addToast(err.message || 'Sync failed', 'error');
        } finally {
            setSetStage('idle');
        }
    };

    const handleBuy = async () => {
        setPurchaseStage('buying');
        try {
            await apiFetch(`/shop/buy/pet/${selectedPet.shopIndex}`, { method: 'POST' });
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            addToast(`Bought ${selectedPet.name}!`, 'success');
            window.dispatchEvent(new CustomEvent('user-data-refresh'));
            window.dispatchEvent(new CustomEvent('shop-data-refresh'));
            if (onPurchaseSuccess) onPurchaseSuccess();
            setSelectedPet(null);
        } catch (err) {
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
            addToast(err.message || 'Purchase failed', 'error');
            setPurchaseStage('idle');
        }
    };

    return (
        <AnimatePresence>
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[110] flex items-center justify-center bg-brand-midnight/95 backdrop-blur-2xl px-4"
            >
                <div className="absolute inset-0" onClick={() => setSelectedPet(null)} />

                <motion.div 
                    initial={{ scale: 0.9, opacity: 0, y: 50 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 50 }}
                    transition={{ type: "spring", damping: 25, stiffness: 200 }}
                    className="relative w-full max-w-md bg-brand-midnight border border-white/10 rounded-[3rem] overflow-hidden shadow-lg flex flex-col max-h-[90vh]"
                >
                    <button 
                        onClick={() => setSelectedPet(null)}
                        className="absolute top-6 right-6 z-50 w-10 h-10 rounded-2xl bg-white/5 flex items-center justify-center text-white/40 active:scale-90"
                    >
                        <X size={20} />
                    </button>

                    <div className="overflow-y-auto no-scrollbar pb-10">
                        <div className="relative aspect-video w-full p-4 bg-gradient-to-b from-brand-accent/5 to-transparent">
                            <img 
                                src={selectedPet.img} 
                                className="w-full h-full object-contain drop-shadow-[0_0_30px_rgba(0,242,255,0.2)]" 
                                alt={selectedPet.name} 
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-transparent" />
                        </div>

                        <div className="px-8 -mt-6 relative z-10 text-center">
                            <div className="inline-block px-3 py-1 rounded-full bg-brand-accent/10 border border-brand-accent/20 mb-3">
                                <span className="text-[9px] font-black uppercase tracking-[0.2em] text-brand-accent">Companion Hub</span>
                            </div>
                            <h2 className="text-3xl font-black text-white uppercase tracking-tight mb-1">{selectedPet.name}</h2>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-8">
                                {selectedPet.ability || 'Standard Companion'}
                            </p>

                            <div className="grid grid-cols-2 gap-3 mb-10">
                                <StatBox icon={Heart} label="Vitality" value={selectedPet.hp || 100} colorClass="text-red-400" />
                                <StatBox icon={Swords} label="Power" value={selectedPet.atk || 10} colorClass="text-orange-400" />
                                <StatBox icon={Wind} label="Speed" value={selectedPet.spd || 10} colorClass="text-cyan-400" />
                                <StatBox icon={Sparkles} label="Luck" value={`${((selectedPet.luck || 0) * 100).toFixed(0)}%`} colorClass="text-brand-accent" />
                            </div>

                            <div className="bg-white/[0.02] border border-white/5 p-5 rounded-[2rem] mb-10 text-left">
                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                                    <Activity size={12} className="text-brand-accent" />
                                    Active Ability
                                </p>
                                <p className="text-[12px] text-slate-300 leading-relaxed font-medium">
                                    {selectedPet.desc || `A high-performance ${selectedPet.name} companion specialized in providing consistent support and statistical advantages during field operations.`}
                                </p>
                            </div>

                            <div className="space-y-4">
                                {isOwned ? (
                                    <button 
                                        onClick={handleSetPet}
                                        disabled={isActive || setStage === 'setting'}
                                        className={cn(
                                            "w-full py-5 rounded-[2rem] font-black uppercase text-[11px] tracking-[0.3em] transition-all flex items-center justify-center gap-3",
                                            isActive 
                                                ? "bg-brand-accent/10 text-brand-accent border border-brand-accent/20"
                                                : "bg-white text-brand-midnight shadow-xl active:scale-95"
                                        )}
                                    >
                                        {setStage === 'setting' ? (
                                            <Loader2 size={16} className="animate-spin" />
                                        ) : isActive ? (
                                            <><Check size={16} /> Currently Synced</>
                                        ) : (
                                            'SYNC COMPANION'
                                        )}
                                    </button>
                                ) : isLocked ? (
                                    <div className="w-full py-5 rounded-[2rem] bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3">
                                        <Lock size={16} /> Requires Level {selectedPet.req_level}
                                    </div>
                                ) : (
                                    <div className="w-full">
                                        <AnimatePresence mode="wait">
                                            {purchaseStage === 'idle' ? (
                                                <button 
                                                    key="buy-btn"
                                                    onClick={() => {
                                                        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                                                        setPurchaseStage('confirm');
                                                    }}
                                                    className="w-full py-5 rounded-[2rem] bg-brand-accent text-brand-midnight font-black uppercase text-[11px] tracking-[0.3em] shadow-xl shadow-brand-accent/20 active:scale-95 transition-all flex items-center justify-center gap-3"
                                                >
                                                    BUY FOR {selectedPet.zenith_price} <Activity size={16} />
                                                </button>
                                            ) : (
                                                <motion.div 
                                                    key="confirm-box"
                                                    initial={{ opacity: 0, scale: 0.95 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    exit={{ opacity: 0, scale: 0.95 }}
                                                    className="p-1 glass-panel rounded-[2rem] border border-brand-accent/20 flex space-x-1"
                                                >
                                                    <button 
                                                        onClick={() => setPurchaseStage('idle')}
                                                        className="flex-1 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500"
                                                    >
                                                        Cancel
                                                    </button>
                                                    <button 
                                                        onClick={handleBuy}
                                                        disabled={purchaseStage === 'buying'}
                                                        className="flex-[2] py-4 bg-brand-accent text-brand-midnight rounded-[1.8rem] text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2"
                                                    >
                                                        {purchaseStage === 'buying' ? (
                                                            <Loader2 size={16} className="animate-spin" />
                                                        ) : 'Confirm Pay'}
                                                    </button>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};
