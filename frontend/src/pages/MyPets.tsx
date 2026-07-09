import React, { useEffect, useMemo, useState } from 'react';
import {
  CheckCircle2,
  Heart,
  Loader2,
  PawPrint,
  RefreshCw,
  Star,
  Sparkles,
  Swords,
  Wind,
  Target,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { EmptyState } from '../components/ui/EmptyState';
import { ProgressBar } from '../components/ui/ProgressBar';
import { useToast } from '../components/ui/Toast';
import { Pet, useUser } from '../context/UserContext';
import { cn, formatNumber } from '../utils';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { motion, AnimatePresence } from 'framer-motion';

interface MyPetsProps {
  onPetClick?: (pet: Pet) => void;
}

const getPetKey = (pet?: Pet | null) => String(pet?.petid || pet?.id || pet?.name || '');

const getPetImageSrc = (pet?: Pet | null) => {
  const src = String(pet?.img || pet?.img_url || pet?.image || pet?.photo_url || '').trim();
  return /^https?:\/\//i.test(src) || src.startsWith('/') ? src : '';
};

const samePet = (a?: Pet | null, b?: Pet | null) => {
  if (!a || !b) return false;
  const aKeys = new Set([a.petid, a.id, a.name].filter(Boolean).map(String));
  return [b.petid, b.id, b.name].filter(Boolean).some((key) => aKeys.has(String(key)));
};

const getPetPower = (pet: Pet) => (
  Number(pet.hp || 0)
  + Number(pet.atk || 0) * 4
  + Number(pet.spd || 0) * 3
  + Math.round(Number(pet.luck || 0) * 100)
);

const PetImage = ({
  pet,
  iconSize,
  className,
}: {
  pet: Pet;
  iconSize: number;
  className?: string;
}) => {
  const src = getPetImageSrc(pet);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    setImageFailed(false);
  }, [src]);

  return (
    <div className={cn('overflow-hidden bg-brand-midnight relative', className)}>
      {src && !imageFailed ? (
        <img
          key={src}
          src={src}
          alt={pet.name}
          className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-brand-midnight text-neutral-800">
          <PawPrint size={iconSize} />
        </div>
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-60" />
    </div>
  );
};

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
    <div className="mb-1 flex items-center gap-1.5 text-[8px] font-black uppercase tracking-widest text-neutral-600">
      <Icon
        size={10}
        className={cn(
          tone === 'accent' && 'text-brand-accent',
          tone === 'danger' && 'text-red-400',
          tone === 'success' && 'text-emerald-400',
          tone === 'neutral' && 'text-neutral-700'
        )}
      />
      <span className="truncate">{label}</span>
    </div>
    <p className="truncate text-[11px] font-black text-white tabular-nums font-mono leading-none">{value}</p>
  </div>
);

