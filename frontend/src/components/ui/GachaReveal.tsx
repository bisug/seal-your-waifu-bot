import React, { useEffect } from 'react';
import { Character } from '../../context/UserContext';
import { cn } from '../../utils';

interface GachaRevealProps {
    character: Character | null;
    onClose: () => void;
}

export const GachaReveal = ({ character, onClose }: GachaRevealProps) => {
    useEffect(() => {
        if (character) {
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
        }
    }, [character]);

    if (!character) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-brand-midnight/95"
            onClick={onClose}
        >
            <div
                className="relative w-full max-w-sm aspect-[3/4] rounded-2xl overflow-hidden bg-slate-900 border border-white/10 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                <img
                    src={character.img_url}
                    alt={character.name}
                    className="absolute inset-0 w-full h-full object-cover"
                />

                <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-transparent" />

                <div className="absolute bottom-0 inset-x-0 p-6 flex flex-col items-center text-center">
                    <span className="text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded bg-brand-accent text-white mb-2">
                        {character.rarity}
                    </span>
                    <h2 className="text-xl font-bold text-white uppercase tracking-tight mb-6">
                        {character.name}
                    </h2>
                    
                    <button
                        onClick={onClose}
                        className="w-full py-4 bg-white text-brand-midnight font-bold uppercase tracking-widest text-[11px] rounded-xl active:scale-95 transition-transform"
                    >
                        Continue
                    </button>
                </div>
            </div>
        </div>
    );
};
