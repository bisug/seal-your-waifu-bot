import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Heart,
  Loader2,
  PawPrint,
  RefreshCw,
  Shield,
  Sparkles,
  Swords,
  Wind,
  Zap,
} from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { EmptyState } from '../components/ui/EmptyState';
import { ProgressBar } from '../components/ui/ProgressBar';
import { useToast } from '../components/ui/Toast';
import { Pet, useUser } from '../context/UserContext';
import { cn, formatNumber } from '../utils';

interface MyPetsProps {
  onPetClick?: (pet: Pet) => void;
}

const getPetKey = (pet?: Pet | null) => String(pet?.id || pet?.name || '');

const samePet = (a?: Pet | null, b?: Pet | null) => {
  if (!a || !b) return false;
  const aKeys = new Set([a.id, a.name].filter(Boolean).map(String));
  return [b.id, b.name].filter(Boolean).some((key) => aKeys.has(String(key)));
};

const getPetPower = (pet: Pet) => (
  Number(pet.hp || 0)
  + Number(pet.atk || 0) * 4
  + Number(pet.spd || 0) * 3
  + Math.round(Number(pet.luck || 0) * 100)
);

const getPetImageUrl = (pet: Pet) => {
  const candidates = [
    pet.img,
    pet.img_url,
    pet.image,
    pet.photo_url,
  ];

  return candidates.find((value) => typeof value === 'string' && value.trim())?.trim() || '';
};

const PetImage = ({
  pet,
  iconSize,
  className,
}: {
  pet: Pet;
  iconSize: number;
  className?: string;
}) => {
  const src = getPetImageUrl(pet);
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const canRenderImage = src && failedSrc !== src;

  useEffect(() => {
    setFailedSrc(null);
  }, [src]);

  return (
    <div className={cn('overflow-hidden rounded-lg bg-brand-midnight', className)}>
      {canRenderImage ? (
        <img
          src={src}
          alt={pet.name}
          className="h-full w-full object-cover"
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setFailedSrc(src)}
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-brand-midnight text-neutral-700">
          <PawPrint size={iconSize} />
        </div>
      )}
    </div>
  );
};

const StatPill = ({
  icon: Icon,
  label,
  value,
  tone = 'neutral',
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  tone?: 'neutral' | 'accent' | 'danger' | 'success';
}) => (
  <div className="min-w-0 rounded-lg border border-white/5 bg-brand-midnight px-3 py-2.5">
    <div className="flex items-center gap-1.5 text-[10px] font-semibold text-neutral-500">
      <Icon
        size={12}
        className={cn(
          tone === 'accent' && 'text-brand-accent',
          tone === 'danger' && 'text-red-400',
          tone === 'success' && 'text-emerald-400',
          tone === 'neutral' && 'text-neutral-600'
        )}
      />
      <span className="truncate">{label}</span>
    </div>
    <p className="mt-1 truncate text-sm font-bold text-white tabular-nums">{value}</p>
  </div>
);

const InlineStat = ({
  icon: Icon,
  label,
  value,
  tone = 'neutral',
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  tone?: 'neutral' | 'accent' | 'danger' | 'success';
}) => (
  <div className="min-w-0">
    <div className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold text-neutral-500">
      <Icon
        size={11}
        className={cn(
          tone === 'accent' && 'text-brand-accent',
          tone === 'danger' && 'text-red-400',
          tone === 'success' && 'text-emerald-400',
          tone === 'neutral' && 'text-neutral-600'
        )}
      />
      <span className="truncate">{label}</span>
    </div>
    <p className="truncate text-sm font-bold text-white tabular-nums">{value}</p>
  </div>
);

