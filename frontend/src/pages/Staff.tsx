import React, { useMemo, useState } from 'react';
import {
  BadgeCheck,
  ChevronDown,
  ChevronUp,
  Coins,
  Gem,
  Image,
  PawPrint,
  ShieldCheck,
  UploadCloud,
  UsersRound,
  Terminal,
  Target,
  Sparkles,
  Activity,
  History,
} from 'lucide-react';
import { Avatar } from '../components/Avatar';
import { ErrorState } from '../components/ui/ErrorState';
import { useApi } from '../hooks/useApi';
import { cn, formatNumber } from '../utils';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { motion, AnimatePresence } from 'framer-motion';

interface UploadReward {
  balance?: number;
  zenith?: number;
}

interface StaffUploadItem {
  type: 'character' | 'pet';
  id?: string | null;
  name: string;
  subtitle?: string | null;
  rarity?: string | null;
  image?: string | null;
  uploaded_at?: string | null;
  enabled?: boolean;
}

interface StaffMember {
  id: number;
  display_name: string;
  username?: string | null;
  avatar?: string | null;
  role_label: string;
  role_tag: string;
  role_symbol: string;
  upload_reward?: UploadReward | null;
  role_benefits?: string[];
  stats: {
    balance: number;
    zenith: number;
    level: number;
    xp: number;
  };
  contributions: {
    total_uploads: number;
    character_uploads: number;
    pet_uploads: number;
    sources: Record<string, number>;
  };
  uploads: {
    characters: StaffUploadItem[];
    pets: StaffUploadItem[];
    limit?: number;
    truncated?: boolean;
  };
}

interface StaffContributionsResponse {
  summary: {
    total_staff: number;
    total_uploads: number;
    character_uploads: number;
    pet_uploads: number;
  };
  staff: StaffMember[];
}

const SOURCE_LABELS: Record<string, string> = {
  web_character: 'WEB_CHAR',
  bot_character: 'BOT_CHAR',
  web_pet: 'WEB_PET',
  bot_pet: 'BOT_PET',
};

const getInitials = (name: string) => {
  const parts = name.replace(/^@/, '').split(/\s+/).filter(Boolean);
  return (parts.slice(0, 2).map(part => part[0]).join('') || 'U').toUpperCase();
};

const formatRewardLabel = (reward?: UploadReward | null) => {
  if (!reward) return '';
  return [
    reward.balance ? `${formatNumber(reward.balance)} SHARDS` : '',
    reward.zenith ? `${formatNumber(reward.zenith)} ZENITH` : '',
  ].filter(Boolean).join(' + ');
};

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }).toUpperCase();
};

const sourceEntries = (sources: Record<string, number>) => (
  Object.entries(SOURCE_LABELS)
    .map(([key, label]) => ({ key, label, value: sources[key] || 0 }))
    .filter(item => item.value > 0)
);

const allUploadsFor = (member: StaffMember) => (
  [...member.uploads.characters, ...member.uploads.pets].sort((a, b) => {
    const aTime = a.uploaded_at ? new Date(a.uploaded_at).getTime() : 0;
    const bTime = b.uploaded_at ? new Date(b.uploaded_at).getTime() : 0;
    return bTime - aTime;
  })
);

