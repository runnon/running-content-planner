/**
 * Browser: empty base → same-origin `/api/...` (rewritten to FastAPI in next.config).
 * Override with NEXT_PUBLIC_API_URL when frontend and API are on different hosts.
 * Server (RSC, etc.): direct backend URL — rewrites do not apply server-side.
 */
function getApiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    return "";
  }
  return process.env.BACKEND_URL || "http://127.0.0.1:8000";
}

async function apiFetch(path: string, options?: RequestInit, timeoutMs = 120000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const base = getApiBase();
  const url = path.startsWith("http") ? path : `${base}${path}`;

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
    clearTimeout(timeout);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json();
  } catch (err: unknown) {
    clearTimeout(timeout);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out - the server is still processing. Try again.");
    }
    if (err instanceof TypeError && err.message === "Failed to fetch") {
      throw new Error(
        "Could not reach the API. Start the FastAPI backend (e.g. uvicorn on port 8000) " +
          "or set NEXT_PUBLIC_API_URL to your API base URL."
      );
    }
    throw err;
  }
}

export async function checkPassword(password: string) {
  return apiFetch("/api/auth/check", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export async function listRaces() {
  return apiFetch("/api/races");
}

export async function getRace(id: number) {
  return apiFetch(`/api/races/${id}`);
}

export async function researchRace(raceName: string) {
  return apiFetch("/api/races/research", {
    method: "POST",
    body: JSON.stringify({ race_name: raceName }),
  });
}

export async function discoverRaces() {
  return apiFetch("/api/races/discover", { method: "POST" });
}

export async function listDiscovered() {
  return apiFetch("/api/races/discovered/list");
}

export async function updateRaceQueue(raceId: number, queued: boolean) {
  return apiFetch(`/api/races/${raceId}`, {
    method: "PATCH",
    body: JSON.stringify({ queued_for_weekly: queued }),
  });
}

export async function toggleCovered(raceId: number) {
  return apiFetch(`/api/races/${raceId}/covered`, { method: "PATCH" });
}

export async function deleteRace(raceId: number) {
  return apiFetch(`/api/races/${raceId}`, { method: "DELETE" });
}

export async function researchMore(raceId: number) {
  return apiFetch(`/api/races/${raceId}/research-more`, { method: "POST" });
}

export async function addRaceSource(raceId: number, url: string) {
  return apiFetch(`/api/races/${raceId}/add-source`, {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function generateScript(params: {
  topic: string;
  script_type?: string;
  target_duration?: string;
  tone: string;
  race_id?: number;
}) {
  return apiFetch("/api/scripts/generate", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function listScripts(raceId?: number) {
  const params = raceId != null ? `?race_id=${raceId}` : "";
  return apiFetch(`/api/scripts${params}`);
}

export async function scrapeContent(params?: {
  hashtags?: string[];
  category?: string;
  max_per_hashtag?: number;
}) {
  return apiFetch("/api/content/scrape", {
    method: "POST",
    body: JSON.stringify(params || {}),
  });
}

export async function listContent(limit = 50, offset = 0) {
  return apiFetch(`/api/content?limit=${limit}&offset=${offset}`);
}

export async function listRaceImages(raceId: number) {
  return apiFetch(`/api/races/${raceId}/images`);
}

export async function scrapeRaceImages(raceId: number) {
  return apiFetch(`/api/races/${raceId}/images/scrape`, { method: "POST" });
}

export async function toggleStarImage(raceId: number, imageId: number) {
  return apiFetch(`/api/races/${raceId}/images/${imageId}/star`, { method: "PATCH" });
}

export async function deleteRaceImage(raceId: number, imageId: number) {
  return apiFetch(`/api/races/${raceId}/images/${imageId}`, { method: "DELETE" });
}