const ActivePetCard = ({ pet, onOpen }: { pet: Pet; onOpen?: (pet: Pet) => void }) => (
  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
    <Card
      variant="tactical"
      className="p-6 border-brand-accent/20 bg-brand-accent/[0.03] shadow-2xl overflow-hidden relative group cursor-pointer"
      onClick={() => onOpen?.(pet)}
    >
        <div className="absolute top-0 right-0 p-4 opacity-[0.02] group-hover:opacity-[0.06] transition-opacity duration-700">
            <ShieldCheck size={120} />
        </div>

        <div className="grid grid-cols-[100px_minmax(0,1fr)] gap-6 sm:grid-cols-[140px_minmax(0,1fr)] relative z-10">
          <PetImage pet={pet} iconSize={32} className="aspect-square rounded-2xl border border-brand-accent/30 shadow-xl" />

          <div className="min-w-0 self-center space-y-4">
            <div className="space-y-1.5">
              <div className="flex min-w-0 items-center gap-3">
                <h2 className="truncate text-2xl font-black text-white uppercase tracking-tighter drop-shadow-md">{pet.name}</h2>
                <Badge variant="primary" size="xs" className="px-2 py-0.5 rounded-md font-black tracking-widest animate-pulse border-none shadow-lg">
                    ACTIVE
                </Badge>
              </div>
              <p className="line-clamp-2 text-[11px] font-bold uppercase tracking-widest text-neutral-500 leading-relaxed max-w-sm">
                {pet.desc || pet.ability || 'AUTHORIZED SYSTEM COMPANION ACTIVE.'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-4 border-t border-white/[0.05] pt-4 sm:grid-cols-4">
              <InlineStat icon={Heart} label="VITALITY" value={pet.hp ?? 0} tone="success" />
              <InlineStat icon={Swords} label="STRIKE" value={pet.atk ?? 0} tone="danger" />
              <InlineStat icon={Wind} label="VELOCITY" value={pet.spd ?? 0} tone="accent" />
              <InlineStat icon={Sparkles} label="LUCK_RATE" value={`${Math.round(Number(pet.luck || 0) * 100)}%`} tone="accent" />
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Badge variant="tactical" size="xs" className="font-mono bg-black text-brand-accent border-brand-accent/20">LVL {pet.level || 1}</Badge>
              <Badge variant="tactical" size="xs" className="font-mono opacity-60">SYNC: {pet.affection ?? 0}%</Badge>
              <Badge variant="tactical" size="xs" className="font-mono opacity-60 uppercase">{pet.mood || 'STABLE'}</Badge>
            </div>

            <div className="max-w-[280px]">
              <ProgressBar current={pet.xp || 0} total={Math.max(1, pet.xp_needed || 100)} label="BOND SYNCHRONIZATION" compact variant="default" />
            </div>
          </div>
        </div>
    </Card>
  </motion.div>
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
  <Card
    variant="tactical"
    className={cn(
      'p-4 transition-all duration-500 border-white/[0.03] group relative',
      isActive ? 'border-brand-accent/30 bg-brand-accent/[0.02]' : 'bg-white/[0.01] hover:bg-white/[0.02] hover:border-white/[0.1]'
    )}
  >
    <button
      type="button"
      onClick={() => onOpen?.(pet)}
      className="grid w-full grid-cols-[64px_minmax(0,1fr)] gap-4 text-left"
    >
      <PetImage pet={pet} iconSize={20} className="aspect-square rounded-xl border border-white/10 group-hover:border-brand-accent/30 transition-colors shadow-lg" />

      <div className="min-w-0 py-1 space-y-1.5">
        <div className="flex min-w-0 items-center gap-2">
          <h3 className="truncate text-[15px] font-black text-white uppercase tracking-tight group-hover:text-brand-accent transition-colors">{pet.name}</h3>
          {isActive && <div className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]" />}
        </div>
        <div className="flex items-center gap-2">
            <Zap size={10} className="text-brand-accent" />
            <p className="truncate text-[10px] font-black text-neutral-500 uppercase tracking-widest">{pet.ability || 'NO_SPECIAL_PERKS'}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-[8px] font-black uppercase tracking-tighter text-neutral-700 pt-1">
          <span className="font-mono text-neutral-500">LVL {pet.level || 1}</span>
          <span className="text-neutral-800">•</span>
          <span>BOND {pet.affection ?? 0}%</span>
        </div>
      </div>
    </button>

    <div className="mt-4 grid grid-cols-4 gap-3 border-t border-white/[0.03] pt-4">
      <InlineStat icon={Heart} label="HP" value={pet.hp ?? 0} />
      <InlineStat icon={Swords} label="ATK" value={pet.atk ?? 0} tone="danger" />
      <InlineStat icon={Wind} label="SPD" value={pet.spd ?? 0} />
      <InlineStat icon={Sparkles} label="LCK" value={`${Math.round(Number(pet.luck || 0) * 100)}%`} />
    </div>

    <div className="mt-4">
        <Button
          onClick={(e) => {
            e.stopPropagation();
            onActivate(pet);
          }}
          disabled={isActive || switching}
          variant={isActive ? "tactical" : "secondary"}
          className={cn(
            'h-10 w-full rounded-xl text-[10px] font-black uppercase tracking-[0.2em] shadow-lg',
            isActive ? "opacity-100" : "border-white/5 active:scale-95"
          )}
        >
          {switching ? <Loader2 size={16} className="animate-spin" /> : isActive ? <CheckCircle2 size={16} strokeWidth={2.5} className="mr-2" /> : <PawPrint size={16} className="mr-2" />}
          <span>{isActive ? 'ACTIVE' : 'AUTHORIZE SYNC'}</span>
        </Button>
    </div>
  </Card>
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
      addToast(`Sync authorized: ${pet.name} is now active.`, 'success');
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
    <div className="pb-32 pt-8 max-w-5xl mx-auto adaptive-px space-y-10 select-none">
      <header className="space-y-8">
        <div className="flex items-start justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                    <PawPrint className="text-brand-accent" size={26} />
               </div>
               <div className="flex flex-col gap-1">
                  <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Companions</h1>
                  <div className="flex items-center gap-2">
                     <Target size={11} className="text-neutral-600" />
                     <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                       SYSTEM SUPPORT ASSET DATABASE
                     </p>
                  </div>
               </div>
            </div>
          </div>

          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={refreshing}
            className="w-12 h-12 p-0 rounded-2xl border-white/5 shadow-xl active:scale-95"
            aria-label="Refresh companions"
          >
            <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
          </Button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
              { icon: PawPrint, label: 'Secured', value: summary.total, variant: 'primary' },
              { icon: Heart, label: 'Avg Bond', value: `${summary.averageAffection}%`, variant: 'danger' },
              { icon: Swords, label: 'Net Power', value: formatNumber(summary.totalPower), variant: 'success' },
              { icon: Star, label: 'Prime Unit', value: summary.bestPet?.name || 'NONE', variant: 'default' },
          ].map((stat, i) => (
            <Card key={i} variant="tactical" className="p-4 border-white/[0.04] bg-white/[0.01]">
              <div className="flex items-center gap-2 mb-2">
                <stat.icon size={12} className={cn(
                    stat.variant === 'primary' ? 'text-brand-accent' :
                    stat.variant === 'danger' ? 'text-red-400' :
                    stat.variant === 'success' ? 'text-success' : 'text-neutral-600'
                )} />
                <span className="text-[9px] font-black text-neutral-600 uppercase tracking-widest leading-none">{stat.label}</span>
              </div>
              <p className="text-sm font-black text-white tabular-nums leading-none truncate uppercase font-mono">{stat.value}</p>
            </Card>
          ))}
        </div>
      </header>

      <div className="space-y-12">
        {currentPet && (
          <section className="space-y-5">
            <div className="flex items-center gap-2 px-1">
               <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">ACTIVE_ASSET_SYNC</h2>
               <div className="h-px flex-1 bg-white/[0.03]" />
            </div>
            <ActivePetCard pet={currentPet} onOpen={onPetClick} />
          </section>
        )}

        <section className="space-y-6">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
               <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">PERSONNEL_STORAGE</h2>
               <div className="h-1 w-1 rounded-full bg-neutral-800" />
            </div>
            <p className="text-[9px] font-black text-neutral-700 uppercase tracking-widest">ORDER_BY_LEVEL</p>
          </div>

          <AnimatePresence mode="popLayout">
          {sortedPets.length > 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            </motion.div>
          ) : (
            <div className="py-24">
                <EmptyState
                icon={PawPrint}
                title="Personnel Missing"
                message="Visit the recruitment center to acquire your first system companion."
                />
            </div>
          )}
          </AnimatePresence>
        </section>
      </div>

      <div className="flex items-center justify-center gap-3 opacity-20 py-4">
         <Sparkles size={12} className="text-brand-accent" />
         <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Companions Online</span>
      </div>
    </div>
  );
};
