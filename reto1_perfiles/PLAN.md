# Plan del Reto 1 (actualizado el 2026-10-12, tras leer la convocatoria)

Fuente: `convocatoria/Convocatoria_Hackaton.pdf` (texto en `convocatoria/convocatoria.txt`). **Regla de trabajo: no se producen entregables finales (documento técnico, fichas, presentación, .zip) hasta que se confirme la decisión de eje y se cierre el análisis.** Hoy solo hay análisis y plan.

## 1. Lo que fija la convocatoria
- **Un solo eje por equipo.** Entregar el Reto 1 implica no entregar el Reto 2.
- **Datos**: Plataforma CCPC 2009-2024; Reto 1 pide datos agregados, sin datos personales. La escolaridad es "cuando esté disponible" (la CCPC no la trae: se usa el censo como aproximación, declarado como tal).
- **Entregables generales obligatorios**: presentación ejecutiva (máximo 10 diapositivas); código o enlace a repositorio; carta de cesión de derechos firmada por todas las personas integrantes; carta declaratoria de decir verdad firmada por todas.
- **Entregables mínimos del Reto 1**: (a) documento técnico de 8 a 12 cuartillas (PDF, Arial/Calibri 11, interlineado 1.5) con la descripción de **4 a 6 perfiles claramente diferenciados**, la metodología de segmentación y las estrategias diferenciadas; (b) fichas de perfil (infografía o tablero; PDF/PNG de alta resolución) con el resumen narrativo e iconográfico de cada perfil.
- **Envío**: carpeta .zip con nombre del equipo y eje, por correo a las dos direcciones de la convocatoria, antes de las 23:59 del 31 de octubre. **Omitir cualquier entregable obligatorio descalifica.** Registro de equipos: hasta el 15 de octubre (un formulario por equipo, con la carta de cesión anexa).
- **Evaluación** (comité de cinco especialistas): apego a la temática (responde al reto y aprovecha la CCPC), claridad y solidez, originalidad y creatividad, viabilidad para el aprovechamiento institucional y potencial de aplicación institucional (ideas capaces de convertirse en proyectos reales del INE).

## 2. Decisión de eje: Reto 1 (recomendación)
Razones, ordenadas por peso en los criterios:
1. **Aprovecha lo que es único de la CCPC.** Su dimensión distintiva es la participación por sexo y edad dentro de cada sección. El Reto 1 la usa de lleno; el Reto 2 usaría sobre todo la participación agregada por sección, que también se obtiene de otras fuentes.
2. **Valor institucional mayor.** El Reto 1 produce información nueva y accionable ("campañas focalizadas y mensajes diferenciados"). El resultado honesto del Reto 2 (R² de 0.62 a 0.71, apenas por encima de repetir la elección anterior, con el error dominado por choques jurisdiccionales que no se anticipan) dice al INE sobre todo dónde ya se sabía que la participación es baja.
3. **El Reto 2 exige un escenario "con y sin intervención" que no podemos fundamentar.** No hay estimaciones de efecto de intervenciones en estos datos; el mapa sería un ejercicio de supuestos, lo que debilita la solidez. En el Reto 1 las estrategias son propuestas y no requieren cuantificar su efecto.
4. **Menor riesgo de descalificación.** El Reto 2 pide un archivo ejecutable de mapas o escenarios, una base anonimizada y un semáforo de riesgo; el Reto 1, un PDF y una infografía.
5. **Costo hundido, no argumento.** El trabajo del Reto 2 (rigor, bandas, hallazgos jurisdiccionales) ya está hecho, pero no puede entregarse; lo útil se aprovecha en el Reto 1 (prueba de persistencia, lección de que la intermitencia es nacional, no territorial).
- **Riesgos del Reto 1 que hay que cubrir**: la evaluación depende de la claridad de perfiles y estrategias (no de una métrica); "perfiles claramente diferenciados" choca con que los datos son un continuo (se defiende con ejes persistentes y medidas de separación); puede haber muchos equipos con K-means sobre edad y sexo (se compite con la validación temporal, el potencial en votos y el uso institucional).
- **Riesgo del Reto 2 si se cambiara**: competir contra equipos que reporten R² altos con validación aleatoria o filtración; nuestra ventaja sería el rigor, pero hay que explicar un resultado modesto a un comité de cinco personas.
- **Revisar la decisión solo si** las bases o la plataforma indicaran que un equipo puede presentar dos ejes (la convocatoria dice que no).

