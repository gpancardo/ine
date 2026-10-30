"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import BenchmarkTable from "@/components/BenchmarkTable";
import SidebarGemma from "@/components/SidebarGemma";
import type { Seccion } from "@/components/types";

const MapComponent = dynamic(() => import("@/components/MapComponent"), { ssr: false });

export default function Page() {
  const [sel, setSel] = useState<Seccion | null>(null);
  const [hl, setHl] = useState<string | null>(null);
  return (
    <main className="h-screen flex flex-col">
      <div className="flex flex-1 min-h-0">
        <div className="flex-1"><MapComponent onSelect={setSel} selectedId={sel?.seccion_id} /></div>
        {sel && <SidebarGemma s={sel} onClose={() => setSel(null)} highlighted={hl} onHighlight={setHl} />}
      </div>
      <div className="max-h-56 overflow-auto border-t border-zinc-800 p-3"><BenchmarkTable /></div>
    </main>
  );
}
