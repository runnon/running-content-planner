"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import Shell from "@/components/Shell";
import {
  deleteRace,
  listRaces,
  researchMore,
  scrapeRaceImages,
  toggleCovered,
  updateRaceQueue,
} from "@/lib/api";

interface Race {
  id: number;
  name: string;
  location: string;
  origin_year: string;
  status: string;
  covered: boolean;
  queued_for_weekly: boolean;
}

export default function VaultPage() {
  const [races, setRaces] = useState<Race[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [researchingIds, setResearchingIds] = useState<Set<number>>(new Set());

  const loadRaces = useCallback(async () => {
    try {
      const data = await listRaces();
      setRaces(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRaces();
  }, [loadRaces]);

  const handleDelete = async (id: number) => {
    try {
      await deleteRace(id);
      await loadRaces();
    } catch (e) {
      console.error(e);
    }
  };

  const handleResearchMore = async (id: number) => {
    if (researchingIds.has(id)) return;
    setResearchingIds((prev) => new Set(prev).add(id));
    try {
      await Promise.all([researchMore(id), scrapeRaceImages(id)]);
      await loadRaces();
    } catch (e) {
      console.error(e);
    } finally {
      setResearchingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleToggleQueue = async (id: number, queued: boolean) => {
    try {
      await updateRaceQueue(id, !queued);
      await loadRaces();
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleCovered = async (id: number) => {
    try {
      const result = await toggleCovered(id);
      setRaces((prev) =>
        prev.map((race) => (race.id === id ? { ...race, covered: result.covered } : race))
      );
    } catch (e) {
      console.error(e);
    }
  };

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredRaces = races.filter((race) => {
    if (!normalizedQuery) return true;

    return [race.name, race.location, race.origin_year, race.status]
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuery);
  });

  return (
    <Shell>
      <div className="space-y-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="text-accent">The</span> <span className="text-accent">Vault</span>
            </h1>
            <p className="text-sm text-muted mt-1">
              {filteredRaces.length === races.length
                ? `${races.length} races saved`
                : `${filteredRaces.length} of ${races.length} races shown`}
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <div className="flex items-center gap-2">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search saved races..."
                className="text-sm"
              />
              {searchQuery.trim() && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="btn-secondary text-sm"
                >
                  Clear
                </button>
              )}
            </div>
            <Link
              href="/discover"
              className="btn-secondary text-sm"
            >
              Discover New
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-5 h-5 border-2 border-foreground/20 border-t-foreground rounded-full animate-spin" />
          </div>
        ) : filteredRaces.length === 0 ? (
          <div className="card py-10 text-center space-y-2">
            <p className="text-sm font-medium">No saved races match that search.</p>
            <p className="text-xs text-muted">
              This search only looks through your vault. Use the Discover tab to find races that are not already saved.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRaces.map((race) => (
              <div key={race.id} className="card space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <Link
                    href={`/scripts?race_id=${race.id}&topic=${encodeURIComponent(race.name)}`}
                    className="block min-w-0 flex-1"
                  >
                    <div>
                      <span className="font-semibold text-sm hover:text-accent transition-colors">
                        {race.name}
                      </span>
                      <p className="text-xs text-muted mt-0.5">
                        {race.location} · {race.origin_year}
                      </p>
                      <p className="text-xs text-muted mt-3">{race.status}</p>
                    </div>
                  </Link>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleToggleCovered(race.id)}
                      className={`w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${
                        race.covered
                          ? "border-green-500 bg-green-500/20 text-green-500"
                          : "border-border hover:border-muted text-transparent hover:text-muted/30"
                      }`}
                      title={race.covered ? "Covered in a video" : "Mark as covered"}
                      aria-label={race.covered ? "Covered in a video" : "Mark as covered"}
                    >
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 7.5L6 10.5L11 4" />
                      </svg>
                    </button>
                    {race.queued_for_weekly && (
                      <span className="tag-accent text-[10px]">Queued</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 items-center">
                  <button
                    onClick={() => handleResearchMore(race.id)}
                    disabled={researchingIds.has(race.id)}
                    className="text-[10px] text-accent hover:text-accent/80 transition-colors disabled:opacity-50"
                  >
                    {researchingIds.has(race.id) ? (
                      <span className="flex items-center gap-1">
                        <span className="w-2.5 h-2.5 border border-accent border-t-transparent rounded-full animate-spin" />
                        Researching...
                      </span>
                    ) : (
                      "Research"
                    )}
                  </button>
                  <button
                    onClick={() => handleToggleQueue(race.id, race.queued_for_weekly)}
                    className="text-[10px] text-muted hover:text-foreground transition-colors"
                  >
                    {race.queued_for_weekly ? "Unqueue" : "Queue"}
                  </button>
                  <button
                    onClick={() => handleDelete(race.id)}
                    className="text-[10px] text-danger hover:text-danger/80 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </Shell>
  );
}
