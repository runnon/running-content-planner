"use client";

import { useState, useEffect, useCallback } from "react";
import { generateScript, listScripts, listRaces, getRace, toggleCovered } from "@/lib/api";

interface ScriptData {
  id: number;
  race_id: number | null;
  script_type: string;
  target_duration?: string | null;
  tone: string;
  topic: string;
  hooks: string[];
  body: string;
  visual_notes: string;
  cta: string;
  hashtags: string;
  caption: string;
  created_at: string;
}

interface RaceOption {
  id: number;
  name: string;
  location: string;
  origin_year: string;
  status: string;
  covered: boolean;
}

interface RaceDetail {
  id: number;
  name: string;
  location: string;
  origin_year: string;
  origin_story: string;
  what_makes_it_wild: string;
  status: string;
  last_known_date: string;
  next_upcoming_date: string;
  notable_moments: string;
  source_links: string[];
  video_angle: string;
}

const SCRIPT_TYPE = "race_history" as const;

const DURATION_OPTIONS = [
  { value: "30", label: "~30 sec", hint: "One sharp beat" },
  { value: "45", label: "~45 sec", hint: "Tight story" },
  { value: "60_90", label: "~60\u201390 sec", hint: "Weekly default" },
];

const TONES = [
  { value: "full_send", label: "Dirtbag" },
  { value: "real_talk", label: "Normal Speak" },
  { value: "history_lesson", label: "History Lesson" },
];

interface ScriptForgeProps {
  initialTopic?: string;
  initialRaceId?: number;
  lockedRaceId?: number;
  compact?: boolean;
}

