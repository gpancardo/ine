export type Ageb = { ageb: string; poblacion: number; marginacion: string };
export type Seccion = {
  seccion_id: number; municipio: string; abstencion_real_2024: number;
  prediccion_2027_inercial: number; prediccion_2027_mitigado: number; diferencia_impacto: number;
  semaforo_riesgo: "Bajo" | "Medio" | "Alto" | "Crítico"; semaforo_mitigado: "Bajo" | "Medio" | "Alto" | "Crítico";
  escolaridad: number; pct_joven: number; marginacion: number; brecha_joven: number; dist_casilla: number; urbano: number;
  agebs_vinculadas: Ageb[];
};
export const COLORS = { Bajo: "#22c55e", Medio: "#eab308", Alto: "#f97316", Crítico: "#ef4444" } as const;