const StaffDetails = ({ member }: { member: StaffMember }) => {
  const reward = formatRewardLabel(member.upload_reward);
  const sources = sourceEntries(member.contributions.sources);
  const uploads = allUploadsFor(member);

  return (
    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-6 border-t border-white/[0.04] pt-6 space-y-6 overflow-hidden">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
            { icon: Image, label: 'ASSETS', value: formatNumber(member.contributions.character_uploads) },
            { icon: PawPrint, label: 'UNITS', value: formatNumber(member.contributions.pet_uploads) },
            { icon: Gem, label: 'ZENITH', value: formatNumber(member.stats.zenith) },
            { icon: Coins, label: 'SHARDS', value: formatNumber(member.stats.balance) },
        ].map((stat, i) => (
            <Card key={i} variant="tactical" className="p-3 border-white/[0.03] bg-black/20">
               <div className="flex items-center gap-2 mb-2">
                  <stat.icon size={11} className="text-brand-accent/60" />
                  <span className="text-[8px] font-black text-neutral-600 uppercase tracking-widest leading-none">{stat.label}</span>
               </div>
               <p className="text-xs font-black text-white tabular-nums font-mono leading-none">{stat.value}</p>
            </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge variant="tactical" size="xs" className="px-2 py-1 border-white/10 bg-white/[0.02]">
          LVL {formatNumber(member.stats.level)}
        </Badge>
        {reward && (
          <Badge variant="success" size="xs" className="px-2 py-1 border-success/10 bg-success/5 text-success">
            REWARD: {reward}
          </Badge>
        )}
        {sources.map(source => (
          <Badge key={source.key} variant="secondary" size="xs" className="px-2 py-1 font-mono">
            {source.label}: {formatNumber(source.value)}
          </Badge>
        ))}
      </div>

      {member.role_benefits && member.role_benefits.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {member.role_benefits.map(benefit => (
            <Badge key={benefit} variant="primary" size="xs" className="px-2 py-1 border-brand-accent/20 bg-brand-accent/5">
              {benefit.toUpperCase()}
            </Badge>
          ))}
        </div>
      )}

      <div className="space-y-3 pt-2">
        <div className="flex items-center gap-2 px-1">
           <History size={12} className="text-neutral-700" />
           <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.3em]">CONTRIBUTION_LOG</span>
        </div>
        {uploads.length > 0 ? (
          <div className="space-y-1.5 bg-black/40 rounded-2xl border border-white/[0.03] p-1.5">
            {uploads.map(item => (
                <div key={`${item.type}:${item.id}:${item.name}`} className="flex items-center gap-3 p-2 hover:bg-white/[0.02] rounded-xl transition-colors group/item">
                    <div className="h-10 w-10 shrink-0 overflow-hidden rounded-lg border border-white/10 bg-brand-midnight">
                        {item.image ? (
                        <img src={item.image} alt={item.name} className="h-full w-full object-cover opacity-80 group-hover/item:opacity-100 transition-opacity" />
                        ) : (
                        <div className="flex h-full w-full items-center justify-center text-neutral-800">
                            {item.type === 'pet' ? <PawPrint size={18} /> : <Image size={18} />}
                        </div>
                        )}
                    </div>
                    <div className="min-w-0 flex-1">
                        <div className="flex min-w-0 items-center gap-2">
                        <p className="truncate text-xs font-black text-white uppercase tracking-tight">{item.name}</p>
                        <Badge variant="tactical" size="xs" className="px-1 py-0 border-white/5 opacity-40 font-mono text-[7px]">
                            {item.type === 'pet' ? 'UNIT' : 'ASSET'}
                        </Badge>
                        </div>
                        <p className="truncate text-[9px] font-bold text-neutral-600 uppercase tracking-widest mt-0.5">
                        {[item.subtitle, item.rarity, item.id ? `ID_${item.id}` : ''].filter(Boolean).join(' • ')}
                        </p>
                    </div>
                    <div className="shrink-0 text-right pr-2">
                        <p className="text-[8px] font-black text-neutral-500 font-mono">{formatDate(item.uploaded_at)}</p>
                        {item.type === 'pet' && item.enabled === false && (
                        <p className="text-[8px] font-black text-danger uppercase tracking-tighter">OFFLINE</p>
                        )}
                    </div>
                </div>
            ))}
            {member.uploads.truncated && (
              <div className="py-3 text-center border-t border-white/[0.03]">
                 <p className="text-[8px] font-black text-neutral-700 uppercase tracking-[0.2em]">
                    LIMIT REACHED: SHOWING LATEST {formatNumber(member.uploads.limit || uploads.length)} RECORDS
                 </p>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center bg-black/20 rounded-2xl border border-dashed border-white/5">
             <p className="text-[9px] font-black text-neutral-800 uppercase tracking-widest">No contribution records detected.</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const Staff = () => {
  const { data, loading, error, execute } = useApi<StaffContributionsResponse>('/admin/sudos/contributions');
  const [openStaffId, setOpenStaffId] = useState<number | null>(null);

  const rankedStaff = useMemo(() => {
    return [...(data?.staff || [])].sort((a, b) => {
      const totalDiff = b.contributions.total_uploads - a.contributions.total_uploads;
      return totalDiff || a.display_name.localeCompare(b.display_name);
    });
  }, [data]);

  return (
    <div className="pb-32 pt-8 max-w-4xl mx-auto adaptive-px space-y-10 select-none">
      <header className="space-y-2">
        <div className="flex items-center gap-4">
           <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                <ShieldCheck className="text-brand-accent" size={26} />
           </div>
           <div className="flex flex-col gap-1">
              <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Admin Terminal</h1>
              <div className="flex items-center gap-2">
                 <Terminal size={11} className="text-neutral-600" />
                 <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                    STAFF RECORDS & CONTRIBUTION PROTOCOL
                 </p>
              </div>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
            { label: 'STAFF', value: data?.summary.total_staff || 0, icon: UsersRound, variant: 'primary' },
            { label: 'UPLOADS', value: data?.summary.total_uploads || 0, icon: UploadCloud, variant: 'default' },
            { label: 'ASSETS', value: data?.summary.character_uploads || 0, icon: Image, variant: 'success' },
            { label: 'UNITS', value: data?.summary.pet_uploads || 0, icon: PawPrint, variant: 'warning' },
        ].map((item, i) => (
            <Card key={i} variant="tactical" className="p-4 border-white/[0.04] bg-white/[0.01]">
              <div className="flex items-center gap-2 mb-2">
                <item.icon size={12} className={cn(
                    item.variant === 'primary' ? 'text-brand-accent' :
                    item.variant === 'success' ? 'text-success' :
                    item.variant === 'warning' ? 'text-amber-500' : 'text-neutral-600'
                )} />
                <span className="text-[9px] font-black text-neutral-600 uppercase tracking-widest leading-none">{item.label}</span>
              </div>
              <p className="text-sm font-black text-white tabular-nums leading-none font-mono">{formatNumber(item.value)}</p>
            </Card>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2 px-1">
            <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">PERSONNEL_ROSTER</h2>
            <div className="h-px flex-1 bg-white/[0.03]" />
        </div>

        <AnimatePresence mode="wait">
        {error && !data ? (
            <div className="py-12">
                <ErrorState message={error} onAction={() => execute()} />
            </div>
        ) : loading ? (
            <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton key={index} className="h-24 w-full rounded-2xl" />
                ))}
            </div>
        ) : rankedStaff.length > 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            {rankedStaff.map(member => {
                const isOpen = openStaffId === member.id;

                return (
                <Card key={member.id} variant="tactical" className={cn(
                    "p-5 transition-all duration-500 relative overflow-hidden",
                    isOpen ? "border-brand-accent/30 bg-brand-accent/[0.01]" : "bg-white/[0.01] border-white/[0.03]"
                )}>
                    <button
                        type="button"
                        onClick={() => {
                            window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                            setOpenStaffId(isOpen ? null : member.id);
                        }}
                        className="flex w-full items-center gap-4 text-left group"
                    >
                        <div className="relative shrink-0">
                            <Avatar
                                src={member.avatar}
                                alt={member.display_name}
                                fallbackText={getInitials(member.display_name)}
                                className="h-14 w-14 rounded-2xl border border-white/10 bg-brand-midnight shadow-lg group-hover:border-brand-accent/30 transition-colors"
                            />
                            {isOpen && <div className="absolute -inset-1 bg-brand-accent/20 blur-md rounded-2xl -z-10 animate-pulse" />}
                        </div>
                        <div className="min-w-0 flex-1 space-y-1.5">
                            <div className="flex min-w-0 flex-wrap items-center gap-3">
                                <h2 className="truncate text-lg font-black text-white uppercase tracking-tight">{member.display_name}</h2>
                                <Badge variant="primary" size="xs" className="px-2 py-0.5 rounded-md font-black border-brand-accent/30 bg-brand-accent/10">
                                    {member.role_symbol} {member.role_tag}
                                </Badge>
                            </div>
                            <p className="truncate text-[10px] font-bold text-neutral-600 uppercase tracking-widest leading-none">
                                {[member.username ? `@${member.username}` : '', `ID_${member.id}`, member.role_label].filter(Boolean).join(' • ')}
                            </p>
                        </div>
                        <div className="shrink-0 text-right pr-4 hidden xs:block">
                            <p className="text-xl font-black text-white tabular-nums font-mono drop-shadow-md leading-none mb-1">{formatNumber(member.contributions.total_uploads)}</p>
                            <p className="text-[8px] font-black uppercase tracking-widest text-neutral-700">UPLOADS</p>
                        </div>
                        <div className={cn(
                            'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition-all duration-300',
                            isOpen ? 'bg-brand-accent border-brand-accent text-black shadow-[0_0_15px_rgba(59,130,246,0.4)] rotate-180' : 'bg-brand-midnight border-white/10 text-neutral-500 hover:text-white hover:border-white/30'
                        )}>
                            <ChevronDown size={20} strokeWidth={3} />
                        </div>
                    </button>

                    <AnimatePresence>
                       {isOpen && <StaffDetails member={member} />}
                    </AnimatePresence>
                </Card>
                );
            })}
            </motion.div>
        ) : (
            <Card variant="tactical" className="py-24 border-dashed border-white/[0.08] bg-white/[0.01] text-center flex flex-col items-center justify-center space-y-4 rounded-[32px]">
                <div className="w-16 h-16 rounded-full border border-white/5 flex items-center justify-center opacity-10">
                   <Target size={40} />
                </div>
                <p className="text-[11px] font-black text-neutral-700 uppercase tracking-[0.4em]">Personnel Missing</p>
            </Card>
        )}
        </AnimatePresence>
      </div>

      <div className="flex items-center justify-center gap-3 opacity-20 py-4">
         <Sparkles size={12} className="text-brand-accent" />
         <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Security Mainframe Active</span>
      </div>
    </div>
  );
};
