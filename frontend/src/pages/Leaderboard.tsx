import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { BookOpen, Brain, ChartNoAxesColumnIncreasing, Coins, Gem, TrendingUp, Trophy, Target, ShieldCheck, Sparkles } from 'lucide-react';
import { formatNumber } from '../utils';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Avatar } from '../components/Avatar';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { motion, AnimatePresence } from 'framer-motion';

interface LeaderboardUser {
    id: number | string;
    rank?: number;
    first_name?: string;
    last_name?: string;
    full_name?: string;
    username?: string;
    avatar?: string | null;
    value: number;
}

const getDisplayName = (user: LeaderboardUser, index: number) => {
    const name = (user.full_name || user.first_name || '').trim();
    if (name && name.toLowerCase() !== 'user') return name;
    if (user.username) return user.username;
    return `OPERATOR_${String(user.id || index + 1).slice(-4).toUpperCase()}`;
};

const getInitials = (name: string) => {
    const parts = name.replace(/^@/, '').split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'U';
    return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase();
};

export const Leaderboard = () => {
    const [metric, setMetric] = useState('harem');
    const { data, loading, error, execute: fetchLeaderboard } = useApi<LeaderboardUser[]>(`/leaderboard?metric=${metric}`, {}, [metric]);

    const METRICS = [
        { id: 'harem', label: 'Registry', icon: BookOpen },
        { id: 'shards', label: 'Shards', icon: Coins },
        { id: 'zenith', label: 'Zenith', icon: Gem },
        { id: 'level', label: 'Level', icon: TrendingUp },
        { id: 'guesses', label: 'Intel', icon: Brain },
    ];
    const activeMetric = METRICS.find(m => m.id === metric);

    return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10 select-none">
            <header className="space-y-2">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 rounded-2xl bg-warning/10 border border-warning/20 flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.1)]">
                        <Trophy className="text-warning" size={26} />
                   </div>
                   <div className="flex flex-col gap-1">
                      <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Rankings</h1>
                      <div className="flex items-center gap-2">
                         <ShieldCheck size={11} className="text-neutral-600" />
                         <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                            GLOBAL CLEARANCE LEADERBOARD
                         </p>
                      </div>
                   </div>
                </div>
            </header>

            <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2 -mx-5 px-5">
                {METRICS.map(m => (
                    <button
                        key={m.id}
                        onClick={() => {
                            window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                            setMetric(m.id);
                        }}
                        className={cn(
                            "px-6 py-3 rounded-xl flex items-center gap-2.5 border transition-all duration-300 whitespace-nowrap text-[10px] font-black uppercase tracking-[0.2em] relative overflow-hidden group",
                            metric === m.id
                            ? 'bg-white text-black border-white shadow-xl scale-100'
                            : 'bg-white/[0.02] border-white/[0.05] text-neutral-500 hover:text-white hover:border-white/10'
                        )}
                    >
                        <m.icon size={14} strokeWidth={3} className={metric === m.id ? "text-black" : "text-neutral-700 group-hover:text-neutral-400"} />
                        <span>{m.label}</span>
                    </button>
                ))}
            </div>

            <div className="space-y-3">
                <AnimatePresence mode="wait">
                    {error && !data ? (
                        <div className="py-12">
                            <ErrorState message={error} onAction={fetchLeaderboard} />
                        </div>
                    ) : loading ? (
                        <div className="space-y-3">
                           {Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-2xl" />)}
                        </div>
                    ) : data && data.length > 0 ? (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                            {data?.map((user, i) => {
                                const displayName = getDisplayName(user, i);
                                const rank = user.rank || i + 1;
                                const isTopThree = rank <= 3;

                                return (
                                <Card key={user.id} variant="tactical" className={cn(
                                    "p-4 flex items-center justify-between group transition-all duration-500",
                                    rank === 1 ? "border-warning/30 bg-warning/[0.03] shadow-[0_0_25px_rgba(245,158,11,0.08)]" :
                                    rank === 2 ? "border-neutral-400/20 bg-white/[0.02]" :
                                    rank === 3 ? "border-orange-500/20 bg-white/[0.02]" : "border-white/[0.03] bg-white/[0.01]"
                                )}>
                                    <div className="flex items-center gap-5 min-w-0">
                                        <div className="relative">
                                            <div className={cn(
                                                "w-11 h-11 rounded-2xl flex items-center justify-center text-[13px] font-black shrink-0 border transition-all duration-700 relative z-10 group-hover:scale-105 font-mono",
                                                rank === 1 ? 'bg-warning/20 text-warning border-warning/40 shadow-[0_0_15px_rgba(245,158,11,0.2)]' :
                                                rank === 2 ? 'bg-neutral-400/20 text-neutral-300 border-neutral-400/30' :
                                                rank === 3 ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                                                'bg-brand-midnight text-neutral-700 border-white/[0.05]'
                                            )}>
                                                {rank}
                                            </div>
                                            {isTopThree && (
                                                <div className={cn(
                                                    "absolute -inset-1 rounded-2xl blur-md opacity-20 transition-opacity duration-700 group-hover:opacity-40",
                                                    rank === 1 ? "bg-warning" : rank === 2 ? "bg-neutral-400" : "bg-orange-500"
                                                )} />
                                            )}
                                        </div>
                                        <div className="flex items-center gap-4 min-w-0">
                                            <Avatar
                                                src={user.avatar}
                                                alt={displayName}
                                                fallbackText={getInitials(displayName)}
                                                className="w-12 h-12 rounded-2xl bg-brand-midnight border border-white/[0.05] shadow-lg group-hover:border-brand-accent/20 transition-colors duration-500"
                                            />
                                            <div className="min-w-0 space-y-1">
                                                <p className="text-[15px] font-black text-white uppercase tracking-tight truncate drop-shadow-sm group-hover:text-brand-accent transition-colors">
                                                    {displayName}
                                                </p>
                                                {user.username ? (
                                                    <p className="text-[10px] font-bold text-neutral-600 truncate uppercase tracking-widest leading-none">@{user.username}</p>
                                                ) : (
                                                    <p className="text-[9px] font-black text-neutral-800 truncate uppercase tracking-[0.2em] leading-none">SECURE_ID_{String(user.id).slice(0, 6)}</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right shrink-0 pl-6 space-y-1.5">
                                        <div className="flex items-center justify-end gap-2 px-3 py-1.5 rounded-xl bg-white/[0.02] border border-white/[0.05] group-hover:border-white/[0.1] transition-all">
                                            <span className="text-sm font-black text-white tabular-nums font-mono drop-shadow-md">{formatNumber(user.value)}</span>
                                            {activeMetric && <activeMetric.icon size={11} className={cn(
                                                "transition-transform group-hover:scale-110 duration-500",
                                                rank === 1 ? 'text-warning' : rank === 2 ? 'text-neutral-300' : rank === 3 ? 'text-orange-400' : 'text-brand-accent/40'
                                            )} />}
                                        </div>
                                        <div className="flex items-center justify-end gap-1.5 opacity-40">
                                            <div className="h-px w-3 bg-neutral-800" />
                                            <p className="text-[8px] font-black text-neutral-600 uppercase tracking-[0.3em]">{activeMetric?.label || metric}</p>
                                        </div>
                                    </div>
                                </Card>
                                );
                            })}
                        </motion.div>
                    ) : (
                        <Card variant="tactical" className="py-32 border-dashed border-white/[0.08] bg-white/[0.01] text-center flex flex-col items-center justify-center space-y-4">
                            <div className="w-16 h-16 rounded-full border border-white/[0.05] flex items-center justify-center opacity-10">
                               <ChartNoAxesColumnIncreasing size={40} />
                            </div>
                            <div className="space-y-1">
                                <p className="text-[11px] font-black text-neutral-700 uppercase tracking-[0.4em]">No Ranking Data</p>
                                <p className="text-[9px] font-bold text-neutral-800 uppercase tracking-widest">AWAITING SYSTEM SYNCHRONIZATION</p>
                            </div>
                        </Card>
                    )}
                </AnimatePresence>
            </div>

            <div className="flex items-center justify-center gap-3 opacity-20 py-4">
               <Sparkles size={12} className="text-brand-accent" />
               <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Mainframe Online</span>
            </div>
        </div>
    );
};
