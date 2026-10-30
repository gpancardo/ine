"use client";
import { useEffect, useState } from "react";
import { MapContainer, GeoJSON, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection } from "geojson";
import { COLORS, type Seccion } from "./types";

type Mode = "inercial" | "mitigado" | "delta";
const MODES: [Mode, string][] = [["inercial", "Inercial (sin intervención)"], ["mitigado", "Mitigación (con política)"], ["delta", "Impacto Δ"]];
const cat = (v: number) => (v < 35 ? "Bajo" : v < 45 ? "Medio" : v < 55 ? "Alto" : "Crítico");
const deltaColor = (d: number) => (d > 1 ? "#22c55e" : d > 0.5 ? "#86efac" : d > 0.2 ? "#bbf7d0" : "#374151");

function Fit({ data }: { data: FeatureCollection }) {
  const map = useMap();
  useEffect(() => { import("leaflet").then(L => map.fitBounds(L.geoJSON(data).getBounds())); }, [data, map]);
  return null;
}

export default function MapComponent({ onSelect, selectedId }: { onSelect: (s: Seccion) => void; selectedId?: number }) {
  const [data, setData] = useState<FeatureCollection | null>(null);
  const [mode, setMode] = useState<Mode>("inercial");
  useEffect(() => { fetch("/secciones_reto2.geojson").then(r => r.json()).then(setData); }, []);

  const color = (p: Seccion) =>
    mode === "delta" ? deltaColor(p.diferencia_impacto)
      : COLORS[cat(mode === "inercial" ? p.prediccion_2027_inercial : p.prediccion_2027_mitigado)];

  if (!data) return <div className="p-4">Cargando…</div>;
  return (
    <div className="relative h-full">
      <div className="absolute right-3 top-3 z-[1000] flex gap-1 rounded bg-zinc-900/90 p-1 text-xs">
        {MODES.map(([m, label]) => (
          <button key={m} onClick={() => setMode(m)}
            className={`rounded px-2 py-1 ${mode === m ? "bg-sky-600 text-white" : "text-zinc-300"}`}>{label}</button>))}
      </div>
      <MapContainer center={[0, 0]} zoom={5} className="h-full w-full" style={{ background: "#0b0f14" }}>
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution="© OSM © CARTO" />
        <Fit data={data} />
        {/* key fuerza re-estilizado al cambiar de modo/selección */}
        <GeoJSON key={mode + selectedId} data={data}
          style={(f?: Feature) => {
            const p = f!.properties as Seccion;
            return { fillColor: color(p), fillOpacity: 0.75, color: p.seccion_id === selectedId ? "#fff" : "#111", weight: p.seccion_id === selectedId ? 3 : 0.5 };
          }}
          onEachFeature={(f, layer) => layer.on("click", () => onSelect(f.properties as Seccion))} />
      </MapContainer>
    </div>
  );
}
