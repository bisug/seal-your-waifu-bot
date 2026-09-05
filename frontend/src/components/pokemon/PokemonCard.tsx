import { Star } from 'lucide-react';
import React, { memo } from 'react';
import type { Pokemon } from '../../context/UserContext';
import { cn, FALLBACK_IMAGE } from '../../utils';

interface PokemonCardProps {
  pokemon: Pokemon;
  onClick?: (pokemon: Pokemon) => void;
  compact?: boolean;
}

const TYPE_EMOJI: Record<string, string> = {
  normal: '⭐', fire: '🔥', water: '💧', electric: '⚡', grass: '🌿',
  ice: '❄️', fighting: '🥊', poison: '☠️', ground: '⛰️', flying: '🕊️',
  psychic: '🔮', bug: '🐛', rock: '🪨', ghost: '👻', dragon: '🐉',
  dark: '🌑', steel: '⚙️', fairy: '🧚',
};

/**
 * raw.githubusercontent.com is slow (7-13s per PNG). jsDelivr serves the
 * same files from its CDN in ~0.2s — rewrite at render time so old
 * catalog URLs still load fast without a data migration.
 */
export const cdnUrl = (url?: string | null): string => {
  if (!url) return '';
  return url.replace(
    'https://raw.githubusercontent.com/PokeAPI/sprites/master/',
    'https://cdn.jsdelivr.net/gh/PokeAPI/sprites@master/',
  );
};

export const PokemonCard = memo(({ pokemon, onClick, compact }: PokemonCardProps) => {
  const [imgError, setImgError] = React.useState(false);
  const [loaded, setLoaded] = React.useState(false);
  React.useEffect(() => {
    setImgError(false);
    setLoaded(false);
  }, [pokemon.img]);

  return (
    <button
      type="button"
      onClick={() => {
        window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
        onClick?.(pokemon);
      }}
      className={cn(
        'relative rounded-md overflow-hidden group cursor-pointer select-none',
        'bg-zinc-950 border border-white/5 transition-all duration-200 active:scale-[0.98]',
        'hover:border-white/10 aspect-square',
      )}
    >
      {!imgError ? (
        <>
          {!loaded && (
            <div className="absolute inset-0 animate-pulse bg-zinc-900/80" aria-hidden="true" />
          )}
          <img
            src={cdnUrl(pokemon.img) || FALLBACK_IMAGE}
            alt={pokemon.name}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={() => setImgError(true)}
            className={cn(
              'absolute inset-0 w-full h-full object-contain p-2 transition-all duration-300',
              loaded ? 'opacity-100 group-hover:scale-105' : 'opacity-0',
              'bg-[radial-gradient(circle_at_50%_35%,rgba(120,120,140,0.12),transparent_70%)]',
            )}
          />
        </>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-zinc-700 text-3xl font-bold">
          #{pokemon.dex}
        </div>
      )}

      {pokemon.is_active && (
        <Star className="absolute top-1.5 right-1.5 w-4 h-4 text-amber-400 fill-amber-400 drop-shadow" />
      )}

      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-zinc-950 via-zinc-950/85 to-transparent px-2 pt-6 pb-1.5">
        <p className="text-[11px] font-semibold text-zinc-100 truncate">
          #{pokemon.dex} {pokemon.name}
        </p>
        {!compact && (
          <div className="flex items-center gap-1 mt-0.5 min-h-[16px]">
            {pokemon.level !== undefined && (
              <span className="text-[10px] text-zinc-400">Lv.{pokemon.level}</span>
            )}
            <span className="text-[10px]">
              {(pokemon.types ?? []).map((t) => TYPE_EMOJI[t] ?? '❔').join('')}
            </span>
          </div>
        )}
      </div>
    </button>
  );
});

PokemonCard.displayName = 'PokemonCard';
