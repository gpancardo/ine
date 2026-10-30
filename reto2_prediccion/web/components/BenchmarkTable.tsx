"use client";
import { useEffect, useState } from "react";

type Row = { modelo: string; rmse: number; mae: number; r2: number; ganador: boolean };

// ponytail: tabla Tailwind plana, sin Shadcn (no aporta aquí). Añadir `shadcn add table` si se exige.
export default function BenchmarkTable() {
  const [rows, setRows] = useState<Row[]>([]);
  useEffect(() => { fetch("/benchmark_results.json").then(r => r.json()).then(setRows); }, []);
  return (
    <table className="w-full text-sm">
      <thead className="text-left text-zinc-400"><tr>
        <th>Modelo</th><th>RMSE</th><th>MAE</th><th>R²</th></tr></thead>
      <tbody>{rows.map(r => (
        <tr key={r.modelo} className={r.ganador ? "text-emerald-300" : ""}>
          <td>{r.modelo} {r.ganador && <span className="ml-1 rounded bg-emerald-600 px-1.5 text-xs text-white">GANADOR</span>}</td>
          <td>{r.rmse.toFixed(3)}</td><td>{r.mae.toFixed(3)}</td><td>{r.r2.toFixed(3)}</td>
        </tr>))}</tbody>
    </table>
  );
}