const ActivePetCard = ({ pet, onOpen }: { pet: Pet; onOpen?: (pet: Pet) => void }) => (
  <button
    type="button"
    onClick={() => onOpen?.(pet)}
    className="w-full rounded-lg border border-brand-accent/20 bg-brand-accent/10 p-4 text-left transition-colors active:scale-[0.99]"
  >
    <div className="grid grid-cols-[84px_minmax(0,1fr)] gap-4 sm:grid-cols-[112px_minmax(0,1fr)]">
      <PetImage pet={pet} iconSize={24} className="aspect-square border border-brand-accent/25" />

      <div className="min-w-0 self-center">
        <div className="mb-2 flex min-w-0 items-center gap-2">
          <h2 className="truncate text-xl font-bold tracking-tight text-white sm:text-2xl">{pet.name}</h2>
          <span className="shrink-0 rounded-lg border border-brand-accent/20 bg-brand-accent/15 px-2 py-1 text-[10px] font-bold text-brand-accent">
            Active
          </span>
        </div>
        <p className="line-clamp-2 text-xs font-medium leading-relaxed text-neutral-400">
          {pet.desc || pet.ability || 'This companion is currently active.'}
        </p>

        <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-white/5 pt-4 sm:grid-cols-4">
          <InlineStat icon={Activity} label="Level" value={pet.level || 1} tone="success" />
          <InlineStat icon={Heart} label="Affection" value={`${pet.affection ?? 0}%`} tone="danger" />
          <InlineStat icon={Swords} label="ATK" value={pet.atk ?? 0} tone="accent" />
          <InlineStat icon={Wind} label="SPD" value={pet.spd ?? 0} />
        </div>

        <div className="mt-4">
          <ProgressBar current={pet.xp || 0} total={Math.max(1, pet.xp_needed || 100)} compact />
        </div>
      </div>
    </div>
  </button>
);

const PetCard = ({
  pet,
  isActive,
  switching,
  onOpen,
  onActivate,
}: {
  pet: Pet;
  isActive: boolean;
  switching: boolean;
  onOpen?: (pet: Pet) => void;
  onActivate: (pet: Pet) => void;
}) => (
  <div
    className={cn(
      'rounded-lg border bg-brand-deep p-3 transition-colors',
      isActive ? 'border-brand-accent/25 bg-brand-accent/5' : 'border-white/5'
    )}
  >
    <button
      type="button"
      onClick={() => onOpen?.(pet)}
      className="grid w-full grid-cols-[64px_minmax(0,1fr)] gap-3 text-left"
    >
      <PetImage pet={pet} iconSize={20} className="aspect-square border border-white/10" />

      <div className="min-w-0 py-0.5">
        <div className="mb-1 flex min-w-0 items-center gap-2">
          <h3 className="truncate text-sm font-bold text-white">{pet.name}</h3>
          {isActive && <CheckCircle2 size={14} className="shrink-0 text-brand-accent" />}
        </div>
        <p className="truncate text-xs font-semibold text-brand-accent">{pet.ability || 'No ability'}</p>
        <div className="mt-2 flex flex-wrap gap-2 text-[10px] font-semibold text-neutral-500">
          <span>Lv. {pet.level || 1}</span>
          <span>{pet.affection ?? 0}% affection</span>
          <span>{pet.mood || 'Neutral'}</span>
        </div>
      </div>
    </button>

    <div className="mt-3 grid grid-cols-3 gap-3 border-t border-white/5 pt-3">
      <InlineStat icon={Shield} label="HP" value={pet.hp ?? 0} />
      <InlineStat icon={Swords} label="ATK" value={pet.atk ?? 0} tone="accent" />
      <InlineStat icon={Wind} label="SPD" value={pet.spd ?? 0} />
    </div>

    <button
      type="button"
      onClick={() => onActivate(pet)}
      disabled={isActive || switching}
      className={cn(
        'mt-3 flex h-10 w-full items-center justify-center gap-2 rounded-lg text-xs font-bold transition-all active:scale-95',
        isActive
          ? 'border border-brand-accent/20 bg-brand-accent/10 text-brand-accent'
          : 'bg-white text-brand-midnight',
        switching && 'opacity-70'
      )}
    >
      {switching ? <Loader2 size={14} className="animate-spin" /> : isActive ? <CheckCircle2 size={14} /> : <Zap size={14} />}
      <span>{isActive ? 'Active pet' : 'Set active'}</span>
    </button>
  </div>
);

