import { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Heart,
  Loader2,
  PawPrint,
  Sparkles,
  Swords,
  Wind,
  X,
  Target,
  ShieldCheck,
  Zap,
  TrendingUp,
  History,
  Info
} from 'lucide-react';
import { apiFetch, getErrorMessage } from '../../api/client';
import { useToast } from '../ui/Toast';
import { useUser, type Pet, type User } from '../../context/UserContext';
import { formatNumber, cn } from '../../utils';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { ProgressBar } from '../ui/ProgressBar';
import { motion, AnimatePresence } from 'framer-motion';

interface PetActionModalProps {
    selectedPet: Pet | null;
    setSelectedPet: (pet: Pet | null) => void;
    user: User | null;
}

export const PetActionModal = ({ selectedPet, setSelectedPet, user }: PetActionModalProps) => {
    const { addToast } = useToast();
    const { triggerRefresh } = useUser();
    const [actionStage, setActionStage] = useState<'idle' | 'loading'>('idle');

    const isOwned = (user?.pets || []).some((p: Pet) => String(p.petid || p.id) === String(selectedPet?.petid || selectedPet?.id));
    const isActive = user?.current_pet && String(user.current_pet.petid || user.current_pet.id) === String(selectedPet?.petid || selectedPet?.id);

    useEffect(() => {
        if (selectedPet) {
            document.body.style.overflow = 'hidden';
            return () => { document.body.style.overflow = 'unset'; };
        }
    }, [selectedPet]);

    if (!selectedPet) return null;

    const handleSetActive = async () => {
        const petRef = selectedPet.petid || selectedPet.id || selectedPet.name;
        if (!petRef) return;

        setActionStage('loading');
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
        try {
            await apiFetch(`/pets/set_active/${encodeURIComponent(petRef)}`, { method: 'POST' });
            await triggerRefresh();
            addToast(`Synchronization complete: ${selectedPet.name} is now active.`, 'success');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            setSelectedPet(null);
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
        } finally {
            setActionStage('idle');
        }
    };

    const imgUrl = selectedPet.img || selectedPet.img_url || selectedPet.image || selectedPet.photo_url || '';

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[1000] flex items-end sm:items-center justify-center p-0 sm:p-6">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-black/80 backdrop-blur-md"
                    onClick={() => setSelectedPet(null)}
                />

                <motion.div
                    initial={{ y: '100%' }}
                    animate={{ y: 0 }}
                    exit={{ y: '100%' }}
                    transition={{ type: 'spring', damping: 30, stiffness: 300, mass: 0.8 }}
                    className="relative w-full max-w-[440px] bg-brand-midnight rounded-t-[32px] sm:rounded-[32px] flex flex-col overflow-hidden shadow-2xl border-t sm:border border-white/[0.08]"
                >
                    {/* Header Controls */}
                    <div className="absolute right-6 top-6 z-20">
                        <Button
                            variant="ghost"
                            onClick={() => setSelectedPet(null)}
                            className="w-10 h-10 p-0 rounded-full bg-black/40 backdrop-blur-xl border border-white/5 hover:bg-white/10"
                            aria-label="Close"
                        >
                            <X size={20} strokeWidth={3} />
                        </Button>
                    </div>

                    {/* Media Section */}
                    <div className="relative aspect-[16/9] flex-shrink-0 bg-brand-deep/30 flex items-center justify-center overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-black/40" />
                        <div className="absolute inset-0 bg-scanline opacity-[0.03] pointer-events-none" />
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.1),transparent_70%)]" />

                        {imgUrl ? (
                            <motion.img
                                initial={{ scale: 1.1, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ duration: 0.8 }}
                                src={imgUrl}
                                className="w-full h-full object-cover"
                                alt={selectedPet.name}
                            />
                        ) : (
                            <div className="flex flex-col items-center gap-3 opacity-20">
                                <PawPrint size={64} />
                                <span className="text-[10px] font-black uppercase tracking-[0.5em]">NO_VISUAL_DATA</span>
                            </div>
                        )}

                        <div className="absolute bottom-6 left-6 z-20 flex gap-2">
                            <Badge variant="tactical" size="sm" className="px-3 py-1 border-none shadow-xl backdrop-blur-md font-black bg-brand-accent/80">
                                CLASS_{selectedPet.rarity?.toUpperCase() || 'STANDARD'}
                            </Badge>
                            {isActive && (
                                <Badge variant="success" size="sm" className="px-3 py-1 border-none shadow-xl backdrop-blur-md font-black bg-emerald-500/80">
                                    ACTIVE_SYNC
                                </Badge>
                            )}
                        </div>
                    </div>

                    {/* Content Section */}
                    <div className="flex-1 bg-brand-midnight p-6 sm:p-8 space-y-8">
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 opacity-50">
                                <Target size={12} className="text-brand-accent" />
                                <span className="text-[10px] font-black uppercase tracking-[0.4em] text-white font-mono leading-none">UNIT_ID: {String(selectedPet.petid || selectedPet.id || 'TEMP').toUpperCase()}</span>
                            </div>
                            <h2 className="text-3xl font-black text-white leading-none uppercase tracking-tighter drop-shadow-md">{selectedPet.name}</h2>
                            <div className="flex items-center gap-2.5">
                               <Sparkles size={14} className="text-brand-accent animate-pulse" />
                               <p className="text-[12px] font-black text-brand-accent uppercase tracking-widest leading-none">{selectedPet.ability || 'SYSTEM_SUPPORT_PERK'}</p>
                            </div>
                        </div>

                        {selectedPet.desc && (
                            <div className="bg-white/[0.02] border border-white/[0.04] p-4 rounded-2xl relative">
                                <div className="absolute top-0 right-0 p-3 opacity-5">
                                   <Info size={40} />
                                </div>
                                <p className="text-[11px] font-bold text-neutral-400 uppercase tracking-widest leading-relaxed relative z-10">
                                    {selectedPet.desc}
                                </p>
                            </div>
                        )}

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {[
                                { icon: Heart, label: 'VITALITY', value: selectedPet.hp ?? 0, variant: 'success' },
                                { icon: Swords, label: 'STRIKE', value: selectedPet.atk ?? 0, variant: 'danger' },
                                { icon: Wind, label: 'VELOCITY', value: selectedPet.spd ?? 0, variant: 'primary' },
                                { icon: Sparkles, label: 'LUCK_RT', value: `${Math.round(Number(selectedPet.luck || 0) * 100)}%`, variant: 'primary' },
                            ].map((stat, i) => (
                                <Card key={i} variant="tactical" className="p-3 bg-white/[0.01] border-white/[0.03] flex flex-col justify-between h-20">
                                    <stat.icon size={12} className={cn(
                                        stat.variant === 'success' ? "text-success" : stat.variant === 'danger' ? "text-danger" : "text-brand-accent"
                                    )} />
                                    <div className="mt-2">
                                        <span className="block text-[8px] font-black text-neutral-700 uppercase tracking-widest mb-1">{stat.label}</span>
                                        <span className="block text-xs font-black text-white tabular-nums font-mono leading-none">
                                            {stat.value}
                                        </span>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        {isOwned && (
                            <div className="space-y-4 pt-2">
                                <div className="flex items-center justify-between px-1">
                                    <div className="flex items-center gap-2">
                                        <TrendingUp size={12} className="text-neutral-700" />
                                        <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.3em]">UNIT_PROGRESS</span>
                                    </div>
                                    <Badge variant="tactical" size="xs" className="font-mono opacity-60">LVL {selectedPet.level || 1}</Badge>
                                </div>
                                <ProgressBar current={selectedPet.xp || 0} total={selectedPet.xp_needed || 1000} variant="default" compact />
                            </div>
                        )}

                        <div className="pt-6 border-t border-white/[0.06] flex flex-col gap-4">
                            {isOwned ? (
                                <Button
                                    onClick={handleSetActive}
                                    disabled={isActive || actionStage === 'loading'}
                                    variant={isActive ? "secondary" : "tactical"}
                                    className="w-full h-16 rounded-2xl uppercase tracking-[0.3em] text-[12px] font-black shadow-2xl active:scale-95 transition-all"
                                >
                                    {actionStage === 'loading' ? (
                                        <Loader2 size={20} className="animate-spin mr-3" />
                                    ) : isActive ? (
                                        <ShieldCheck size={20} strokeWidth={2.5} className="mr-3 text-success" />
                                    ) : (
                                        <History size={20} strokeWidth={2.5} className="mr-3" />
                                    )}
                                    {isActive ? 'SYNC_ACTIVE' : 'AUTHORIZE_SYNC'}
                                </Button>
                            ) : (
                                <div className="bg-brand-accent/10 border border-brand-accent/20 p-5 rounded-2xl flex items-center justify-between">
                                   <div className="flex items-center gap-4">
                                      <div className="w-10 h-10 rounded-xl bg-brand-accent/20 flex items-center justify-center text-brand-accent shadow-inner">
                                         <Zap size={20} />
                                      </div>
                                      <div className="flex flex-col">
                                         <span className="text-[9px] font-black text-brand-accent uppercase tracking-widest mb-1">AVAILABILITY</span>
                                         <span className="text-sm font-black text-white uppercase tracking-tight">VISIT BREEDER TERMINAL</span>
                                      </div>
                                   </div>
                                   <Badge variant="tactical" size="sm" className="bg-black/40 border-white/10 uppercase font-black px-3 py-1.5">LOCKED</Badge>
                                </div>
                            )}

                            <div className="flex items-center justify-center gap-3 opacity-20 py-2">
                               <Sparkles size={12} className="text-brand-accent" />
                               <span className="text-[8px] font-black uppercase tracking-[0.5em] text-white">End of Registry</span>
                            </div>
                        </div>
                    </div>

                    {/* Safe Area Padding */}
                    <div className="h-[calc(var(--sab,24px)+4px)] sm:hidden" />
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
