"use client";

import { useCallback, useEffect, useState } from "react";

import Shell from "@/components/Shell";
import { discoverRaces, listDiscovered, researchRace } from "@/lib/api";

interface DiscoveredRace {
  id: number;
  name: string;
  snippet: string;
  source: string;
  source_url?: string;
}

export default function DiscoverPage() {
  const [discovered, setDiscovered] = useState<DiscoveredRace[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [savingDiscoveredIds, setSavingDiscoveredIds] = useState<Set<number>>(new Set());

  const loadDiscovered = useCallback(async () => {
    try {
      const data = await listDiscovered();
      setDiscovered(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDiscovered();
  }, [loadDiscovered]);

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      await discoverRaces();
      await loadDiscovered();
    } catch (e) {
      console.error(e);
    } finally {
      setDiscovering(false);
    }
  };

  const handleSaveDiscovered = async (race: DiscoveredRace) => {
    if (savingDiscoveredIds.has(race.id)) return;
    setSavingDiscoveredIds((prev) => new Set(prev).add(race.id));
    try {
      await researchRace(race.name);
      await loadDiscovered();
    } catch (e) {
      console.error(e);
    } finally {
      setSavingDiscoveredIds((prev) => {
        const next = new Set(prev);
        next.delete(race.id);
        return next;
      });
    }
  };

  return (
    <Shell>
      <div className="space-y-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Discover Races</h1>
            <p className="text-sm text-muted mt-1">
              Find races that are not already in the vault, then research and save the ones worth keeping.
            </p>
          </div>
          <button
            onClick={handleDiscover}
            disabled={discovering}
            className="btn-primary text-sm shrink-0"
          >
            {discovering ? "Discovering..." : "Scan for New Races"}
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-5 h-5 border-2 border-foreground/20 border-t-foreground rounded-full animate-spin" />
          </div>
        ) : discovered.length === 0 ? (
          <div className="card py-12 text-center space-y-3">
            <p className="text-sm font-medium">No discovery candidates yet.</p>
            <p className="text-xs text-muted">
              Run a discovery scan to pull in races that are not already saved in the vault.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {discovered.map((race) => (
              <div key={race.id} className="card space-y-3">
                <div className="space-y-1">
                  <p className="text-sm font-semibold">{race.name}</p>
                  <p className="text-[10px] uppercase tracking-[0.12em] text-muted">
                    {race.source || "Unknown source"}
                  </p>
                </div>
                <p className="text-sm text-foreground/80">
                  {race.snippet || "No snippet captured for this discovery candidate."}
                </p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleSaveDiscovered(race)}
                    disabled={savingDiscoveredIds.has(race.id)}
                    className="btn-secondary text-sm"
                  >
                    {savingDiscoveredIds.has(race.id) ? "Saving..." : "Research & Save"}
                  </button>
                  {race.source_url && (
                    <a
                      href={race.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-muted hover:text-foreground transition-colors"
                    >
                      View source
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