export const MyPets = ({ onPetClick }: MyPetsProps) => {
  const { user, refreshUser } = useUser();
  const { addToast } = useToast();
  const [switching, setSwitching] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const pets = useMemo(() => user?.pets || [], [user?.pets]);
  const currentPet = useMemo(() => {
    if (!pets.length) return user?.current_pet || null;
    return pets.find((pet) => pet.is_active || samePet(pet, user?.current_pet)) || user?.current_pet || pets[0];
  }, [pets, user?.current_pet]);

  const sortedPets = useMemo(() => (
    [...pets].sort((a, b) => {
      const activeDiff = Number(samePet(b, currentPet) || b.is_active) - Number(samePet(a, currentPet) || a.is_active);
      if (activeDiff !== 0) return activeDiff;
      const levelDiff = Number(b.level || 1) - Number(a.level || 1);
      if (levelDiff !== 0) return levelDiff;
      return a.name.localeCompare(b.name);
    })
  ), [currentPet, pets]);

  const summary = useMemo(() => {
    const bestPet = pets.reduce<Pet | null>((best, pet) => (!best || getPetPower(pet) > getPetPower(best) ? pet : best), null);
    const averageAffection = pets.length
      ? Math.round(pets.reduce((total, pet) => total + Number(pet.affection || 0), 0) / pets.length)
      : 0;

    return {
      total: pets.length,
      averageAffection,
      bestPet,
      totalPower: pets.reduce((total, pet) => total + getPetPower(pet), 0),
    };
  }, [pets]);

  const handleRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    try {
      await refreshUser();
    } finally {
      setRefreshing(false);
    }
  };

  const handleSetActive = async (pet: Pet) => {
    const petRef = getPetKey(pet);
    if (!petRef || switching || samePet(pet, currentPet) || pet.is_active) return;

    setSwitching(petRef);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      await apiFetch(`/pets/set_active/${encodeURIComponent(petRef)}`, { method: 'POST' });
      await refreshUser();
      addToast(`${pet.name} is now active`, 'success');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    } catch (err: any) {
      addToast(getErrorMessage(err), 'error');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    } finally {
      setSwitching(null);
    }
  };

  if (!user) return null;

  return (
    <div className="pb-20 pt-4 max-w-5xl mx-auto">
      <header className="px-4 pb-5 mb-5 border-b border-white/5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <PawPrint size={18} className="text-brand-accent shrink-0" />
              <h1 className="text-lg font-bold text-white tracking-tight">My Pets</h1>
            </div>
            <p className="text-sm font-medium text-neutral-400 leading-snug">
              Review companion stats and choose the pet that should stay active.
            </p>
          </div>

          <button
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2.5 rounded-lg bg-brand-deep border border-white/5 text-neutral-400 hover:text-white hover:bg-white/5 disabled:opacity-60 transition-colors active:scale-95 shrink-0"
            aria-label="Refresh pets"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatPill icon={PawPrint} label="Owned" value={summary.total} tone="accent" />
          <StatPill icon={Heart} label="Affection" value={`${summary.averageAffection}%`} tone="danger" />
          <StatPill icon={Shield} label="Power" value={formatNumber(summary.totalPower)} tone="success" />
          <StatPill icon={Sparkles} label="Best" value={summary.bestPet?.name || 'None'} />
        </div>
      </header>

      <div className="space-y-6 px-4">
        {currentPet && (
          <section>
            <div className="mb-3 flex items-center gap-2">
              <Zap size={15} className="text-brand-accent" />
              <h2 className="text-sm font-bold text-white">Active companion</h2>
            </div>
            <ActivePetCard pet={currentPet} onOpen={onPetClick} />
          </section>
        )}

        <section>
          <div className="mb-3 flex items-end justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Sparkles size={15} className="text-brand-accent" />
                <h2 className="text-sm font-bold text-white">Collection</h2>
              </div>
              <p className="mt-1 text-xs font-medium text-neutral-500">
                Active pet stays first, then higher-level companions.
              </p>
            </div>
          </div>

          {sortedPets.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sortedPets.map((pet) => {
                const petKey = getPetKey(pet);
                const isActive = pet.is_active || samePet(pet, currentPet);
                return (
                  <PetCard
                    key={petKey || pet.name}
                    pet={pet}
                    isActive={isActive}
                    switching={switching === petKey}
                    onOpen={onPetClick}
                    onActivate={handleSetActive}
                  />
                );
              })}
            </div>
          ) : (
            <EmptyState
              icon={PawPrint}
              title="No pets yet"
              message="Visit the Pet Store to buy your first companion."
            />
          )}
        </section>
      </div>
    </div>
  );
};