export default function ScriptForge({
  initialTopic = "",
  initialRaceId,
  lockedRaceId,
  compact = false,
}: ScriptForgeProps) {
  const effectiveRaceId = lockedRaceId ?? initialRaceId;

  const [races, setRaces] = useState<RaceOption[]>([]);
  const [raceDetail, setRaceDetail] = useState<RaceDetail | null>(null);
  const [selectedScript, setSelectedScript] = useState<ScriptData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const [topic, setTopic] = useState(initialTopic);
  const [targetDuration, setTargetDuration] = useState("60_90");
  const [tone, setTone] = useState("full_send");
  const [raceId, setRaceId] = useState<number | undefined>(effectiveRaceId);

  const loadRaces = useCallback(async () => {
    if (lockedRaceId) return;
    try {
      const data = await listRaces();
      setRaces(data);
    } catch (e) {
      console.error(e);
    }
  }, [lockedRaceId]);

  useEffect(() => {
    loadRaces();
  }, [loadRaces]);

  useEffect(() => {
    if (!raceId || lockedRaceId) {
      setRaceDetail(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await getRace(raceId);
        if (!cancelled) setRaceDetail(data);
      } catch (e) {
        console.error(e);
        if (!cancelled) setRaceDetail(null);
      }
    })();
    return () => { cancelled = true; };
  }, [raceId, lockedRaceId]);

  const handleRaceSelect = (race: RaceOption) => {
    setRaceId(race.id);
    setTopic(race.name);
  };

  const handleToggleCovered = async (e: React.MouseEvent, race: RaceOption) => {
    e.stopPropagation();
    try {
      const result = await toggleCovered(race.id);
      setRaces((prev) =>
        prev.map((r) => (r.id === race.id ? { ...r, covered: result.covered } : r))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerate = async () => {
    if (!topic.trim() || !raceId) return;
    setGenerating(true);
    setError("");
    try {
      const result = await generateScript({
        topic: topic.trim(),
        script_type: SCRIPT_TYPE,
        target_duration: targetDuration,
        tone,
        race_id: raceId,
      });
      setSelectedScript(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Generation failed";
      setError(msg);
    } finally {
      setGenerating(false);
    }
  };

  const display = selectedScript;

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredRaces = races.filter((race) => {
    if (!normalizedQuery) return true;
    return [race.name, race.location, race.origin_year, race.status]
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuery);
  });

  // Compact mode for embedded use (e.g. /races/[id] page)
  if (compact) {
    return (
      <div className="space-y-6">
        <div className="card space-y-5">
          <div>
            <label className="block text-xs font-medium text-muted mb-2">Topic</label>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="What's this script about?"
              rows={2}
              className="w-full resize-none"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted mb-2">Type</label>
            <div className="px-3 py-2.5 rounded-xl border border-border bg-background/50 text-sm font-medium">
              Race history
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted mb-2">Length</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {DURATION_OPTIONS.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setTargetDuration(d.value)}
                  className={`p-2 rounded-xl border text-left transition-all ${
                    targetDuration === d.value
                      ? "border-accent bg-accent/5"
                      : "border-border hover:border-muted/30"
                  }`}
                >
                  <span className="block text-xs font-medium">{d.label}</span>
                  <span className="block text-[10px] text-muted leading-tight">{d.hint}</span>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted mb-2">Tone</label>
            <div className="flex gap-2">
              {TONES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTone(t.value)}
                  className={`flex-1 py-2 rounded-full border text-xs font-medium transition-all ${
                    tone === t.value
                      ? "border-accent bg-accent/5 text-accent"
                      : "border-border text-muted hover:border-muted/30"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
          {error && <p className="text-xs text-danger">{error}</p>}
          <button
            onClick={handleGenerate}
            disabled={generating || !topic.trim()}
            className="btn-primary w-full"
          >
            {generating ? (
              <>
                <span className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
                Forging...
              </>
            ) : (
              "Generate Script"
            )}
          </button>
        </div>

        {display && <ScriptOutput script={display} />}
        {!display && (
          <div className="card flex items-center justify-center h-48">
            <p className="text-muted">Fill in the details and hit Generate</p>
          </div>
        )}
      </div>
    );
  }

  // Full-page layout: scrolling race cards left, generator + output right
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Left — Race browser */}
      <div className="space-y-4">
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search for a race..."
          className="w-full text-sm"
        />

        <div className="space-y-3 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1">
          {filteredRaces.length === 0 ? (
            <div className="card py-10 text-center">
              <p className="text-sm text-muted">No races match that search.</p>
            </div>
          ) : (
            filteredRaces.map((race) => (
              <button
                key={race.id}
                onClick={() => handleRaceSelect(race)}
                className={`w-full text-left card !p-4 relative transition-all ${
                  raceId === race.id ? "!border-accent bg-accent/5" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-sm">{race.name}</h3>
                    <p className="text-xs text-muted mt-0.5">
                      {race.location || "Unknown"} &middot; {race.origin_year || "??"}
                    </p>
                    <p className="text-xs text-muted mt-1">{race.status}</p>
                  </div>

                  {/* Covered checkmark circle */}
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={(e) => handleToggleCovered(e, race)}
                    onKeyDown={(e) => { if (e.key === "Enter") handleToggleCovered(e as unknown as React.MouseEvent, race); }}
                    className={`shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all cursor-pointer ${
                      race.covered
                        ? "border-green-500 bg-green-500/20 text-green-500"
                        : "border-border hover:border-muted text-transparent hover:text-muted/30"
                    }`}
                    title={race.covered ? "Covered in a video" : "Mark as covered"}
                  >
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 7.5L6 10.5L11 4" />
                    </svg>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right — Generator controls + output */}
      <div className="space-y-6">
        <div className="card space-y-5">
          <div>
            <label className="block text-xs font-medium text-muted mb-2">Topic</label>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="What's this script about?"
              rows={2}
              className="w-full resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-muted mb-2">Type</label>
            <div className="px-3 py-2.5 rounded-xl border border-border bg-background/50 text-sm font-medium">
              Race history
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-muted mb-2">Length</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {DURATION_OPTIONS.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setTargetDuration(d.value)}
                  className={`p-2 rounded-xl border text-left transition-all ${
                    targetDuration === d.value
                      ? "border-accent bg-accent/5"
                      : "border-border hover:border-muted/30"
                  }`}
                >
                  <span className="block text-xs font-medium">{d.label}</span>
                  <span className="block text-[10px] text-muted leading-tight">{d.hint}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-muted mb-2">Tone</label>
            <div className="flex gap-2">
              {TONES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTone(t.value)}
                  className={`flex-1 py-2 rounded-full border text-xs font-medium transition-all ${
                    tone === t.value
                      ? "border-accent bg-accent/5 text-accent"
                      : "border-border text-muted hover:border-muted/30"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-xs text-danger">{error}</p>}

          <button
            onClick={handleGenerate}
            disabled={generating || !topic.trim() || !raceId}
            className="btn-primary w-full"
          >
            {generating ? (
              <>
                <span className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
                Forging...
              </>
            ) : (
              "Generate Script"
            )}
          </button>
        </div>

        {display ? (
          <ScriptOutput script={display} />
        ) : (
          <div className="card flex items-center justify-center h-48">
            <p className="text-muted">
              {raceId
                ? "Fill in the details and hit Generate"
                : "Pick a race to get started"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function ScriptOutput({ script }: { script: ScriptData }) {
  return (
    <div className="card space-y-6">
      {script.hooks && script.hooks.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-accent mb-3">Hook Options</h3>
          <div className="space-y-2">
            {script.hooks.map((hook, i) => (
              <div key={i} className="p-4 bg-background rounded-xl border border-border">
                <span className="text-xs text-accent font-mono mr-2">#{i + 1}</span>
                <span className="text-sm">{hook}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {script.body && (
        <div>
          <h3 className="text-sm font-semibold text-accent mb-3">Script</h3>
          <div className="p-5 bg-background rounded-xl border border-border">
            <p className="text-sm whitespace-pre-wrap font-mono leading-relaxed">
              {script.body}
            </p>
          </div>
        </div>
      )}

      {script.visual_notes && (
        <div>
          <h3 className="text-sm font-semibold text-accent mb-2">Visual Notes</h3>
          <p className="text-sm text-foreground/70 leading-relaxed whitespace-pre-wrap">
            {script.visual_notes}
          </p>
        </div>
      )}

      {script.cta && (
        <div>
          <h3 className="text-sm font-semibold text-accent mb-2">CTA</h3>
          <p className="text-sm">{script.cta}</p>
        </div>
      )}

      {script.caption && (
        <div>
          <h3 className="text-sm font-semibold text-accent mb-2">Caption</h3>
          <div className="p-4 bg-background rounded-xl border border-border">
            <p className="text-sm whitespace-pre-wrap">{script.caption}</p>
          </div>
        </div>
      )}

      {script.hashtags && (
        <div>
          <h3 className="text-sm font-semibold text-accent mb-2">Hashtags</h3>
          <p className="text-sm text-muted">{script.hashtags}</p>
        </div>
      )}
    </div>
  );
}
