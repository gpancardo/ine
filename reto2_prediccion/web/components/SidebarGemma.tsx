"use client";
import { useEffect, useState } from "react";
import { COLORS, type Seccion } from "./types";

export default function SidebarGemma({ s, onClose, highlighted, onHighlight }: {
  s: Seccion; onClose: () => void; highlighted: string | null; onHighlight: (a: string | null) => void;
}) {
  const [text, setText] = useState("Generando diagnóstico…");
  useEffect(() => {
    setText("Generando diagnóstico…");
    const { agebs_vinculadas, ...vars } = s; // el prompt se arma en /api/gemma
    fetch("/api/gemma", { method: "POST", body: JSON.stringify({ ...vars, n_agebs: agebs_vinculadas.length }) })
      .then(r => r.json()).then(d => setText(d.text)).catch(() => setText("Error al contactar a Gemma."));
  }, [s]);

  return (
    <aside className="w-96 overflow-y-auto border-l border-zinc-800 bg-zinc-950 p-4 text-sm">
      <button onClick={onClose} className="float-right text-zinc-400">✕</button>
      <h2 className="text-lg font-semibold">Sección {s.seccion_id}</h2>
      <p className="text-zinc-400">{s.municipio}</p>
      <span className="my-2 inline-block rounded px-2 py-0.5 text-black" style={{ background: COLORS[s.semaforo_riesgo] }}>{s.semaforo_riesgo}</span>
      <div className="grid grid-cols-3 gap-2 text-center">
        <Stat l="Real 2024" v={s.abstencion_real_2024} /><Stat l="Inercial 2027" v={s.prediccion_2027_inercial} />
        <Stat l="Mitigado 2027" v={s.prediccion_2027_mitigado} />
      </div>
      <p className="mt-1 text-emerald-400">Abstención evitada: {s.diferencia_impacto.toFixed(2)} pp</p>

      <h3 className="mt-4 font-semibold">Diagnóstico Gemma 4</h3>
      <div className="whitespace-pre-line rounded bg-zinc-900 p-3">{text}</div>

      <h3 className="mt-4 font-semibold">AGEBs INEGI vinculadas ({s.agebs_vinculadas.length})</h3>
      {s.agebs_vinculadas.map(a => (
        <div key={a.ageb} className={`mt-2 rounded border p-2 ${highlighted === a.ageb ? "border-sky-500" : "border-zinc-800"}`}>
          <div className="font-mono">{a.ageb}</div>
          <div className="text-zinc-400">Pob. {a.poblacion.toLocaleString()} · Marginación {a.marginacion}</div>
          <button className="mt-1 text-xs text-sky-400" onClick={() => onHighlight(highlighted === a.ageb ? null : a.ageb)}>
            {highlighted === a.ageb ? "Quitar resaltado" : "Resaltar"}</button>
        </div>))}
      {/* ponytail: el resaltado solo marca la tarjeta; sin polígonos AGEB en el GeoJSON no hay qué pintar en el mapa */}
    </aside>
  );
}
const Stat = ({ l, v }: { l: string; v: number }) => (
  <div className="rounded bg-zinc-900 p-2"><div className="text-xs text-zinc-400">{l}</div><div className="text-base">{v.toFixed(1)}%</div></div>);
