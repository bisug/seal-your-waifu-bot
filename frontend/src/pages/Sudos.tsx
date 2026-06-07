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
} from 'lucide-react';
import { Avatar } from '../components/Avatar';
import { ErrorState } from '../components/ui/ErrorState';
import { useApi } from '../hooks/useApi';
import { cn, formatNumber } from '../utils';

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
  role_source: string;
  can_upload: boolean;
  can_edit_character: boolean;
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
    persisted_character_uploads: number;
    persisted_pet_uploads: number;
    sources: Record<string, number>;
  };
  uploads: {
    characters: StaffUploadItem[];
    pets: StaffUploadItem[];
  };
}

interface SudoContributionsResponse {
  summary: {
    total_staff: number;
    total_uploads: number;
    character_uploads: number;
    pet_uploads: number;
  };
  staff: StaffMember[];
}

const SOURCE_LABELS: Record<string, string> = {
  web_character: 'Web chars',
  bot_character: 'Bot chars',
  web_pet: 'Web pets',
  bot_pet: 'Bot pets',
};

const getInitials = (name: string) => {
  const parts = name.replace(/^@/, '').split(/\s+/).filter(Boolean);
  return (parts.slice(0, 2).map(part => part[0]).join('') || 'U').toUpperCase();
};

const formatReward = (reward?: UploadReward | null) => {
  if (!reward) return '';
  return [
    reward.balance ? `${formatNumber(reward.balance)} Shards` : '',
    reward.zenith ? `${formatNumber(reward.zenith)} Zenith` : '',
  ].filter(Boolean).join(' + ');
};

const formatDate = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
};

const sourceEntries = (sources: Record<string, number>) => (
  Object.entries(SOURCE_LABELS)
    .map(([key, label]) => ({ key, label, value: sources[key] || 0 }))
    .filter(item => item.value > 0)
);

