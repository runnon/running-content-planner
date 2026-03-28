"use client";

import { ReactNode } from "react";
import AuthGate from "./AuthGate";
import Nav from "./Nav";

export default function Shell({ children }: { children: ReactNode }) {
  return (
    <AuthGate>
      <Nav />
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
        {children}
      </main>
    </AuthGate>
  );
}
