import { useState, useEffect, type ElementType } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Heart, Gem, X, Swords, Wind, Sparkles, Check, Lock, PawPrint } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { apiFetch, getErrorMessage } from '../../api/client';
import { cn } from '../../utils';
import { useUser, type Pet, type User } from '../../context/UserContext';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

interface StatBoxProps {
    icon: ElementType;
    label: string;
    value: string | number;
    colorClass: string;
}

const StatBox = ({ icon: Icon, label, value, colorClass }: StatBoxProps) => (
    <Card className="p-4 bg-white/[0.02] flex items-center space-x-3">
        <div className={cn("p-2 rounded-xl bg-black/20", colorClass)}>
            <Icon size={16} />
        </div>
        <div>
            <p className="text-[8px] font-black text-neutral-500 uppercase tracking-widest">{label}</p>
            <p className="text-[12px] font-black text-white uppercase">{value}</p>
        </div>
    </Card>
);

const getPetImageSrc = (pet: Pet | null) => {
    const src = String(pet?.img || pet?.img_url || pet?.image || pet?.photo_url || '').trim();
    return /^https?:\/\//i.test(src) || src.startsWith('/') ? src : '';
};

interface PetActionModalProps {
    selectedPet: Pet | null;
    setSelectedPet: (pet: Pet | null) => void;
    user: User | null;
}

