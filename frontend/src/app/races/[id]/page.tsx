"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import ScriptForge from "@/components/ScriptForge";
import {
  getRace,
  updateRaceQueue,
  addRaceSource,
  researchMore,
  deleteRace,
  listRaceImages,
  scrapeRaceImages,
  toggleStarImage,
  deleteRaceImage,
} from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Race {
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
  queued_for_weekly: boolean;
  queue_date: string | null;
  raw_research: string;
  created_at: string;
}

interface RaceImage {
  id: number;
  race_id: number;
  source_url: string;
  local_url: string;
  filename: string;
  title: string;
  source_page: string;
  source_type: string;
  width: number | null;
  height: number | null;
  file_size: number | null;
  starred: boolean;
  created_at: string;
}

export default function RaceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const raceId = Number(params.id);

  const [race, setRace] = useState<Race | null>(null);
  const [loading, setLoading] = useState(true);
  const [sourceUrl, setSourceUrl] = useState("");
  const [addingSource, setAddingSource] = useState(false);
  const [researching, setResearching] = useState(false);
  const [activeTab, setActiveTab] = useState<"details" | "scripts" | "photos">("details");

  const [images, setImages] = useState<RaceImage[]>([]);
  const [scrapingImages, setScrapingImages] = useState(false);
  const [selectedImage, setSelectedImage] = useState<RaceImage | null>(null);
  const [imageFilter, setImageFilter] = useState<"all" | "starred" | "ddg" | "reddit" | "instagram" | "web">("all");

  const loadRace = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getRace(raceId);
      setRace(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [raceId]);

  useEffect(() => {
    loadRace();
  }, [loadRace]);

  const handleQueue = async () => {
    if (!race) return;
    try {
      await updateRaceQueue(race.id, !race.queued_for_weekly);
      setRace({ ...race, queued_for_weekly: !race.queued_for_weekly });
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async () => {
    if (!race || !confirm(`Remove "${race.name}" from the vault?`)) return;
    try {
      await deleteRace(race.id);
      router.push("/");
    } catch (e) {
      console.error(e);
    }
  };

  const handleResearchMore = async () => {
    if (!race) return;
    setResearching(true);
    try {
      await researchMore(race.id);
      await loadRace();
    } catch (e) {
      console.error(e);
    } finally {
      setResearching(false);
    }
  };

  const handleAddSource = async () => {
    if (!race || !sourceUrl.trim()) return;
    setAddingSource(true);
    try {
      await addRaceSource(race.id, sourceUrl.trim());
      setSourceUrl("");
      await loadRace();
    } catch (e) {
      console.error(e);
    } finally {
      setAddingSource(false);
    }
  };

  const loadImages = useCallback(async () => {
    try {
      const data = await listRaceImages(raceId);
      setImages(data);
    } catch (e) {
      console.error(e);
    }
  }, [raceId]);

  useEffect(() => {
    if (activeTab === "photos") {
      loadImages();
    }
  }, [activeTab, loadImages]);

  const handleFindPhotos = async () => {
    setScrapingImages(true);
    try {
      const result = await scrapeRaceImages(raceId);
      setImages(result.images || []);
    } catch (e) {
      console.error(e);
    } finally {
      setScrapingImages(false);
    }
  };

  const handleToggleStar = async (img: RaceImage) => {
    try {
      const updated = await toggleStarImage(raceId, img.id);
      setImages((prev) => prev.map((i) => (i.id === img.id ? updated : i)));
      if (selectedImage?.id === img.id) setSelectedImage(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteImage = async (img: RaceImage) => {
    if (!confirm("Remove this image?")) return;
    try {
      await deleteRaceImage(raceId, img.id);
      setImages((prev) => prev.filter((i) => i.id !== img.id));
      if (selectedImage?.id === img.id) setSelectedImage(null);
    } catch (e) {
      console.error(e);
    }
  };

  const filteredImages = images.filter((img) => {
    if (imageFilter === "all") return true;
    if (imageFilter === "starred") return img.starred;
    return img.source_type === imageFilter;
  });

  const formatBytes = (bytes: number | null) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  if (loading) {
    return (
      <Shell>
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      </Shell>
    );
  }

  if (!race) {
    return (
      <Shell>
        <div className="text-center py-12">
          <p className="text-muted mb-4">Race not found</p>
          <button
            onClick={() => router.push("/")}
            className="text-accent hover:underline text-sm"
          >
            Back to Race Vault
          </button>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <Link
              href="/"
              className="text-xs text-muted hover:text-accent transition-colors mb-2 inline-block"
            >
              &larr; Race Vault
            </Link>
            <h1 className="text-2xl font-bold">{race.name}</h1>
            <p className="text-sm text-muted">
              {race.location || "Location unknown"} · Est.{" "}
              {race.origin_year || "??"}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={handleResearchMore}
              disabled={researching}
              className="px-3 py-1.5 text-sm font-medium rounded-md border border-accent/30 text-accent hover:bg-accent/10 transition-colors disabled:opacity-50"
            >
              {researching ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                  Researching...
                </span>
              ) : (
                "Research More"
              )}
            </button>
            <button
              onClick={handleQueue}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                race.queued_for_weekly
                  ? "bg-accent text-background"
                  : "border border-accent/30 text-accent hover:bg-accent/10"
              }`}
            >
              {race.queued_for_weekly ? "Queued" : "Queue for Weekly"}
            </button>
            <button
              onClick={handleDelete}
              className="px-3 py-1.5 text-sm font-medium rounded-md border border-danger/30 text-danger hover:bg-danger/10 transition-colors"
            >
              Remove
            </button>
          </div>
        </div>

        {/* Status badges */}
        <div className="flex flex-wrap gap-2">
          <span className="inline-block text-xs bg-surface-hover px-2 py-1 rounded text-muted">
            {race.status || "Status unknown"}
          </span>
          {race.last_known_date && (
            <span className="inline-block text-xs bg-surface-hover px-2 py-1 rounded text-muted">
              Last held: {race.last_known_date}
            </span>
          )}
          {race.next_upcoming_date && race.next_upcoming_date !== "Unknown" && (
            <span className="inline-block text-xs bg-accent/20 px-2 py-1 rounded text-accent font-medium">
              Next: {race.next_upcoming_date}
            </span>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-border">
          <button
            onClick={() => setActiveTab("details")}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === "details"
                ? "border-accent text-accent"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            Race Details
          </button>
          <button
            onClick={() => setActiveTab("scripts")}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === "scripts"
                ? "border-accent text-accent"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            Script Forge
          </button>
          <button
            onClick={() => setActiveTab("photos")}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === "photos"
                ? "border-accent text-accent"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            Photos{images.length > 0 ? ` (${images.length})` : ""}
          </button>
        </div>

        {/* Tab content */}
        {activeTab === "details" && (
          <div className="space-y-5">
            {race.origin_story && (
              <div>
                <h3 className="text-sm font-semibold text-accent mb-1">
                  Origin Story
                </h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                  {race.origin_story}
                </p>
              </div>
            )}

            {race.what_makes_it_wild && (
              <div>
                <h3 className="text-sm font-semibold text-accent mb-1">
                  What Makes It Wild
                </h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                  {race.what_makes_it_wild}
                </p>
              </div>
            )}

            {race.notable_moments && (
              <div>
                <h3 className="text-sm font-semibold text-accent mb-1">
                  Notable Moments
                </h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                  {race.notable_moments}
                </p>
              </div>
            )}

            {race.video_angle && (
              <div>
                <h3 className="text-sm font-semibold text-accent mb-1">
                  Video Angle for Runnon
                </h3>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap">
                  {race.video_angle}
                </p>
              </div>
            )}

            {race.source_links && race.source_links.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-accent mb-1">
                  Sources
                </h3>
                <div className="space-y-1">
                  {race.source_links.map((link, i) => (
                    <a
                      key={i}
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-accent-dim hover:text-accent truncate"
                    >
                      {link}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Add source */}
            <div className="pt-3 border-t border-border">
              <p className="text-xs text-muted mb-2">
                Drop a URL to enrich this profile:
              </p>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://..."
                  className="flex-1 text-xs"
                />
                <button
                  onClick={handleAddSource}
                  disabled={addingSource || !sourceUrl.trim()}
                  className="px-3 py-1.5 text-xs bg-surface-hover border border-border text-foreground rounded-md hover:border-accent/30 disabled:opacity-50"
                >
                  {addingSource ? "Adding..." : "Add Source"}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "scripts" && (
          <ScriptForge
            initialTopic={race.name}
            lockedRaceId={race.id}
            compact
          />
        )}

        {activeTab === "photos" && (
          <div className="space-y-5">
            {/* Controls */}
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex gap-1.5 flex-wrap">
                {(["all", "starred", "ddg", "instagram", "reddit", "web"] as const).map((f) => {
                  const labels: Record<string, string> = {
                    all: "All",
                    starred: "Starred",
                    ddg: "Web Search",
                    instagram: "Instagram",
                    reddit: "Reddit",
                    web: "Page Scrape",
                  };
                  const count =
                    f === "all"
                      ? images.length
                      : f === "starred"
                        ? images.filter((i) => i.starred).length
                        : images.filter((i) => i.source_type === f).length;
                  return (
                    <button
                      key={f}
                      onClick={() => setImageFilter(f)}
                      className={`px-3 py-1 rounded-full text-xs transition-colors ${
                        imageFilter === f
                          ? "bg-foreground text-background font-medium"
                          : "text-muted hover:text-foreground bg-surface-hover"
                      }`}
                    >
                      {labels[f]}{count > 0 ? ` (${count})` : ""}
                    </button>
                  );
                })}
              </div>
              <button
                onClick={handleFindPhotos}
                disabled={scrapingImages}
                className="px-4 py-2 text-sm font-medium rounded-md bg-accent text-background hover:bg-accent/90 transition-colors disabled:opacity-50 shrink-0"
              >
                {scrapingImages ? (
                  <span className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 border-2 border-background border-t-transparent rounded-full animate-spin" />
                    Finding Photos...
                  </span>
                ) : (
                  "Find Photos"
                )}
              </button>
            </div>

            {scrapingImages && (
              <div className="card !border-accent/20 !bg-accent/5">
                <p className="text-sm text-accent">
                  Searching DuckDuckGo Images, Instagram, Reddit, and source pages for photos of {race.name}... This can take a minute.
                </p>
              </div>
            )}

            {/* Image grid */}
            {filteredImages.length === 0 && !scrapingImages ? (
              <div className="card flex flex-col items-center justify-center py-16 gap-3">
                <p className="text-muted text-sm">
                  {images.length === 0
                    ? "No photos yet. Hit \"Find Photos\" to scrape the web, Instagram, Reddit, and source pages."
                    : "No photos match this filter."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {filteredImages.map((img) => (
                  <div
                    key={img.id}
                    className={`group relative rounded-lg overflow-hidden border transition-all cursor-pointer ${
                      selectedImage?.id === img.id
                        ? "border-accent ring-2 ring-accent/30"
                        : "border-border hover:border-accent/40"
                    }`}
                    onClick={() => setSelectedImage(selectedImage?.id === img.id ? null : img)}
                  >
                    <div className="aspect-[4/3] bg-surface-hover">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={img.local_url ? `${API_BASE}${img.local_url}` : img.source_url}
                        alt={img.title || "Race photo"}
                        className="w-full h-full object-cover"
                        loading="lazy"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </div>

                    {/* Overlay controls */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="absolute bottom-0 left-0 right-0 p-2 flex items-end justify-between gap-1">
                        <span className="text-[10px] text-white/80 truncate flex-1">
                          {img.source_type === "ddg" ? "Web" : img.source_type === "reddit" ? "Reddit" : img.source_type === "instagram" ? "IG" : "Page"}
                          {img.file_size ? ` · ${formatBytes(img.file_size)}` : ""}
                          {img.width && img.height ? ` · ${img.width}x${img.height}` : ""}
                        </span>
                        <div className="flex gap-1 shrink-0">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleToggleStar(img); }}
                            className={`w-6 h-6 flex items-center justify-center rounded text-xs transition-colors ${
                              img.starred
                                ? "bg-yellow-500/90 text-black"
                                : "bg-black/50 text-white hover:bg-black/70"
                            }`}
                            title={img.starred ? "Unstar" : "Star"}
                          >
                            {img.starred ? "\u2605" : "\u2606"}
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDeleteImage(img); }}
                            className="w-6 h-6 flex items-center justify-center rounded bg-black/50 text-white hover:bg-red-600/80 text-xs transition-colors"
                            title="Remove"
                          >
                            &times;
                          </button>
                        </div>
                      </div>
                    </div>

                    {img.starred && (
                      <div className="absolute top-1.5 right-1.5 w-5 h-5 flex items-center justify-center rounded-full bg-yellow-500 text-black text-[10px]">
                        &#9733;
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Selected image detail */}
            {selectedImage && (
              <div className="card space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold truncate">
                      {selectedImage.title || "Untitled"}
                    </h3>
                    <p className="text-xs text-muted mt-0.5">
                      Source: {selectedImage.source_type === "ddg" ? "Web Search" : selectedImage.source_type === "reddit" ? "Reddit" : selectedImage.source_type === "instagram" ? "Instagram" : "Page Scrape"}
                      {selectedImage.width && selectedImage.height
                        ? ` · ${selectedImage.width} x ${selectedImage.height}`
                        : ""}
                      {selectedImage.file_size ? ` · ${formatBytes(selectedImage.file_size)}` : ""}
                    </p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <a
                      href={selectedImage.local_url ? `${API_BASE}${selectedImage.local_url}` : selectedImage.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="px-3 py-1.5 text-xs font-medium rounded-md bg-accent text-background hover:bg-accent/90 transition-colors"
                    >
                      Download
                    </a>
                    {selectedImage.source_page && (
                      <a
                        href={selectedImage.source_page}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 text-xs font-medium rounded-md border border-border text-muted hover:text-foreground hover:border-accent/30 transition-colors"
                      >
                        Source Page
                      </a>
                    )}
                    <button
                      onClick={() => handleToggleStar(selectedImage)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                        selectedImage.starred
                          ? "bg-yellow-500/20 text-yellow-600 border border-yellow-500/30"
                          : "border border-border text-muted hover:text-foreground"
                      }`}
                    >
                      {selectedImage.starred ? "Starred" : "Star"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Shell>
  );
}
