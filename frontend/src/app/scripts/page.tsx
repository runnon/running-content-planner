"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import ScriptForge from "@/components/ScriptForge";

function ScriptForgeContent() {
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic") || "";
  const raceId = searchParams.get("race_id")
    ? Number(searchParams.get("race_id"))
    : undefined;

  return (
    <ScriptForge initialTopic={topic} initialRaceId={raceId} />
  );
}

export default function ScriptForgePage() {
  return (
    <Shell>
      <Suspense
        fallback={
          <div className="flex justify-center py-16">
            <div className="w-5 h-5 border-2 border-foreground/20 border-t-foreground rounded-full animate-spin" />
          </div>
        }
      >
        <ScriptForgeContent />
      </Suspense>
    </Shell>
  );
}