## 3. Cómo se traduce cada criterio en trabajo
| Criterio | Qué debe mostrarse | Trabajo pendiente |
|---|---|---|
| Apego a la temática | Responde "¿qué tipos de ciudadanía existen según su comportamiento de participación?"; usa edad, sexo, región e historial de la CCPC; escolaridad solo como aproximación declarada; menciona explícitamente los ejemplos del reto (jóvenes con alta participación, participación ocasional, comunidades de baja participación) | Mapear cada perfil a esos ejemplos; explicar con la prueba de persistencia por qué la participación "ocasional" es un fenómeno nacional y no un perfil territorial; segmentar solo con la CCPC y dejar los demás datos como complemento |
| Claridad y solidez | Pregunta, método, hallazgos y límites coherentes; cifras que cuadren con las tablas | Documento técnico conciso; medidas de diferenciación entre perfiles (E1b); validación temporal y por entidad; revisión cruzada de cifras (E9) |
| Originalidad y creatividad | Una mirada novedosa y un producto creativo y útil | Rasgos elegidos por persistencia (no por conveniencia); "votos recuperables" como medida de prioridad; segmentos para comunicar y pertenencias suaves para planear; reglas para clasificar cualquier sección; fichas iconográficas |
| Viabilidad institucional | Adaptable a acciones del INE sin costo ni datos personales | Uso concreto por Juntas Locales y Distritales y por la DECEyEC (tablas por distrito y municipio); actualización con cada publicación de la CCPC; código abierto; salvaguardas (neutralidad, celdas pequeñas, falacia ecológica) |
| Potencial de aplicación | Cómo se vuelve proyecto real | Piloto aleatorizado en las elecciones de 2027 con medición con la CCPC 2027; poder calculado con los datos (`potencia_piloto.py`: con 250 secciones por brazo, efecto mínimo detectable de 1.0 a 1.7 pp según el grupo); ruta de implementación por etapas |

## 4. Plan de trabajo ajustado (sin entregables)

**Estado al 2026-10-12 (cierre del análisis):** E1 hecho (no se adopta el perfil de 14 celdas como segmentación: R² 0.15-0.18 frente a 0.40 de los tres rasgos). E1b, E2/E3, E4, E6, E7 y E9 hechos (ver INFORME §9). **Actualización 2026-10-14:** E7 cerrado (cifras confirmadas en texto; se retiró una cita no localizable); E8 hecho (`reports/tablero.html`); voto por partido retirado de scripts e informe; revisión de calidad aplicada (INFORME §0, §3.3-3.4, §5, §6, §7, §9). Pendientes externos: registro y firmas (P0) y la producción de entregables (21-28 de octubre).
**Hoy a 14 de octubre**
- **P0**: registrar al equipo antes del 15 y reunir las firmas de las dos cartas (formatos en ine.mx/hackathon-2026). Definir el nombre del equipo (se usa para el .zip).
- **E1** (listo para correr): `comparar_algoritmos.py` con los segmentos sobre el perfil completo de 14 celdas; criterio fijado: adoptarlo solo si mejora en 0.03 el R² medio fuera de ventana y fuera de entidad y la estabilidad no baja de 0.65.
- **E1b**: medidas de **diferenciación** entre perfiles para defender "claramente diferenciados": varianza entre perfiles de cada eje (η²), distancia estandarizada entre perfiles vecinos, y qué proporción de secciones queda cerca de la frontera.
**15 a 20 de octubre (cierre del análisis)**
- **E2/E3**: rehacer la cadena si E1 cambia la solución; guardar pertenencias suaves (`tipologia_pertenencias.csv`).
- **E4**: descriptores del INEGI desagregados por sexo (ECEG, ya disponible) y verificación de la ENDUTIH y la ENCUCI (nivel estatal).
- **E5/E6**: causas de la brecha masculina (exploratorio) y cohortes (entrada a los 18 años).
- **E7**: evidencia de intervenciones para respaldar las estrategias (marcando el nivel de verificación).
- **E9**: calidad adicional (sin 2015, intervalos de los descriptores, revisión de cifras contra tablas).
- **Congelar el análisis el 20 de octubre.** Quitar de lo que se presenta el contexto político por partido y las comparaciones con el Reto 2.
**21 a 28 de octubre (producción)**: documento técnico (8 a 12 cuartillas exactas, con verificación del número de páginas), fichas de perfil, presentación de 10 diapositivas, paquete de código, instrucciones de reproducción y .zip de prueba.
**29 a 30 de octubre**: revisión con ojos frescos (cifras, formato, cartas firmadas, ortografía, neutralidad) y envío anticipado; **enviar el 30, no el 31 a las 23:59**.

## 5. Pendientes técnicos heredados (siguen válidos)
- **E8 tablero**: ya no es entregable obligatorio del Reto 1; se considera solo si sobra tiempo, como apoyo de las fichas.
- **Notas técnicas**: scripts desde la raíz con `uv run reto1_perfiles/analysis/<script>.py`; `comparar_algoritmos.py` fija `numpy<2` (por `py_pcha`); usar siempre ventanas de elecciones disjuntas entre rasgos de entrada y resultado.
- **Resultados que condicionan**: la intermitencia no persiste por territorio (r 0.28 en secciones, 0.07 en municipios); los datos forman un continuo y los cortes duros pierden cerca de la mitad de la información predictiva (R² 0.21 frente a 0.40); la hipótesis de emigración masculina no se sostiene con el censo.
