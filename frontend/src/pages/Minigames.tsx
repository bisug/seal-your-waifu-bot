import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
    Target
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { apiFetch, getErrorMessage } from '../api/client';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';
import { cn } from '../utils';

// --- Types ---

interface MinigameState {
    energy: number;
    max_energy: number;
    last_energy_recharge: string | null;
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

const CIPHER_SYMBOLS = ['✦', '✧', '◈', '◇', '⬪', '⬫', '⧫', '◊'];

const CipherMatch = ({ onComplete, onCancel }: { onComplete: (score: number) => void, onCancel: () => void }) => {
    const [cards, setCards] = useState<{ id: number, symbol: string, isFlipped: boolean, isMatched: boolean }[]>([]);
    const [flippedIndices, setFlippedIndices] = useState<number[]>([]);
    const [matches, setMatches] = useState(0);
    const [moves, setMoves] = useState(0);
    const [startTime] = useState(Date.now());

    useEffect(() => {
        const symbols = [...CIPHER_SYMBOLS, ...CIPHER_SYMBOLS];
        const shuffled = symbols
            .sort(() => Math.random() - 0.5)
            .map((symbol, index) => ({ id: index, symbol, isFlipped: false, isMatched: false }));
        setCards(shuffled);
    }, []);

    const handleCardClick = (index: number) => {
        if (cards[index].isFlipped || cards[index].isMatched || flippedIndices.length === 2) return;

        const newCards = [...cards];
        newCards[index].isFlipped = true;
        setCards(newCards);

        const newFlipped = [...flippedIndices, index];
        setFlippedIndices(newFlipped);

        if (newFlipped.length === 2) {
            setMoves(m => m + 1);
            const [first, second] = newFlipped;
            if (cards[first].symbol === cards[second].symbol) {
                setTimeout(() => {
                    setCards(prev => {
                        const updated = [...prev];
                        updated[first].isMatched = true;
                        updated[second].isMatched = true;
                        return updated;
                    });
                    setMatches(m => {
                        const next = m + 1;
                        if (next === CIPHER_SYMBOLS.length) {
                             onComplete(next);
                        }
                        return next;
                    });
                    setFlippedIndices([]);
                }, 400);
            } else {
                setTimeout(() => {
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
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="text-center">
                        <span className="block text-[8px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Matches</span>
                        <span className="text-lg font-mono font-bold text-zinc-200">{matches} / {CIPHER_SYMBOLS.length}</span>
                    </div>
                    <div className="h-8 w-px bg-white/5" />
                    <div className="text-center">
                        <span className="block text-[8px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Moves</span>
                        <span className="text-lg font-mono font-bold text-zinc-200">{moves}</span>
                    </div>
                </div>
                <Button variant="ghost" size="sm" onClick={onCancel} className="text-zinc-500 hover:text-zinc-200">Abandon</Button>
            </div>

            <div className="grid grid-cols-4 gap-2.5">
                {cards.map((card, idx) => (
                    <motion.div
                        key={card.id}
                        whileHover={{ scale: card.isMatched || card.isFlipped ? 1 : 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleCardClick(idx)}
                        className={cn(
                            "aspect-square rounded-lg flex items-center justify-center text-xl cursor-pointer transition-all duration-300 border",
                            card.isFlipped || card.isMatched
                                ? "bg-zinc-100 text-zinc-950 border-white"
                                : "bg-zinc-900 border-white/10 text-transparent"
                        )}
                    >
                        {(card.isFlipped || card.isMatched) ? card.symbol : '✦'}
                    </motion.div>
                ))}
            </div>
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

const NexusWheel = ({ onComplete, onCancel }: { onComplete: (score: number) => void, onCancel: () => void }) => {
    const [isSpinning, setIsSpinning] = useState(false);
    const [rotation, setRotation] = useState(0);

    const spin = () => {
        if (isSpinning) return;
        setIsSpinning(true);
        const extraRounds = 5 + Math.random() * 5;
        const newRotation = rotation + (extraRounds * 360) + Math.random() * 360;
        setRotation(newRotation);

        setTimeout(() => {
            setIsSpinning(false);
            onComplete(0); // Score doesn't matter for wheel, backend handles reward
        }, 4000);
    };

    return (
        <div className="flex flex-col items-center py-8 space-y-10">
            <div className="relative w-64 h-64">
                {/* Pointer */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
                    <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-brand-accent filter drop-shadow-xl" />
                </div>

                {/* Outer Ring */}
                <div className="absolute inset-0 rounded-full border-[8px] border-zinc-900 shadow-[0_0_40px_rgba(0,0,0,0.5)] z-10" />

                <motion.div
                    animate={{ rotate: rotation }}
                    transition={{ duration: 4, ease: [0.16, 1, 0.3, 1] }}
                    className="w-full h-full rounded-full bg-zinc-950 overflow-hidden border border-white/5 relative"
                >
                    {WHEEL_PRIZES.map((prize, i) => (
                        <div
                            key={i}
                            className="absolute top-0 left-1/2 w-px h-1/2 bg-white/5 origin-bottom"
                            style={{ transform: `rotate(${i * (360 / WHEEL_PRIZES.length)}deg)` }}
                        >
                            <div
                                className="absolute top-8 left-0 -translate-x-1/2 flex flex-col items-center gap-1"
                                style={{ transform: `rotate(${180 / WHEEL_PRIZES.length}deg)` }}
                            >
                                <span className={cn(
                                    "text-[7px] font-bold uppercase tracking-widest whitespace-nowrap",
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

                {/* Center Cap */}
                <div className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-zinc-950 border border-white/10 flex items-center justify-center z-20 shadow-xl">
                    <CircleDashed size={20} className={cn("text-zinc-700", isSpinning && "animate-spin")} />
                </div>
            </div>

            <div className="flex flex-col items-center gap-4 w-full px-6">
                <Button
                    onClick={spin}
                    disabled={isSpinning}
                    className="w-full h-12 bg-zinc-100 text-zinc-950 font-bold uppercase tracking-widest text-xs"
                >
                    {isSpinning ? "Spinning..." : "Engage Protocol"}
                </Button>
                <Button variant="ghost" size="sm" onClick={onCancel} disabled={isSpinning} className="text-zinc-500">Cancel</Button>
            </div>
        </div>
    );
};

// --- Reward Modal ---

const RewardModal = ({ rewards, onClose }: { rewards: Reward, onClose: () => void }) => {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-xl flex items-center justify-center p-6"
        >
            <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                className="w-full max-w-sm bg-zinc-950 border border-white/5 rounded-2xl overflow-hidden shadow-2xl"
            >
                <div className="p-8 text-center space-y-6">
                    <div className="flex justify-center">
                         <div className="w-16 h-16 rounded-2xl bg-brand-accent/10 flex items-center justify-center border border-brand-accent/20 relative">
                            <Trophy size={32} className="text-brand-accent" />
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                                className="absolute inset-0 border border-brand-accent/20 border-dashed rounded-2xl"
                            />
                         </div>
                    </div>

                    <div className="space-y-1">
                        <h3 className="text-xl font-bold text-zinc-100 uppercase tracking-wider">Mission Success</h3>
                        <p className="text-[10px] text-zinc-500 uppercase tracking-[0.2em]">Asset allocation complete</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div className="p-4 rounded-xl bg-zinc-900/50 border border-white/[0.03]">
                            <div className="flex items-center justify-center gap-1.5 mb-1">
                                <Sparkles size={12} className="text-brand-accent" />
                                <span className="text-[9px] font-bold text-zinc-500 uppercase">Shards</span>
                            </div>
                            <span className="text-xl font-mono font-bold text-zinc-100">+{rewards.shards}</span>
                        </div>
                        <div className="p-4 rounded-xl bg-zinc-900/50 border border-white/[0.03]">
                            <div className="flex items-center justify-center gap-1.5 mb-1">
                                <Zap size={12} className="text-zinc-500" />
                                <span className="text-[9px] font-bold text-zinc-500 uppercase">Experience</span>
                            </div>
                            <span className="text-xl font-mono font-bold text-zinc-100">+{rewards.xp}</span>
                        </div>
                    </div>

                    {rewards.character && (
                        <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/20 flex items-center gap-4 text-left">
                            <div className="w-12 h-12 rounded bg-zinc-800 overflow-hidden border border-white/10 shrink-0">
                                <img src={rewards.character.img_url} alt={rewards.character.name} className="w-full h-full object-cover" />
                            </div>
                            <div className="min-w-0">
                                <div className="text-[8px] font-bold text-purple-400 uppercase tracking-widest mb-0.5">Character Drop</div>
                                <div className="text-xs font-bold text-zinc-100 truncate">{rewards.character.name}</div>
                                <div className="text-[9px] text-zinc-500 truncate">{rewards.character.anime}</div>
                            </div>
                        </div>
                    )}

                    <Button
                        onClick={onClose}
                        className="w-full bg-zinc-100 text-zinc-950 font-bold uppercase tracking-widest text-[10px] py-4"
                    >
                        Confirm Intake
                    </Button>
                </div>
            </motion.div>
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
            await apiFetch(`/minigames/start/${game}`, { method: 'POST' });
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
                        {activeGame === 'cipher_match' && (
                            <CipherMatch onComplete={handleSubmit} onCancel={() => setActiveGame(null)} />
                        )}
                        {activeGame === 'nexus_wheel' && (
                            <NexusWheel onComplete={() => handleSubmit(0)} onCancel={() => setActiveGame(null)} />
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
