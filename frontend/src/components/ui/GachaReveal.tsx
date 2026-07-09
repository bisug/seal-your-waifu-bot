import { useEffect, useMemo } from 'react';
import { Character } from '../../context/UserContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Heart, ShieldCheck, Target, Zap } from 'lucide-react';
import { Badge } from './Badge';
import { Button } from './Button';

interface GachaRevealProps {
    character: Character | null;
    onClose: () => void;
}

export const GachaReveal = ({ character, onClose }: GachaRevealProps) => {
    const particles = useMemo(() => {
        return [...Array(6)].map((_, i) => ({
            delay: i * 0.2,
            x: (i - 2.5) * 40,
            duration: 2 + (i % 3) // Use deterministic values for render purity
        }));
    }, []);

    useEffect(() => {
        if (character) {
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
        }
    }, [character]);

    if (!character) return null;

    const rarityLabel = character.rarity.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim().toUpperCase();

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black select-none overflow-hidden">
                {/* Background Effects */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.15),transparent_70%)]"
                />
                <div className="tactical-grid absolute inset-0 opacity-20 pointer-events-none" />
                <div className="absolute inset-0 bg-scanline opacity-[0.05] pointer-events-none" />

                <motion.div
                    initial={{ opacity: 0, scale: 0.8, rotateY: 90 }}
                    animate={{ opacity: 1, scale: 1, rotateY: 0 }}
                    transition={{ type: 'spring', damping: 20, stiffness: 100, mass: 1 }}
                    className="relative w-[90vw] max-w-[400px] aspect-[3/4.5] flex flex-col items-center"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Card Container */}
                    <div className="w-full h-full rounded-[40px] border border-white/20 bg-brand-midnight shadow-[0_0_100px_rgba(0,0,0,0.9)] overflow-hidden relative group">
                        {/* Particle Effects */}
                        <div className="absolute inset-0 pointer-events-none z-20">
                             {particles.map((p, i) => (
                                 <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 100, x: 0 }}
                                    animate={{ opacity: [0, 1, 0], y: -200, x: p.x }}
                                    transition={{ duration: p.duration, repeat: Infinity, delay: p.delay }}
                                    className="absolute bottom-0 left-1/2 w-1 h-1 bg-brand-accent rounded-full blur-[2px]"
                                 />
                             ))}
                        </div>

                        <img
                            src={character.img_url}
                            alt={character.name}
                            className="absolute inset-0 w-full h-full object-cover transition-transform duration-[2s] group-hover:scale-110"
                        />

                        {/* Top Gradient */}
                        <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-black/80 to-transparent z-10" />

                        {/* Bottom Gradient */}
                        <div className="absolute inset-x-0 bottom-0 h-[60%] bg-gradient-to-t from-brand-midnight via-brand-midnight/60 to-transparent z-10" />

                        {/* Card Info Overlay */}
                        <div className="absolute top-8 left-8 z-20 space-y-2">
                             <div className="flex items-center gap-2 opacity-50">
                                <Target size={12} className="text-brand-accent" />
                                <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white font-mono">ASSET_SECURED</span>
                             </div>
                             <div className="h-0.5 w-12 bg-brand-accent" />
                        </div>

                        <div className="absolute top-8 right-8 z-20">
                           <div className="w-10 h-10 rounded-full bg-black/40 backdrop-blur-md border border-white/10 flex items-center justify-center">
                              <ShieldCheck size={20} className="text-success" />
                           </div>
                        </div>

                        <div className="absolute bottom-0 inset-x-0 p-10 flex flex-col items-center text-center z-20 space-y-6">
                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.3 }}
                                className="space-y-4"
                            >
                                <Badge variant="primary" size="md" className="px-6 py-1.5 rounded-full font-black tracking-[0.3em] bg-brand-accent text-white border-none shadow-[0_0_30px_rgba(59,130,246,0.4)] text-[10px] uppercase">
                                    {rarityLabel}
                                </Badge>

                                <div className="space-y-1">
                                    <h2 className="text-4xl font-black text-white tracking-tighter uppercase drop-shadow-2xl">
                                        {character.name}
                                    </h2>
                                    <div className="flex items-center justify-center gap-2 opacity-40">
                                       <Zap size={12} className="text-brand-accent" />
                                       <p className="text-[10px] font-bold text-white uppercase tracking-[0.2em]">{character.anime}</p>
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.6 }}
                                className="w-full pt-4"
                            >
                                <Button
                                    onClick={onClose}
                                    className="w-full h-16 rounded-[22px] bg-white text-black font-black uppercase text-[12px] tracking-[0.4em] shadow-2xl active:scale-95 transition-all"
                                >
                                    AUTHORIZE_ENTRY
                                </Button>
                            </motion.div>
                        </div>
                    </div>
                    
                    {/* Visual Flourish Under Card */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.1 }}
                        transition={{ delay: 1 }}
                        className="mt-12 flex items-center gap-4"
                    >
                       <div className="h-px w-20 bg-white" />
                       <Sparkles size={20} className="text-brand-accent" />
                       <div className="h-px w-20 bg-white" />
                    </motion.div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