const StatPill = ({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) => (
  <div className="flex min-w-0 items-center gap-2 rounded-lg border border-white/5 bg-brand-midnight px-3 py-2">
    <Icon size={15} className="shrink-0 text-brand-accent" />
    <div className="min-w-0">
      <p className="text-[10px] font-bold uppercase tracking-wider text-neutral-500">{label}</p>
      <p className="truncate text-sm font-bold text-white tabular-nums">{value}</p>
    </div>
  </div>
);

const UploadRow = ({ item }: { item: StaffUploadItem }) => {
  const isPet = item.type === 'pet';
  const Icon = isPet ? PawPrint : Image;
  return (
    <div className="flex items-center gap-3 border-t border-white/5 py-3 first:border-t-0">
      <div className="h-12 w-12 shrink-0 overflow-hidden rounded-lg border border-white/5 bg-brand-midnight">
        {item.image ? (
          <img src={item.image} alt={item.name} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-neutral-600">
            <Icon size={18} />
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center gap-2">
          <p className="truncate text-sm font-bold text-white">{item.name}</p>
          <span className="shrink-0 rounded border border-white/5 px-1.5 py-0.5 text-[9px] font-bold uppercase text-neutral-400">
            {isPet ? 'Pet' : 'Char'}
          </span>
        </div>
        <p className="truncate text-xs font-medium text-neutral-500">
          {[item.subtitle, item.rarity, item.id ? `ID ${item.id}` : ''].filter(Boolean).join(' · ')}
        </p>
      </div>
      <div className="shrink-0 text-right">
        <p className="text-[10px] font-semibold text-neutral-500">{formatDate(item.uploaded_at)}</p>
        {isPet && item.enabled === false && (
          <p className="text-[10px] font-bold text-red-400">Disabled</p>
        )}
      </div>
    </div>
  );
};

export const Sudos = () => {
  const { data, loading, error, execute } = useApi<SudoContributionsResponse>('/admin/sudos/contributions');
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const rankedStaff = useMemo(() => {
    return [...(data?.staff || [])].sort((a, b) => {
      const totalDiff = b.contributions.total_uploads - a.contributions.total_uploads;
      return totalDiff || a.display_name.localeCompare(b.display_name);
    });
  }, [data]);

  const summaryItems = [
    { label: 'Sudos', value: data?.summary.total_staff || 0, icon: UsersRound },
    { label: 'Uploads', value: data?.summary.total_uploads || 0, icon: UploadCloud },
    { label: 'Characters', value: data?.summary.character_uploads || 0, icon: Image },
    { label: 'Pets', value: data?.summary.pet_uploads || 0, icon: PawPrint },
  ];

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 pb-24 select-none">
      <header className="mb-6 border-b border-white/5 pb-4">
        <div className="mb-1 flex items-center gap-2">
          <ShieldCheck size={18} className="text-brand-accent" />
          <h1 className="text-xl font-bold text-white">Sudos</h1>
        </div>
        <p className="text-sm font-medium text-neutral-400">Staff roles, contribution totals, uploads, and account info.</p>
      </header>

      <div className="mb-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {summaryItems.map(item => (
          <StatPill
            key={item.label}
            icon={item.icon}
            label={item.label}
            value={formatNumber(item.value)}
          />
        ))}
      </div>

      {error && !data ? (
        <ErrorState message={error} onAction={() => execute()} />
      ) : loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-40 animate-pulse rounded-lg border border-white/5 bg-brand-deep" />
          ))}
        </div>
      ) : rankedStaff.length > 0 ? (
        <div className="space-y-4">
          {rankedStaff.map(member => {
            const uploads = [
              ...member.uploads.characters,
              ...member.uploads.pets,
            ].sort((a, b) => {
              const aTime = a.uploaded_at ? new Date(a.uploaded_at).getTime() : 0;
              const bTime = b.uploaded_at ? new Date(b.uploaded_at).getTime() : 0;
              return bTime - aTime;
            });
            const showAll = Boolean(expanded[member.id]);
            const visibleUploads = showAll ? uploads : uploads.slice(0, 4);
            const reward = formatReward(member.upload_reward);
            const sources = sourceEntries(member.contributions.sources);

            return (
              <section key={member.id} className="rounded-lg border border-white/5 bg-brand-deep p-4">
                <div className="flex items-start gap-3">
                  <Avatar
                    src={member.avatar}
                    alt={member.display_name}
                    fallbackText={getInitials(member.display_name)}
                    className="h-12 w-12 rounded-lg border border-white/10 bg-brand-midnight"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex min-w-0 flex-wrap items-center gap-2">
                      <h2 className="truncate text-base font-bold text-white">{member.display_name}</h2>
                      <span className="inline-flex items-center gap-1 rounded border border-brand-accent/20 bg-brand-accent/10 px-1.5 py-0.5 text-[10px] font-bold text-brand-accent">
                        <span className="text-sm leading-none">{member.role_symbol}</span>
                        <span>{member.role_tag}</span>
                      </span>
                    </div>
                    <p className="mt-1 truncate text-xs font-medium text-neutral-500">
                      {[member.username ? `@${member.username}` : '', `ID ${member.id}`, member.role_label].filter(Boolean).join(' · ')}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-lg font-bold text-white tabular-nums">{formatNumber(member.contributions.total_uploads)}</p>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-neutral-500">Uploads</p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <StatPill icon={Image} label="Chars" value={formatNumber(member.contributions.character_uploads)} />
                  <StatPill icon={PawPrint} label="Pets" value={formatNumber(member.contributions.pet_uploads)} />
                  <StatPill icon={Gem} label="Zenith" value={formatNumber(member.stats.zenith)} />
                  <StatPill icon={Coins} label="Shards" value={formatNumber(member.stats.balance)} />
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-bold text-neutral-300">
                    <BadgeCheck size={13} className="text-brand-accent" />
                    Level {formatNumber(member.stats.level)}
                  </span>
                  {reward && (
                    <span className="rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-bold text-neutral-300">
                      Reward: {reward}
                    </span>
                  )}
                  {sources.map(source => (
                    <span key={source.key} className="rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-bold text-neutral-300">
                      {source.label}: {formatNumber(source.value)}
                    </span>
                  ))}
                </div>

                {member.role_benefits && member.role_benefits.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {member.role_benefits.map(benefit => (
                      <span key={benefit} className="rounded-lg border border-brand-accent/10 bg-brand-accent/5 px-2 py-1 text-[10px] font-semibold text-brand-accent">
                        {benefit}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-4 border-t border-white/5 pt-1">
                  {visibleUploads.length > 0 ? (
                    visibleUploads.map(item => <UploadRow key={`${item.type}:${item.id}:${item.name}`} item={item} />)
                  ) : (
                    <div className="py-5 text-center text-sm font-medium text-neutral-500">No upload records yet.</div>
                  )}
                </div>

                {uploads.length > 4 && (
                  <button
                    type="button"
                    onClick={() => setExpanded(prev => ({ ...prev, [member.id]: !showAll }))}
                    className={cn(
                      'mt-2 flex h-9 w-full items-center justify-center gap-2 rounded-lg border border-white/5 text-xs font-bold transition-colors',
                      showAll ? 'bg-white text-brand-midnight' : 'bg-brand-midnight text-neutral-300 hover:text-white'
                    )}
                  >
                    {showAll ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                    {showAll ? 'Show less' : `Show ${uploads.length - 4} more`}
                  </button>
                )}
              </section>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-white/10 bg-brand-deep p-10 text-center">
          <p className="text-sm font-medium text-neutral-500">No sudo records found.</p>
        </div>
      )}
    </div>
  );
};
