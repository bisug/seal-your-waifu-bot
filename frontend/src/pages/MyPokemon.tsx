import { Sparkles, Star } from 'lucide-react';
import { useState } from 'react';
import { apiFetch, getErrorMessage } from '../api/client';
import { PokemonCard } from '../components/pokemon/PokemonCard';
import { PokemonDetailModal } from '../components/pokemon/PokemonDetailModal';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { useUser } from '../context/UserContext';

export const MyPokemon = () => {
  const { user, triggerRefresh } = useUser();
  const { addToast } = useToast();
  const [actionDex, setActionDex] = useState<number | null>(null);
  const [detailDex, setDetailDex] = useState<number | null>(null);

  const owned = user?.pokemon ?? [];
  const active = user?.current_pokemon ?? null;

  const handleSetActive = async (dex: number) => {
    setActionDex(dex);
    try {
      await apiFetch('/pokemon/set_active', {
        method: 'POST',
        body: JSON.stringify({ dex }),
      });
      addToast('Active Pokémon updated.', 'success');
      triggerRefresh();
    } catch (err) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setActionDex(null);
    }
  };

  if (!owned.length) {
    return (
      <EmptyState
        icon={Sparkles}
        title="No Pokémon yet"
        message="Catch a wild Pokémon in a group chat — guess its name before anyone else to claim it."
      />
    );
  }

  return (
    <div className="p-4 space-y-4">
      {active && (
        <Card className="p-4 flex items-center gap-4">
          <div className="w-16 h-16 rounded-md bg-zinc-900 border border-white/5 overflow-hidden shrink-0">
            <img src={active.img} alt={active.name} className="w-full h-full object-contain p-1" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-amber-400 fill-amber-400 shrink-0" />
              <p className="text-sm font-semibold text-zinc-100 truncate">
                {active.name}
              </p>
              <Badge variant="rare">Lv.{active.level}</Badge>
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              Active partner — fights in /battle and earns XP.
            </p>
          </div>
        </Card>
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-300">
          Collection <span className="text-zinc-600">({owned.length})</span>
        </h2>
      </div>

      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
        {owned.map((p) => (
          <div key={p.dex} className="space-y-1.5">
            <PokemonCard
              pokemon={p}
              onClick={(pk) => {
                if (pk.is_active) setDetailDex(pk.dex);
                else handleSetActive(pk.dex);
              }}
            />
            {!p.is_active && (
              <Button
                variant="outline"
                size="sm"
                className="w-full text-[10px]"
                disabled={actionDex === p.dex}
                onClick={() => handleSetActive(p.dex)}
              >
                {actionDex === p.dex ? 'Setting…' : 'Set Active'}
              </Button>
            )}
          </div>
        ))}
      </div>

      <PokemonDetailModal
        dex={detailDex}
        onClose={() => setDetailDex(null)}
        onSetActive={handleSetActive}
        settingDex={actionDex}
      />
    </div>
  );
};