export const PetActionModal = ({ selectedPet, setSelectedPet, user }: PetActionModalProps) => {
    const { addToast } = useToast();
    const { triggerRefresh, liteMode } = useUser();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [syncStage, setSyncStage] = useState('idle');
    const [imageFailed, setImageFailed] = useState(false);
    const petImage = selectedPet ? getPetImageSrc(selectedPet) : '';

    useEffect(() => {
        if (!selectedPet) {
            setPurchaseStage('idle');
            setSyncStage('idle');
        }
    }, [selectedPet]);

    useEffect(() => {
        setImageFailed(false);
    }, [petImage, selectedPet]);

    if (!selectedPet) return null;

    const ownedPets = user?.pets || [];
    const selectedRef = String(selectedPet.petid || selectedPet.id || selectedPet.name || '');
    const isOwned = ownedPets.some((p: Pet) => [p.petid, p.id, p.name].filter(Boolean).includes(selectedRef) || p.name === selectedPet.name);
    const activeRef = user?.current_pet?.petid || user?.current_pet?.id || user?.current_pet?.name;
    const isActive = activeRef === selectedRef;
    const isLocked = (user?.stats?.level || 0) < (selectedPet.req_level || 0);
    const zenithBalance = user?.stats?.zenith ?? user?.zenith ?? 0;
    const canAfford = zenithBalance >= (selectedPet.zenith_price || 0);

    const handleBuy = async () => {
        setPurchaseStage('buying');
        try {
            await apiFetch(`/shop/buy/pet/${encodeURIComponent(selectedRef)}`, { method: 'POST' });
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
        <div className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center p-0 sm:p-4 select-none">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedPet(null)}
                className={cn(
                    "absolute inset-0 bg-black/90",
                    !liteMode && "backdrop-blur-xl"
                )}
            />

            <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={liteMode 
                    ? { duration: 0.15 }
                    : { type: "spring", damping: 30, stiffness: 300 }
                }
                className="relative w-full max-w-md bg-brand-midnight border-t sm:border border-white/5 rounded-t-[2.5rem] sm:rounded-[2.5rem] overflow-hidden flex flex-col max-h-[95vh] shadow-[0_0_50px_rgba(0,0,0,0.8)]"
            >
                <div className="p-8 overflow-y-auto no-scrollbar space-y-8">
                    <div className="flex justify-between items-start">
                        <div className="relative">
                            <div className="absolute -inset-1 bg-brand-accent/30 rounded-3xl blur-md opacity-50" />
                            <div className="w-28 h-28 rounded-3xl overflow-hidden border-2 border-brand-accent/20 bg-black/40 relative z-10 shadow-2xl">
                                {petImage && !imageFailed ? (
                                    <img
                                        key={petImage}
                                        src={petImage}
                                        alt={selectedPet.name}
                                        className="w-full h-full object-cover transition-transform duration-700 hover:scale-110"
                                        referrerPolicy="no-referrer"
                                        onError={() => setImageFailed(true)}
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-neutral-800 bg-brand-midnight">
                                        <PawPrint size={32} />
                                    </div>
                                )}
                            </div>
                        </div>
                        <Button
                            variant="secondary"
                            onClick={() => setSelectedPet(null)}
                            className="w-10 h-10 p-0 rounded-full bg-white/5 border-white/10"
                        >
                            <X size={20} />
                        </Button>
                    </div>

                    <div className="space-y-1">
                        <div className="flex items-center gap-3 min-w-0">
                            <h2 className="text-3xl font-black text-white tracking-tighter uppercase truncate">{selectedPet.name}</h2>
                            <Badge variant="primary" className="py-1 px-2 rounded-lg font-black uppercase tracking-widest text-[9px] shrink-0">
                                {selectedPet.rarity || 'ELITE'}
                            </Badge>
                        </div>
                        <p className="text-[10px] font-black text-neutral-500 uppercase tracking-[0.2em]">Biological Companion Asset</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <StatBox icon={Heart} label="Endurance" value={selectedPet.hp ?? 0} colorClass="text-red-500" />
                        <StatBox icon={Swords} label="Offense" value={selectedPet.atk ?? 0} colorClass="text-brand-accent" />
                        <StatBox icon={Wind} label="Velocity" value={selectedPet.spd ?? 0} colorClass="text-blue-400" />
                        <StatBox icon={Sparkles} label="Probability" value={`${Math.round(Number(selectedPet.luck || 0) * 100)}%`} colorClass="text-amber-400" />
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center space-x-2 text-brand-accent">
                            <Sparkles size={14} className="text-brand-accent" />
                            <span className="text-[10px] font-black uppercase tracking-widest">Innate Talent</span>
                        </div>
                        <p className="text-xs font-bold text-neutral-400 leading-relaxed uppercase tracking-wide bg-white/[0.02] p-4 rounded-2xl border border-white/5">
                            {selectedPet.desc || `${selectedPet.name} provides specialized tactical support while deployed.`}
                        </p>
                    </div>
                </div>

                <div className="p-8 pt-2 mt-auto">
                    {isActive ? (
                         <Badge variant="primary" icon={Check} className="w-full py-5 rounded-2xl justify-center text-xs font-black tracking-widest uppercase border-brand-accent/30 bg-brand-accent/5">
                             Currently Deployed
                         </Badge>
                    ) : isOwned ? (
                        <Button
                            onClick={handleSync}
                            isLoading={syncStage === 'syncing'}
                            className="w-full py-6 rounded-2xl uppercase tracking-[0.2em] text-[11px] font-black shadow-[0_10px_30px_rgba(59,130,246,0.3)]"
                        >
                            Deploy Companion
                        </Button>
                    ) : isLocked ? (
                        <Badge variant="danger" icon={Lock} className="w-full py-5 rounded-2xl justify-center text-xs font-black tracking-widest uppercase bg-red-500/5 border-red-500/20">
                            Lvl {selectedPet.req_level} Required
                        </Badge>
                    ) : (
                        <div className="w-full">
                            {purchaseStage === 'idle' ? (
                                <Button
                                    onClick={() => {
                                        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                                        setPurchaseStage('confirm');
                                    }}
                                    disabled={!canAfford}
                                    className="w-full py-6 rounded-2xl uppercase tracking-[0.2em] text-[11px] font-black shadow-[0_10px_30px_rgba(59,130,246,0.3)]"
                                >
                                    {canAfford ? `Acquire for ${selectedPet.zenith_price} Zenith` : `Need ${Math.max(0, (selectedPet.zenith_price || 0) - zenithBalance)} more Zenith`}
                                </Button>
                            ) : (
                                <div className="flex gap-3">
                                    <Button
                                        variant="secondary"
                                        onClick={() => setPurchaseStage('idle')}
                                        className="flex-1 rounded-2xl uppercase tracking-widest text-[10px] font-black"
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        onClick={handleBuy}
                                        isLoading={purchaseStage === 'buying'}
                                        className="flex-[2] rounded-2xl uppercase tracking-widest text-[10px] font-black"
                                    >
                                        Confirm Acquisition
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};
