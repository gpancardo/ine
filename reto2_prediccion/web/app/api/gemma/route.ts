// Gemma 4 vía endpoint compatible con OpenAI (Ollama/vLLM). Configurar GEMMA_URL y GEMMA_MODEL.
export async function POST(req: Request) {
  const s = await req.json();
  const prompt = `Eres analista electoral. Con estos datos de la sección ${s.seccion_id} (${s.municipio}):
${JSON.stringify(s)}
Responde en exactamente 3 viñetas en español: (1) diagnóstico del riesgo (${s.semaforo_riesgo}), (2) factores que lo explican, (3) recomendación táctica y efecto esperado de la mitigación (${s.diferencia_impacto} pp). No inventes datos.`;
  const url = process.env.GEMMA_URL;
  if (!url) return Response.json({ text: `⚠️ GEMMA_URL no configurada; prompt listo:\n\n${prompt}` });
  try {
    const r = await fetch(`${url}/v1/chat/completions`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: process.env.GEMMA_MODEL ?? "gemma4", messages: [{ role: "user", content: prompt }] }),
    });
    const j = await r.json();
    return Response.json({ text: j.choices[0].message.content });
  } catch (e) {
    return Response.json({ text: `Gemma no disponible: ${e}` });
  }
}
