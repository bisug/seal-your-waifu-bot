import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Gamepad2,
    Zap,
    Timer,
    Trophy,
    Play,
    RotateCcw,
    Brain,
    Loader2,
    ChevronRight,
    Star,
    Sparkles,
    CircleDashed,
    Target,
    ShieldAlert,
    Scan,
    Activity,
    Lock
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { apiFetch, getErrorMessage } from '../api/client';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';
import { cn, haptics } from '../utils';

// --- Types ---

interface MinigameState {
    energy: number;
    max_energy: number;
    last_energy_recharge: string | null;
}

interface SessionData {
    start_time: number;
    cards?: {
        id: string;
        img_url: string;
        name: string;
    }[];
    prize?: {
        type: string;
        label: string;
        amount?: number;
    };
    prize_index?: number;
}

interface Reward {
    shards: number;
    xp: number;
    character?: {
        id: string;
        name: string;
        anime: string;
        rarity: string;
        img_url: string;
    } | null;
}

// --- Components ---

const EnergyDisplay = ({ energy, maxEnergy, lastRecharge }: { energy: number, maxEnergy: number, lastRecharge: string | null }) => {
    const [timeLeft, setTimeLeft] = useState<string | null>(null);

    useEffect(() => {
        if (energy >= maxEnergy || !lastRecharge) {
            setTimeLeft(null);
            return;
        }

        const interval = setInterval(() => {
            const last = new Date(lastRecharge).getTime();
            const now = new Date().getTime();
            const rechargeInterval = 20 * 60 * 1000; // 20 mins
            const next = last + rechargeInterval;
            const diff = next - now;

            if (diff <= 0) {
                setTimeLeft("00:00");
                return;
            }

            const mins = Math.floor(diff / 60000);
            const secs = Math.floor((diff % 60000) / 1000);
            setTimeLeft(`${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`);
        }, 1000);

        return () => clearInterval(interval);
    }, [energy, maxEnergy, lastRecharge]);

    return (
        <Card className="p-4 bg-zinc-900/50 border-white/[0.04] mb-6 overflow-hidden relative">
            <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-brand-accent/10 flex items-center justify-center border border-brand-accent/20">
                        <Zap size={20} className="text-brand-accent" fill="currentColor" />
                    </div>
                    <div>
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-0.5">Energy Reserve</h4>
                        <div className="flex items-end gap-1.5">
                            <span className="text-xl font-mono font-bold text-zinc-100">{energy}</span>
                            <span className="text-xs font-mono text-zinc-600 mb-1">/ {maxEnergy}</span>
                        </div>
                    </div>
                </div>
                {timeLeft && (
                    <div className="text-right">
                         <h4 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Next Unit</h4>
                         <div className="flex items-center gap-1.5 text-zinc-400 font-mono text-sm">
                            <Timer size={12} className="text-zinc-600" />
                            {timeLeft}
                         </div>
                    </div>
                )}
            </div>

            {/* Visual Energy Bar */}
            <div className="absolute bottom-0 left-0 h-0.5 bg-zinc-800 w-full">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(energy / maxEnergy) * 100}%` }}
                    className="h-full bg-brand-accent shadow-[0_0_10px_rgba(var(--brand-accent-rgb),0.5)]"
                />
            </div>
        </Card>
    );
};

// --- Cipher Match (Memory) ---

const MAX_MOVES = 24;

const CipherMatch = ({ session, onComplete, onCancel }: { session: SessionData, onComplete: (score: number) => void, onCancel: () => void }) => {
    const [cards, setCards] = useState<{ id: string, img_url: string, name: string, isFlipped: boolean, isMatched: boolean, key: number }[]>([]);
    const [flippedIndices, setFlippedIndices] = useState<number[]>([]);
    const [matches, setMatches] = useState(0);
    const [moves, setMoves] = useState(0);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        if (!session.cards) return;
        const doubled = [...session.cards, ...session.cards];
        const shuffled = doubled
            .sort(() => Math.random() - 0.5)
            .map((card, index) => ({ ...card, isFlipped: false, isMatched: false, key: index }));
        setCards(shuffled);
    }, [session.cards]);

    const handleCardClick = (index: number) => {
        if (failed || cards[index].isFlipped || cards[index].isMatched || flippedIndices.length === 2) return;

        haptics.light();
        const newCards = [...cards];
        newCards[index].isFlipped = true;
        setCards(newCards);

        const newFlipped = [...flippedIndices, index];
        setFlippedIndices(newFlipped);

        if (newFlipped.length === 2) {
            const nextMoves = moves + 1;
            setMoves(nextMoves);
            const [first, second] = newFlipped;

            if (cards[first].id === cards[second].id) {
                haptics.notification('success');
                setTimeout(() => {
                    setCards(prev => {
                        const updated = [...prev];
                        updated[first].isMatched = true;
                        updated[second].isMatched = true;
                        return updated;
                    });
                    setMatches(m => {
                        const next = m + 1;
                        if (next === session.cards!.length) {
                             onComplete(next);
                        }
                        return next;
                    });
                    setFlippedIndices([]);
                }, 400);
            } else {
                setTimeout(() => {
                    if (nextMoves >= MAX_MOVES) {
                        haptics.notification('error');
                        setFailed(true);
                    }
                    setCards(prev => {
                        const updated = [...prev];
                        updated[first].isFlipped = false;
                        updated[second].isFlipped = false;
                        return updated;
                    });
                    setFlippedIndices([]);
                }, 800);
            }
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-6">
                    <div className="relative">
                        <span className="block text-[7px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-1">Grid Sync</span>
                        <div className="flex items-center gap-2">
                            <Activity size={10} className="text-brand-accent animate-pulse" />
                            <span className="text-base font-mono font-bold text-zinc-100">{matches} <span className="text-zinc-600 text-xs">/ {session.cards?.length}</span></span>
                        </div>
                    </div>
                    <div className="w-px h-6 bg-white/5" />
                    <div className="relative">
                        <span className="block text-[7px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-1">Sync Capacity</span>
                        <div className="flex items-center gap-2">
                            <ShieldAlert size={10} className={cn(moves > MAX_MOVES * 0.7 ? "text-red-500" : "text-zinc-500")} />
                            <span className={cn(
                                "text-base font-mono font-bold",
                                moves > MAX_MOVES * 0.7 ? "text-red-400" : "text-zinc-100"
                            )}>
                                {MAX_MOVES - moves}
                                <span className="text-zinc-600 text-xs"> Left</span>
                            </span>
                        </div>
                    </div>
                </div>
                <Button variant="ghost" size="sm" onClick={onCancel} className="text-[9px] font-bold uppercase tracking-widest text-zinc-600 hover:text-red-400">
                    Abort
                </Button>
            </div>

            <div className="grid grid-cols-4 gap-2">
                {cards.map((card, idx) => (
                    <div key={card.key} className="aspect-[3/4] perspective-1000">
                        <motion.div
                            initial={false}
                            animate={{ rotateY: card.isFlipped || card.isMatched ? 180 : 0 }}
                            transition={{ type: "spring", stiffness: 260, damping: 20 }}
                            className="relative w-full h-full preserve-3d"
                            onClick={() => handleCardClick(idx)}
                        >
                            {/* Front (Hidden) */}
                            <div className="absolute inset-0 backface-hidden rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center cursor-pointer overflow-hidden group">
                                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.05)_0%,transparent_70%)] opacity-0 group-hover:opacity-100 transition-opacity" />
                                <Scan size={24} className="text-zinc-800 group-hover:text-brand-accent/40 transition-colors" />
                                <div className="absolute bottom-1 right-1">
                                    <div className="w-1 h-1 bg-zinc-800 rounded-full" />
                                </div>
                            </div>

                            {/* Back (Visible) */}
                            <div className="absolute inset-0 backface-hidden rounded-lg bg-zinc-100 border border-white overflow-hidden rotateY-180">
                                <img src={card.img_url} alt={card.name} referrerPolicy="no-referrer" className="w-full h-full object-cover" />
                                {card.isMatched && (
                                    <div className="absolute inset-0 bg-brand-accent/20 backdrop-blur-[1px] flex items-center justify-center">
                                        <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-lg">
                                            <Star size={14} className="text-brand-accent fill-brand-accent" />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </div>
                ))}
            </div>

            {failed && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center"
                >
                    <ShieldAlert size={48} className="text-red-500 mb-4" />
                    <h3 className="text-xl font-bold text-white uppercase tracking-tighter mb-2">Sync Failure</h3>
                    <p className="text-xs text-zinc-500 uppercase tracking-widest mb-6">Operational capacity exceeded</p>
                    <div className="flex gap-3 w-full">
                        <Button onClick={onCancel} variant="ghost" className="flex-1 text-zinc-400">Exit</Button>
                        <Button onClick={() => onComplete(matches)} className="flex-1 bg-red-500 hover:bg-red-600 text-white">Submit Progress</Button>
                    </div>
                </motion.div>
            )}
        </div>
    );
};

// --- Nexus Wheel ---

const WHEEL_PRIZES = [
    { label: '50 Shards', value: 50, color: 'zinc' },
    { label: '100 Shards', value: 100, color: 'zinc' },
    { label: '200 Shards', value: 200, color: 'brand' },
    { label: 'Character', value: 'char', color: 'epic' },
    { label: '150 Shards', value: 150, color: 'zinc' },
    { label: '500 Shards', value: 500, color: 'rare' },
    { label: '80 Shards', value: 80, color: 'zinc' },
    { label: 'XP Boost', value: 'xp', color: 'brand' },
];

const NexusWheel = ({ session, onComplete, _onCancel }: { session: SessionData, onComplete: (score: number) => void, _onCancel: () => void }) => {
    const [isSpinning, setIsSpinning] = useState(false);
    const [rotation, setRotation] = useState(0);

    const spin = () => {
        if (isSpinning || session.prize_index === undefined) return;
        setIsSpinning(true);
        haptics.heavy();

        const sectorSize = 360 / WHEEL_PRIZES.length;
        const targetSector = session.prize_index;
        // Calculate rotation to land target sector under pointer (at top, 0deg)
        // sectors are indexed 0 to 7. 0 is at 0-45deg.
        // We want the middle of the target sector to be at 0deg.
        const extraRounds = 8;
        const finalRotation = (extraRounds * 360) - (targetSector * sectorSize + sectorSize / 2);
        setRotation(finalRotation);

        // Haptic ticks during spin
        const tickInterval = setInterval(() => {
            haptics.light();
        }, 150);
        setTimeout(() => clearInterval(tickInterval), 3500);

        setTimeout(() => {
            setIsSpinning(false);
            haptics.notification('success');
            setTimeout(() => onComplete(0), 1000);
        }, 4500);
    };

    return (
        <div className="flex flex-col items-center py-4 space-y-12">
            <div className="w-full flex items-center justify-between px-6">
                <div className="space-y-1">
                    <span className="block text-[7px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Flux Capacitor</span>
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-pulse" />
                        <span className="text-xs font-mono font-bold text-zinc-300">STABLE</span>
                    </div>
                </div>
                <div className="text-right space-y-1">
                    <span className="block text-[7px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Sync Rate</span>
                    <span className="text-xs font-mono font-bold text-brand-accent">99.98%</span>
                </div>
            </div>

            <div className="relative w-72 h-72">
                {/* Tactical Ring */}
                <div className="absolute -inset-4 rounded-full border border-white/[0.02] flex items-center justify-center">
                     <div className="absolute inset-0 rounded-full border border-dashed border-white/[0.05] animate-[spin_60s_linear_infinite]" />
                </div>

                {/* Pointer */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30">
                    <div className="flex flex-col items-center">
                        <div className="w-0.5 h-4 bg-brand-accent shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                        <div className="w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[12px] border-t-brand-accent" />
                    </div>
                </div>

                {/* Outer Ring */}
                <div className="absolute inset-0 rounded-full border-[6px] border-zinc-900 shadow-[0_0_50px_rgba(0,0,0,0.8)] z-20 pointer-events-none" />

                <motion.div
                    animate={{ rotate: rotation }}
                    transition={{ duration: 4.5, ease: [0.15, 0, 0.15, 1] }}
                    className="w-full h-full rounded-full bg-zinc-950 overflow-hidden border border-white/10 relative z-10"
                >
                    {WHEEL_PRIZES.map((prize, i) => (
                        <div
                            key={i}
                            className="absolute top-0 left-1/2 w-px h-1/2 bg-white/[0.03] origin-bottom"
                            style={{ transform: `rotate(${i * (360 / WHEEL_PRIZES.length)}deg)` }}
                        >
                            <div
                                className="absolute top-10 left-0 -translate-x-1/2 flex flex-col items-center gap-2"
                                style={{ transform: `rotate(${180 / WHEEL_PRIZES.length}deg)` }}
                            >
                                <div className={cn(
                                    "w-1 h-1 rounded-full",
                                    prize.color === 'brand' ? "bg-brand-accent" :
                                    prize.color === 'epic' ? "bg-purple-500" :
                                    prize.color === 'rare' ? "bg-cyan-500" : "bg-zinc-800"
                                )} />
                                <span className={cn(
                                    "text-[8px] font-bold uppercase tracking-[0.15em] [writing-mode:vertical-lr] rotate-180",
                                    prize.color === 'brand' ? "text-brand-accent" :
                                    prize.color === 'epic' ? "text-purple-400" :
                                    prize.color === 'rare' ? "text-cyan-400" : "text-zinc-500"
                                )}>
                                    {prize.label}
                                </span>
                            </div>
                        </div>
                    ))}
                </motion.div>

                {/* Center Hub */}
                <div className="absolute inset-0 m-auto w-16 h-16 rounded-full bg-zinc-950 border border-white/10 flex items-center justify-center z-30 shadow-2xl">
                    <div className="absolute inset-0 rounded-full border border-white/5 animate-pulse" />
                    <CircleDashed size={24} className={cn("text-zinc-700 transition-all duration-1000", isSpinning ? "animate-spin text-brand-accent" : "")} />
                </div>
            </div>

            <div className="flex flex-col items-center gap-4 w-full px-8 pt-4">
                <div className="w-full flex justify-between text-[8px] font-bold text-zinc-600 uppercase tracking-widest mb-2">
                    <span>Power Lvl</span>
                    <span className="text-zinc-400">1.21 GW</span>
                </div>
                <Button
                    onClick={spin}
                    disabled={isSpinning}
                    className="w-full h-14 bg-zinc-100 text-zinc-950 font-bold uppercase tracking-[0.2em] text-[10px] rounded-xl relative overflow-hidden group shadow-[0_0_20px_rgba(255,255,255,0.1)]"
                >
                    <span className="relative z-10">{isSpinning ? "Synchronizing..." : "Initiate Sequence"}</span>
                    {!isSpinning && (
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: '100%' }}
                            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                            className="absolute inset-0 bg-gradient-to-r from-transparent via-black/[0.05] to-transparent"
                        />
                    )}
                </Button>
                <p className="text-[7px] text-zinc-600 font-bold uppercase tracking-widest">Authorized use only • Personnel class B+</p>
            </div>
        </div>
    );
};

// --- Reward Modal ---

const RewardModal = ({ rewards, onClose }: { rewards: Reward, onClose: () => void }) => {
    const [revealed, setRevealed] = useState(false);

    useEffect(() => {
        haptics.notification('success');
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-2xl flex items-center justify-center p-6"
        >
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-brand-accent/10 blur-[120px] rounded-full" />
            </div>

            <AnimatePresence mode="wait">
                {!revealed && rewards.character ? (
                    <motion.div
                        key="box"
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 1.2, opacity: 0, filter: 'brightness(2) blur(10px)' }}
                        className="relative flex flex-col items-center gap-8"
                    >
                        <motion.div
                            animate={{
                                y: [0, -10, 0],
                                rotate: [0, 1, -1, 0]
                            }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="w-48 h-48 relative"
                        >
                            <div className="absolute inset-0 bg-brand-accent/20 rounded-3xl blur-2xl animate-pulse" />
                            <div className="absolute inset-0 bg-zinc-900 border border-white/10 rounded-3xl flex items-center justify-center overflow-hidden shadow-2xl">
                                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.1)_0%,transparent_70%)]" />
                                <Lock size={64} className="text-brand-accent" />
                                <div className="absolute bottom-0 left-0 w-full h-1 bg-brand-accent shadow-[0_0_20px_rgba(59,130,246,0.5)]" />
                            </div>
                        </motion.div>

                        <div className="text-center space-y-2">
                             <h3 className="text-xl font-bold text-white uppercase tracking-[0.3em]">Encrypted Asset</h3>
                             <p className="text-[9px] text-zinc-500 uppercase tracking-widest">Awaiting manual decryption</p>
                        </div>

                        <Button
                            onClick={() => {
                                haptics.heavy();
                                setRevealed(true);
                            }}
                            className="w-64 bg-white text-black font-bold uppercase tracking-widest text-[10px] py-4 rounded-xl"
                        >
                            Decryption Sequence
                        </Button>
                    </motion.div>
                ) : (
                    <motion.div
                        key="content"
                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        className="w-full max-w-sm bg-zinc-950/50 border border-white/10 rounded-3xl overflow-hidden shadow-2xl relative"
                    >
                        <div className="p-8 text-center space-y-8">
                            <div className="space-y-2">
                                <div className="flex justify-center mb-4">
                                     <div className="w-12 h-12 rounded-xl bg-brand-accent/10 flex items-center justify-center border border-brand-accent/20">
                                        <Trophy size={24} className="text-brand-accent" />
                                     </div>
                                </div>
                                <h3 className="text-xl font-bold text-zinc-100 uppercase tracking-wider">Mission Success</h3>
                                <p className="text-[10px] text-zinc-500 uppercase tracking-[0.2em]">Operational rewards allocated</p>
                            </div>

                            {rewards.character && (
                                <motion.div
                                    initial={{ y: 20, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                    transition={{ delay: 0.2 }}
                                    className="relative group"
                                >
                                    <div className="absolute -inset-4 bg-purple-500/10 blur-2xl rounded-full opacity-50" />
                                    <div className="relative aspect-[3/4] rounded-2xl overflow-hidden border-2 border-purple-500/30 shadow-2xl">
                                        <img src={rewards.character.img_url} alt={rewards.character.name} referrerPolicy="no-referrer" className="w-full h-full object-cover" />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
                                        <div className="absolute bottom-0 left-0 w-full p-4 text-left">
                                            <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30 mb-2 uppercase tracking-widest text-[8px]">
                                                {rewards.character.rarity}
                                            </Badge>
                                            <div className="text-lg font-bold text-white leading-tight">{rewards.character.name}</div>
                                            <div className="text-[10px] text-zinc-400 font-medium">{rewards.character.anime}</div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 rounded-2xl bg-zinc-900/50 border border-white/[0.05] flex flex-col items-center gap-1">
                                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Shards</span>
                                    <span className="text-2xl font-mono font-bold text-zinc-100">+{rewards.shards}</span>
                                </div>
                                <div className="p-4 rounded-2xl bg-zinc-900/50 border border-white/[0.05] flex flex-col items-center gap-1">
                                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Exp</span>
                                    <span className="text-2xl font-mono font-bold text-zinc-100">+{rewards.xp}</span>
                                </div>
                            </div>

                            <Button
                                onClick={onClose}
                                className="w-full bg-zinc-100 text-zinc-950 font-bold uppercase tracking-widest text-[10px] py-4 rounded-xl"
                            >
                                Confirm & Close
                            </Button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// --- Main Page ---

export const Minigames = () => {
    const { refreshUser } = useUser();
    const { addToast } = useToast();
    const [state, setState] = useState<MinigameState | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeGame, setActiveGame] = useState<'cipher_match' | 'nexus_wheel' | null>(null);
    const [session, setSession] = useState<SessionData | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [rewards, setRewards] = useState<Reward | null>(null);

    const fetchState = useCallback(async () => {
        try {
            const data = await apiFetch('/minigames/state');
            setState(data);
        } catch (err) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setIsLoading(false);
        }
    }, [addToast]);

    useEffect(() => {
        fetchState();
    }, [fetchState]);

    const handleStartGame = async (game: 'cipher_match' | 'nexus_wheel') => {
        if (!state || state.energy <= 0) {
            addToast('Insufficient energy reserve', 'error');
            return;
        }

        try {
            setIsLoading(true);
            const data = await apiFetch(`/minigames/start/${game}`, { method: 'POST' });
            setSession(data.session);
            setActiveGame(game);
            // Optimization: update local energy state immediately
            setState(prev => prev ? { ...prev, energy: prev.energy - 1 } : null);
        } catch (err) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = async (score: number) => {
        if (!activeGame) return;
        setSubmitting(true);
        try {
            const data = await apiFetch('/minigames/submit', {
                method: 'POST',
                body: JSON.stringify({ game_type: activeGame, score })
            });
            setRewards(data.rewards);
            setActiveGame(null);
            refreshUser();
            fetchState();
        } catch (err) {
            addToast(getErrorMessage(err), 'error');
            setActiveGame(null);
            fetchState();
        } finally {
            setSubmitting(false);
        }
    };

    if (isLoading && !state) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 size={24} className="text-zinc-800 animate-spin" />
            </div>
        );
    }

    return (
        <div className="adaptive-px pb-20 pt-4">
            <header className="mb-8">
                <h2 className="text-2xl font-bold text-zinc-100 uppercase tracking-tight mb-1">Nexus Games</h2>
                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em]">Operational training & testing</p>
            </header>

            {state && (
                <EnergyDisplay
                    energy={state.energy}
                    maxEnergy={state.max_energy}
                    lastRecharge={state.last_energy_recharge}
                />
            )}

            <AnimatePresence mode="wait">
                {!activeGame ? (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-4"
                    >
                        <Card
                            onClick={() => handleStartGame('cipher_match')}
                            className={cn(
                                "p-5 border-white/[0.04] bg-zinc-900/40 cursor-pointer group transition-all relative overflow-hidden",
                                state?.energy === 0 && "opacity-50 grayscale pointer-events-none"
                            )}
                        >
                            <div className="flex items-center justify-between relative z-10">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-zinc-950 flex items-center justify-center border border-white/5 shadow-inner">
                                        <Brain size={20} className="text-zinc-500 group-hover:text-brand-accent transition-colors" />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-bold text-zinc-200 uppercase tracking-wider mb-0.5">Cipher Match</h3>
                                        <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-widest">Memory sequence training</p>
                                    </div>
                                </div>
                                <ChevronRight size={18} className="text-zinc-700 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </Card>

                        <Card
                            onClick={() => handleStartGame('nexus_wheel')}
                            className={cn(
                                "p-5 border-white/[0.04] bg-zinc-900/40 cursor-pointer group transition-all relative overflow-hidden",
                                state?.energy === 0 && "opacity-50 grayscale pointer-events-none"
                            )}
                        >
                            <div className="flex items-center justify-between relative z-10">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-zinc-950 flex items-center justify-center border border-white/5 shadow-inner">
                                        <Target size={20} className="text-zinc-500 group-hover:text-purple-400 transition-colors" />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-bold text-zinc-200 uppercase tracking-wider mb-0.5">Nexus Wheel</h3>
                                        <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-widest">Random resource allocation</p>
                                    </div>
                                </div>
                                <ChevronRight size={18} className="text-zinc-700 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </Card>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        className="min-h-[400px] flex flex-col justify-center"
                    >
                        {activeGame === 'cipher_match' && session && (
                            <CipherMatch session={session} onComplete={handleSubmit} onCancel={() => setActiveGame(null)} />
                        )}
                        {activeGame === 'nexus_wheel' && session && (
                            <NexusWheel session={session} onComplete={() => handleSubmit(0)} _onCancel={() => setActiveGame(null)} />
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {submitting && (
                <div className="fixed inset-0 z-[250] bg-black/60 backdrop-blur-sm flex items-center justify-center">
                    <div className="flex flex-col items-center gap-4">
                        <Loader2 size={32} className="text-brand-accent animate-spin" />
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.3em]">Processing Rewards</span>
                    </div>
                </div>
            )}

            {rewards && (
                <RewardModal rewards={rewards} onClose={() => setRewards(null)} />
            )}
        </div>
    );
};
