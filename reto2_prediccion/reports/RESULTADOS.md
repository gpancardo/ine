# Modelos, benchmark, ablación y validez

Todo reproducible: `download_data.py` → `download_extra.py` → `build_panel.py` → `analysis/eda.py` → `benchmark.py` → `ablation.py` → `rigor.py`; los análisis de §9-11 están indexados en `README.md`. Tablas fuente en `reports/*.csv`.

## 0. Resumen ejecutivo

1. **El R² de 0.82 no es alcanzable *ex ante* con estas fuentes, y no es un problema de limpieza ni de modelo.** El R² honesto (entrenar en elecciones pasadas, predecir la siguiente) es **0.62 (2021)** y **0.71 (2024)** sobre abstención relativa al nivel nacional. Con las mismas variables pero aprendiendo la relación *dentro del propio año* (CV por municipio) el R² es 0.78–0.79: ese es el techo estático. La diferencia es que cada elección tiene su propia dinámica y con 2–3 transiciones pasadas no se aprende.
2. **Casi toda la señal es historia electoral.** Quitar los rezagos sube el RMSE 0.009–0.020 (IC95% lejos de 0). Censo, edad, espacio, municipio, estructura, calidad y calendario de gubernaturas no mejoran, y en varios casos empeoran.
3. **El mejor modelo (Lasso/Ridge sobre rezagos "semánticos") es solo ~7% mejor que repetir la última elección presidencial en 2024 y no es distinguible de ella en 2021** (el análogo de 2027).
4. **El nivel nacional es la mayor incertidumbre**: error de ±2–5 pp en el backtest, mayor que el error por sección.
5. Mejoras reales logradas: (a) rezagos por **tipo de elección** (última presidencial / última intermedia) en vez de por posición: R² 2021 de 0.47 a 0.61; (b) **excluir 2015 como objetivo de entrenamiento**: +0.05 R² en 2021.

6. **Búsqueda de datos y causas adicionales (2026-10-11, §11).** Datos INEGI/INE/Magar nuevos, historia 1994-2024, clusters geográficos, calendario y competitividad municipal, y variables político-jurisdiccionales: ninguno mejora el R² honesto. El choque que limita el R² es jurisdiccional (municipio > estado) y cambia de tamaño y causa entre elecciones; con el choque estatal conocido el R² sería 0.72-0.78, con el distrital 0.80-0.81.

## 1. Limpieza: qué se probó, qué ayudó

| Decisión | Resultado |
|---|---|
| Abstención ajustada NV/(SV+NV) en vez de cruda | Adoptada: NS pasa de 0.2% (2012) a 6.8% (2018) |
| Excluir secciones con NS alto del *test* | Sin efecto (R² 0.611 vs 0.616) |
| Filtrar por estabilidad de lista nominal (cambios de sección) | Sin efecto: la correlación entre elecciones no mejora en secciones estables |
| Filtro LN ≥ 100 | Adoptado; LN≥0, 300 o 1000 cambia el R² ≤ 0.04 |
| Recortar outliers \|y\|≥0.40 | Sin efecto relevante |
| **Excluir 2015 como objetivo de entrenamiento** | **Ayuda**: R² 2021 0.561→0.616; 2024 0.699→0.711 |

**Por qué 2015.** Es la elección menos correlacionada con todas las demás, incluso entre municipios (corr. 2015↔2018 = 0.57; 2018↔2024 = 0.85) y con NS<2%. Los pesos de regresión lo delatan: el peso de la presidencial previa es 0.77–0.81 en 2018, 2021 y 2024, pero 0.41 en 2015. Causa no identificada (hipótesis, sin verificar: bloqueos y boicot electoral en estados del sur tras Ayotzinapa; cambios de captura). Lo trato como dato atípico, no como error comprobado.

## 2. Modelos propuestos

| Modelo | Por qué |
|---|---|
| Baselines: media nacional, última presidencial (P1), elección adyacente, media de historia | Piso mínimo; P1 resultó ser el rival serio |
| OLS sobre rezagos semánticos | Referencia lineal sin regularización |
| Lasso / Ridge | Pocas observaciones efectivas de "elección" (2–3): regularizar importa |
| Random Forest (100 árboles), LightGBM, CatBoost | No linealidades e interacciones censo × historia |
| Stacking (Ridge + LGBM + RF → Ridge) | Combinación estándar; ver advertencia de validez en §7 |

**Protocolo (rolling-origin, solo pasado).** Fold 2021: entrena con transición →2018, prueba 2021. Fold 2024: entrena →2018 y →2021, prueba 2024. Objetivo: abstención relativa `y = abst_T − media_nacional_T`. Los rezagos también son relativos a cada año. Métricas: RMSE, MAE, R² (sin ponderar, y ponderado por electores en `rigor_*.csv`).

## 3. Configuraciones de features (RMSE medio, Ridge y LightGBM, ambos folds)

| Config | RMSE medio |
|---|---|
| S2 sem + edad/sexo (elegida) | **0.0682** |
| S7 sem + calidad NS | 0.0683 |
| S1 sem (P1,M1,P2,M2,tipo) | 0.0684 |
| S8 sem + gubernaturas | 0.0688 |
| S9 sem + historia agregada | 0.0692 |
| S6 sem + estructura | 0.0693 |
| S5 sem + municipal | 0.0693 |
| S10 sem + todo (sin estado) | 0.0702 |
| S4 sem + espacial | 0.0703 |
| S11 sem + todo + estado | 0.0705 |
| S3 sem + censo | 0.0711 |
| S0 rezago posicional (a1,a2,Δ) | 0.0792 |
| S12 solo censo + estructura (sin historia) | 0.0980 |

Sin historia electoral el modelo es mucho peor (0.098); con ella, agregar grupos no ayuda. S1 y S2 son indistinguibles: la diferencia está dentro del ruido.

## 4. Benchmark (RMSE medio de ambos folds; IC95% por bootstrap de municipios en `rigor_ci.csv`)

| Modelo | RMSE 2021 | RMSE 2024 | R² 2021 | R² 2024 |
|---|---|---|---|---|
| **Lasso** | 0.0783 | 0.0562 | 0.617 | 0.712 |
| Ridge | 0.0784 | 0.0563 | 0.616 | 0.711 |
| Stacking | 0.0785 | 0.0567 | 0.615 | 0.707 |
| OLS sem | 0.0789 | 0.0568 | 0.611 | 0.705 |
| LightGBM | 0.0800 | 0.0580 | 0.600 | 0.693 |
| Baseline P1 (última presidencial) | 0.0779 | 0.0606 | 0.621 | 0.665 |
| Random Forest | 0.0808 | 0.0584 | 0.592 | 0.689 |
| CatBoost | 0.0817 | 0.0589 | 0.583 | 0.684 |
| Baseline elección adyacente | 0.0779 | 0.0855 | 0.621 | 0.334 |
| Baseline media nacional | 0.1265 | 0.1047 | 0.000 | −0.001 |

**Lectura con intervalos.** En 2024 todos los modelos superan a P1 de forma significativa (Δ RMSE de −0.002 a −0.004, IC95% sin 0). En 2021 ninguno lo supera: Ridge/Lasso/Stacking tienen Δ IC que incluye 0 y los modelos de árboles son significativamente peores (+0.002 a +0.004). El empate entre los seis modelos entrenados no es sospechoso: es lo que se espera cuando solo 4 variables de historia aportan información y todos las capturan.

## 5. Ablación (leave-one-group-out desde S10; IC95% por municipio en `ablation.csv`)

Δ RMSE al quitar el grupo (positivo = el grupo ayudaba):

| Grupo quitado | Ridge 2021 | Ridge 2024 | LGBM 2021 | LGBM 2024 |
|---|---|---|---|---|
| **historia (sem)** | **+0.0144** | **+0.0110** | **+0.0204** | **+0.0091** |
| censo | +0.0038 | −0.0007 | +0.0008 | −0.0009 |
| espacial | −0.0028 | +0.0002 | +0.0004 | −0.0003 |
| municipal | −0.0009 | −0.0003 | +0.0025 | −0.0018 |
| edad/sexo, estructura, calidad | \|Δ\| ≤ 0.0005 | \|Δ\| ≤ 0.0001 | \|Δ\| ≤ 0.0005 | \|Δ\| ≤ 0.0005 |

Dentro de la historia (Ridge): quitar **P1** (última presidencial) sube el RMSE 0.022 (2021) y 0.019 (2024); quitar M1 sube 0.003 y 0.001; P2/M2 y las interacciones de tipo aportan ~0. Es decir: **la última presidencial es casi toda la señal**. Limitación: en el fold 2021 el entrenamiento solo contiene un objetivo presidencial (2018), por lo que `is_mid` y sus interacciones son constantes (Δ exactamente 0) y el efecto del tipo de elección no se aprende ahí.

## 6. Por qué no se llega a 0.82 (diagnóstico)

Descomposición del R² relativo (`rigor_techo.csv`):

| Concepto | 2021 | 2024 |
|---|---|---|
| Modelo honesto (temporal) | 0.616 | 0.711 |
| Oráculo: pesos de rezago del propio año | 0.669 | 0.721 |
| **Estático**: LGBM, todas las features, mismo año, CV por municipio | **0.776** | **0.791** |
| Oráculo + media municipal del residuo en T **(fuga, no usable)** | 0.877 | 0.859 |
| Ruido binomial (varianza irreducible) | 0.019 | 0.027 |

- El ruido de medición **no** es el problema (2–3% de la varianza).
- Las features tienen poder explicativo (0.78–0.79) **si** se ajustan al año objetivo. Lo que no transfiere de una elección a otra es la forma de la relación. Con 2–3 transiciones previas no se puede aprender qué cambia.
- Un R² de 0.8+ en la literatura de participación por precinto/sección suele provenir de (i) predecir con la misma elección del año previo del mismo tipo, (ii) incluir resultados parciales del propio año o (iii) un panel con muchas elecciones. Aquí hay 6 elecciones, de tipos alternados y una (2015) atípica. (Referencias conceptuales —teoría de oleada y declive de Campbell, efecto de elecciones concurrentes y de competitividad— no fueron verificadas contra fuentes en esta sesión; citar solo tras revisarlas.)
- El residuo está **agrupado por municipio**: su media municipal predice 65% (2021) y 59% (2024) de su varianza. Es información de coyuntura local (competitividad de la elección municipal, conflictos) que no está en los censos. Es la vía de mejora más prometedora, pero requiere datos nuevos (resultados municipales de elecciones locales, margen de victoria), no limpieza.
- El calendario de gubernaturas **no ayudó** (S8 ≈ S1), así que ese efecto no explica los choques estatales.
- R² en valores **absolutos** (nivel nacional incluido): 0.62/0.71 con nivel oráculo; **0.43 (2021) y 0.65 (2024)** si el nivel nacional se predice por persistencia del mismo tipo. Agrupar años no lo infla a >0.8 (solo hay dos años de prueba).

## 7. Rigor y validez

| Prueba | Resultado |
|---|---|
| Placebo, etiquetas barajadas globalmente | R² = 0.008 (2021) y −0.007 (2024): sin fuga en el pipeline |
| Placebo, barajado dentro de municipio | R² 0.48 / 0.62: **la habilidad es sobre todo municipal**; la parte intra-municipal aporta ~0.14 / ~0.09 |
| Semillas (LGBM, CatBoost, 3 semillas) | sd del RMSE ≤ 0.0001: estable |
| Calibración (y ~ predicción) | pendiente 1.11 (2021), 0.94 (2024); intercepto ≈ 0 |
| Heterogeneidad | RMSE rural 0.096 vs urbano 0.069 (2021); peores estados 2021: TLAX 0.151, NAY, VER, HGO, TAB; 2024: GRO 0.098, CHIS, TLAX, OAX, TAB. Tlaxcala es el peor en ambos |
| Nivel nacional (media de secciones) | Error de 5.4 pp con persistencia mismo tipo en 2021 (1.8 con tendencia lineal) y −2.5 pp en 2024: **±3–5 pp** |
| Descomposición municipal/intra-municipal de los rezagos | Gana ≤0.01 de R²; no adoptada |

**Riesgos de validez, dichos con franqueza**
- **Grados de libertad del analista.** Elegí configuración, regularización de LGBM y la exclusión de 2015 mirando ambos folds. No existe un fold intacto. La estimación es optimista; las diferencias entre configuraciones adyacentes (<0.001) no deben interpretarse.
- **Stacking** usa CV aleatorio interno (`cv=3`) que puede filtrar información entre secciones de un mismo municipio al ajustar el meta-modelo; el efecto parece pequeño (Stacking ≈ Ridge) pero no se aisló.
- **Censo 2020 como covariable estática** también se usa para objetivos de 2018. No ayudó, por lo que no sesga el ranking.
- **Calendario de gubernaturas 2009–2018** compilado por el ciclo sexenal sin verificar contra el INE por estado (2021, 2024 y 2027 sí tienen respaldo). No mejoró los resultados.
- **Cartografía:** el marco es 2021 (68,806 polígonos) y 2024 tiene 70,751 secciones, así que parte de las secciones nuevas queda sin geometría; para 2027 el INE publica un marco nuevo el 12-nov-2026.
- Solo dos folds de prueba; los IC reflejan incertidumbre muestral entre municipios, **no** entre elecciones.

## 8. Qué haría el siguiente paso

1. Incorporar **información municipal ex ante** (margen de victoria y alternancia en la última elección municipal, competitividad esperada) desde SICEE/OPLE. Es donde está el 59–65% de varianza residual.
2. Modelar el **nivel nacional** explícitamente con un intervalo (±3–5 pp) y propagar a los escenarios.
3. Reportar el semáforo con **bandas de incertidumbre**, no con un valor puntual, y marcar secciones de alto error (rurales; Tlaxcala, Guerrero, Chiapas).
4. Mantener P1 y Lasso/Ridge como línea y modelo de producción; árboles solo si se agrega información que justifique interacciones.

## 9. Enfoques alternativos probados (geoespacial, física social, demografía, riesgo)

Mismo backtest (folds 2021/2024), referencia S2 = rezagos semánticos + edad, Ridge. Δ RMSE pareado con IC95% por municipio; negativo = mejor. Código: `analysis/alt_approaches.py`, tablas `reports/alt_*.csv`, `reports/alt_diag.txt`.

| Enfoque | Qué se hizo | Δ RMSE 2021 | Δ RMSE 2024 | Veredicto |
|---|---|---|---|---|
| Persistencia de choques locales | Residuo de la transición previa (sección y municipio) como feature | +0.0019 | +0.0003 | No ayuda |
| Difusión multi-escala (DeGroot / suavizado en grafo) | P1 y M1 promediados con 1, 2 y 4 saltos sobre vecinos (KNN-8) | +0.0018 | **−0.0008** | Solo 2024, mínimo; LightGBM empeora |
| Pendientes espacialmente variables (estilo GWR) | Pendiente de P1/M1 e intercepto por estado | +0.0068 | +0.0158 | Sobreajusta |
| Idem por 40 regiones k-means | Igual, sobre centroides | +0.0078 | +0.0111 | Sobreajusta |
| Combinación A+D+B | Todo junto | +0.0110 | +0.0187 | Peor |
| Dinámica demográfica | Crecimiento de la lista nominal; proporción 18–24 y 60+; su cambio | −0.0002 | −0.0002 (Ridge) | ≤1%, irrelevante |

**Diagnóstico de fondo (enfoque A).** La correlación del residuo entre transiciones consecutivas es ≈0 a nivel sección (+0.014, −0.008, +0.002) y casi nula a nivel municipio (+0.002, +0.180, +0.045). Los choques locales **no persisten ni se revierten**: no hay una señal temporal que explotar con estos datos. Esto es consistente con el techo de §6.

**Riesgo como ranking de "deterioro" (enfoque F).** Se evaluó si un criterio ordena bien qué secciones empeoran respecto a la última elección del mismo tipo (Spearman y precisión en el decil superior; azar = 0.10):

| Criterio | 2021: Spearman / precisión@10% | 2024: Spearman / precisión@10% |
|---|---|---|
| Ridge S2 (predicción − última del mismo tipo) | 0.75 / 0.46 | 0.39 / 0.29 |
| Heurística tendencia (a1 − a2) | 0.77 / 0.51 | 0.22 / 0.17 |
| Abstención alta en la última del mismo tipo | −0.49 / 0.01 | −0.20 / 0.03 |
| Azar | 0.00 / 0.10 | 0.00 / 0.10 |

Dos advertencias. (1) La heurística de tendencia comparte el término `−a2` con la variable "cambio", por lo que su Spearman en 2021 está inflado mecánicamente; en 2024 el modelo es claramente mejor. (2) El signo negativo del criterio "abstención alta antes" muestra que el cambio está dominado por **regresión a la media**: las secciones que "empeoran" son sobre todo las que habían participado de forma inusualmente alta. Un semáforo de riesgo basado solo en el cambio marcaría esas secciones; conviene combinar **nivel esperado** (¿dónde la abstención será alta?) con **cambio** (¿dónde se deteriora?).

**Lo que no se probó y por qué.** Modelos tipo Ising/umbral de Granovetter y percolación: sin variables de interacción medidas, un modelo mecanístico no tiene cómo calibrarse con 6 instantáneas por sección. Factorización de matrices/PCA de la matriz sección×elección: con solo 4 rezagos relevantes y ruido de medición del 2–3%, el rango reducido no tiene qué eliminar. Un multiplicador social espacial (efecto de derrame de una intervención sobre vecinos) sí es útil para **escenarios**, pero su parámetro no es identificable con datos observacionales; si se usa, debe presentarse como supuesto explícito con rango de sensibilidad.

## 10. Literatura consultada (oct-2026) y nivel de verificación

Búsqueda web limitada; el buscador devolvió sobre todo trabajos anteriores a 2022 y notas de prensa. **No se encontró** literatura académica de 2022–2026 sobre predicción de participación por sección en México, lo que no demuestra que no exista. Los conceptos mencionados en §6 (teoría de oleada y declive, competitividad) **no se recuperaron en la búsqueda y no deben citarse** hasta verificarlos.

| Fuente | Nivel de verificación | Relación con los resultados |
|---|---|---|
| Finan, Seira y Simpser, *Voting with One's Neighbors* (documento de trabajo, 31-jul-2021) | Texto leído (resumen e introducción) | Efectos de pares a nivel manzana: mudarse a una manzana con 10 pp más de participación se asocia con ≈0.5 pp más de probabilidad de votar. Respalda la hipótesis de contagio espacial, con efecto individual pequeño |
| Lizama Carrasco, abstencionismo municipal 1994–2009 (reseña UAEH) | Solo resumen/reseña | Agrupamiento espacial con Moran y LISA; consistente con Moran I ≈ 0.7 aquí |
| Política y Gobierno, abstencionismo, escolaridad y confianza, elecciones 2003 | Solo fragmento del buscador | Reporta menor participación en municipios con mayor escolaridad; consistente con la correlación casi nula de escolaridad aquí |
| Estudio de abstencionismo del INE (portal anterior) | Solo fragmento del buscador | Reporta distritos abstencionistas más rurales. **Contradice** lo observado aquí (rural 40.7% < urbano 47.5% en 2021). Revisar año y unidad antes de afirmar cuál aplica |
| Base de datos de casilla para elecciones municipales, Scientific Data 2025 | Solo resumen y página de la comunidad | 1994–2019, 31 estados, >2,400 municipios; votos por partido, votos totales, lista nominal y participación. Candidata a fuente de competitividad municipal, pero **termina en 2019** y no cubre 2021 ni 2024 |
| Humbert, tesis ASU 2018, elecciones locales concurrentes | Solo resumen | Efecto de la concurrencia sobre resultados partidistas; sin efecto sobre participación confirmado |
| Cifras de participación 2021 (52.7%) y 2024 (59.6%), citadas por prensa a partir de estudios del INE | Secundaria | Coinciden con la abstención ajustada obtenida aquí: 2024 = 40.3% (1−0.596 = 40.4%); 2021 = 48.2% (1−0.527 = 47.3%) |

## 11. Datos nuevos INE/INEGI/Magar probados para llegar a 0.82 (2026-10-11)

Mismo backtest (folds 2021/2024, referencia S2 Ridge: R² 0.616 / 0.710). Código: `analysis/extra_test2.py`, `party_test.py`, `extra_test3.py`; tablas `reports/extra_inegi_test.csv`, `party_test.csv`, `extra_calendario_test.csv`.

| Fuente | R² honesto 2021 / 2024 (mejor de Ridge/LGBM) | Techo estático (mismo año) | Veredicto |
|---|---|---|---|
| ECEG 2010→2020 (cambio sociodemográfico) | 0.612 / 0.674 (peor) | 0.735 / 0.779 | No ayuda ex ante |
| DENUE (economía local) | 0.616 / 0.696 (+0.006 solo LGBM 2024) | 0.713 / 0.760 | Irrelevante |
| Todo INEGI nuevo | 0.585 / 0.678 (peor) | 0.752 / 0.790 | Sobreajuste temporal |
| Voto por bloque (Morena/PRI/PAN/PRD), margen y swing por sección, panel largo 2006-2024 (Magar) | LGBM +0.055 en 2021, −0.04 en 2024; Ridge inestable | n/a | Mixto, no robusto |
| Calendario municipal verdadero en T (ayuntamiento, concurrencia federal/gubernatura/congreso local) | 0.621 / 0.724 Ridge (+0.005 / +0.014) | n/a | Mejor caso, ya con oráculo: insuficiente |
| Margen y participación de la última elección municipal | 0.627 / 0.690 | n/a | No ayuda |
| Agregar a municipio o estado (R² honesto) | municipio 0.60 / 0.72; estado 0.54 / 0.73 | n/a | No sube: el error es municipal/estatal, no ruido de sección |

**Conclusión.** Con la información disponible antes de la elección no hay palanca que lleve a 0.82. Lo único que supera 0.82 usa datos del propio año objetivo: LGBM ponderado por electores con CV por municipio (0.81 en 2021, 0.84 en 2024, `ceiling_decomposition.csv`) o la media municipal del residuo (fuga). Si se presenta 0.82, debe etiquetarse como R² dentro de muestra/estático ponderado, no como pronóstico. Corrección: `extra_test2.py` fallaba con infinitos (cociente con población 2010 = 0) y no había producido resultados hasta hoy.

### 11.1 Historia más larga y cuánta información extra haría falta (2026-10-11)

- **Perfil histórico por sección desde 1994** (media de elecciones del mismo tipo/otro tipo, dispersión, brecha de ciclo intermedia−presidencial; `extra_test4.py`, `extra_test5.py`). En el arnés principal 2021 sube 0.616→0.656 (Ridge) pero 2024 baja 0.711→0.653; en el panel largo, con 2-6 transiciones de entrenamiento, empeora 2012 y 2024 y no cambia 2018/2021. El +0.04 de 2021 se debe a entrenar con un solo objetivo (2018); no es robusto. Calendario estatal verificado con Magar: ±0.005.
- **Información necesaria para 0.82** (`info_needed.py`, `reports/info_needed.csv`): R² de la predicción honesta Ridge más la media LOO del residuo por grupo (choque del año objetivo).

| Se conociera el choque medio por… | 2021 | 2024 |
|---|---|---|
| nada (honesto) | 0.616 | 0.711 |
| estado (32) | 0.722 | 0.780 |
| distrito federal (300) | 0.796 | 0.807 |
| municipio (~2,400) | 0.861 | 0.849 |
| 300 grupos al azar (control) | 0.614 | 0.709 |

0.82 exige conocer el choque a nivel distrital-municipal (p. ej. encuesta distrital o conteo parcial). Con el choque estatal supuesto en un escenario, el R² condicional es 0.72-0.78.

### 11.2 Palancas predictivas para escenarios (2026-10-11)

Solo ex ante. Código: `extra_test6.py`, `escenarios_base.py`; tablas `extra_cargas_test.csv`.

- **Carga de respuesta al cambio nacional** (brecha media presidencial↔intermedia de ciclos previos, 1994+) a nivel estado/municipio/sección: 2021 +0.00 a +0.03 R², 2024 −0.01 a −0.06 (mismo patrón que §11.1: aparente ganancia con un solo objetivo de entrenamiento, no robusta).
- **Persistencia del choque** (residuo del modelo honesto): corr(2021, 2024) = 0.22 por estado (n=32), 0.17 por municipio. Trasladarlo a 2024 *baja* el R² (0.711 → 0.698 con λ=0.2 estatal): no se usa.
- **Nivel nacional en intermedias** (abstención por acta, dip. federal): 2009 55.4%, 2015 52.6%, 2021 47.8%. Persistir la última intermedia sobreestima 3.6 pp en promedio (siempre hacia arriba); extrapolar la tendencia intermedia a intermedia tuvo error 0.4 pp (2015) y 2.0 pp (2021), n=2. Para 2027 la tendencia da ≈43% y la persistencia ≈48%; usar ese rango como escenarios nacionales bajo/alto.
- **Datos distritales de coyuntura** ex ante probados: ECEG 2010-2020, DENUE, CONEVAL, SESNSP, voto por partido, calendario y margen municipal: ninguno mejora el honesto (§11).

### 11.3 Clusters geográfico-culturales (2026-10-11)

`analysis/cluster_test.py`, `cluster_rev.py`; tablas `cluster_test.csv`, `cluster_rev.csv`. Clusters k-means definidos sin información del año objetivo: geográficos (coordenadas), culturales (ECEG 2020: lengua indígena, sin religión, escolaridad, migración interna, hogar, etc.), mixtos y de trayectoria electoral.

- **Los choques sí son espaciales.** Si se conociera el choque medio del cluster en T: geo k=300 → R² 0.77 (2021) / 0.81 (2024); k=100 → 0.74 / 0.79; clusters culturales k=100 → 0.71 / 0.75; mixtos k=300 → 0.75 / 0.79. Un control al azar con 300 grupos no mejora (0.61). Son comparables a los distritos federales (0.80 / 0.81): la geografía fina captura el choque.
- **Pero no es predecible del ciclo anterior.** Corr del choque 2021→2024 por cluster: geo +0.02 a +0.12, mixtos −0.01 a −0.09, culturales y de trayectoria −0.30 a −0.38. Trasladar el choque (λ=0.3) baja el R² 2024 de 0.713 a 0.68-0.70.
- **La reversión negativa no es estable.** En 5 pares de ciclos (panel largo) el signo alterna: 2012→2015 positivo (0.14 a 0.69), 2015→2018 negativo (−0.37 a −0.43), 2018→2021 positivo o nulo, 2021→2024 negativo. Aplicar una λ estimada con pares anteriores empeora en casi todos los pares. Los clusters culturales no tienen dinámica común predecible entre elecciones.

### 11.4 Qué hay debajo de los choques geográficos (2026-10-11)

`analysis/underlying.py`, `underlying2.py`. Residuo del Ridge honesto (2021, 2024).

- **Son jurisdiccionales, no geográficos.** A distancia igualada, la correlación del residuo entre secciones vecinas es 0.74 / 0.50 (2021 / 2024) en el mismo municipio a <700 m y 0.71 / 0.57 a 3-8 km: la distancia casi no importa. Pasando a otro municipio del mismo estado baja a 0.56 / 0.30 (0.51 / 0.40 a 3-8 km) y a otro estado a ≈0.0-0.1 (algunos valores 0.3-0.4 en zonas conurbadas, n≈2,000). Una cultura o un paisaje continuos no cortarían así en una frontera.
- **Peso por nivel:** estado explica 28% / 24% de la varianza del residuo y municipio 66% / 51% (R² ajustado). Los efectos fijos de estado solos explican 0.40 / 0.39 de la varianza del choque municipal; añadir 11 rasgos censales y de tendencia llega a 0.64 / 0.57 dentro de muestra, pero la corr de los coeficientes entre 2021 y 2024 es −0.32 (p. ej. `a1` +0.33 → −0.21, `graproes` −0.09 → −0.28, `tendencia` −0.04 → +0.45): la relación rasgo→choque cambia con la elección.
- **Estados extremos** (pp, vs modelo): 2021 Tlaxcala −11.9, Nayarit −7.8, Veracruz −6.2; arriba Tabasco +7.3, Hidalgo +7.2. 2024 Tlaxcala −6.3 de nuevo; arriba Tabasco +6.1, Chiapas +4.4.
- **Lectura:** el choque viene del contexto político-administrativo de la elección (campaña local, gobierno estatal/municipal, estructura de partido), no de afinidad cultural o geográfica; por eso clusters continuos no lo capturan y por eso cambia de signo entre ciclos.

### 11.5 Causas del choque jurisdiccional: explicación, no predicción (2026-10-11)

`analysis/causas_mun.py`, `surge_decline.py`; tabla `surge_decline.csv`. Es análisis explicativo (variables del propio año T), no un modelo predictivo.

- **Choque municipal ~ factores político-jurisdiccionales (con efectos fijos de estado).** Sobre el residuo del Ridge honesto, municipios con elección concurrente: 2021 R² 0.43 (solo estado) → 0.55 (+ sede abierta, reelección, alternancia, margen, partido ganador y previo, gubernatura concurrente) → 0.63 (+ abstención previa). 2024: 0.41 → 0.44. El factor dominante en 2021 es el partido: los municipios que gana Morena abstienen 2-4.5 pp *más* de lo que el modelo esperaba (PRI −4.3, otros −4.6, PAN −2.2 respecto de Morena). En 2024 ese contraste cae a ≈0.6 pp y aparecen sede abierta (+0.9 pp) y reelección (+0.9 pp). Los signos de los coeficientes coinciden entre años (corr 0.66, n=11) pero las magnitudes cambian ×4-6.
- **Oleada y declive** (la fuerza del partido ganador de la última presidencial predice sobre-abstención en la intermedia siguiente, pp por SD, controlando P1 y M1): 2003 +1.0 (PAN, t=1.9), 2009 +0.15 (n.s.), 2015 −0.7 (PRI, n.s.), **2021 +2.5 (Morena, t=4.8)**. Solo 2021 es claro; no es regularidad de los cuatro ciclos intermedios. En las presidenciales el efecto es ≈0 o pequeño (2012 +1.4, 2018 +1.0, 2024 +0.15).
- **Lectura:** el declive tras la oleada de 2018 fue un fenómeno específico de Morena como partido nuevo con votantes de baja propensión, no una ley general. Para 2027 (intermedia tras presidencial de Morena) la analogía sugiere sobre-abstención en bastiones de Morena, pero con n=1 ciclo comparable no se puede validar ni calibrar.
- **Literatura consultada (solo resúmenes de buscador, no verificada a texto completo):** Trelles y Carreras 2012 (violencia y participación municipal 2000-2010; efecto negativo), Ley (ataques a autoridades se asocian con −1 pp en municipales y −2 pp en federales; hallazgo contrario en un trabajo reciente de asesinatos políticos), Hernández-Huerta 2026 (maquinarias partidistas estatales y ventaja del titular en gubernaturas), Díaz-Cayeros et al. (clientelismo como construcción de partido), Klesner (maquinaria del PRI y costo de abstenerse), Moscú 2012-18 (descomposición SVD de la participación en componente histórico y geográfico).

### 11.6 Diseño de frontera, eventos municipales con efectos fijos y descomposición SVD (2026-10-11)

Código: `analysis/border_design.py`, `panel_events.py`, `matrix_svd.py`; tablas `border_pairs.csv`, `panel_events.csv`.

**Diseño de frontera estatal** (secciones a <3 km a ambos lados; 747 pares en 25 fronteras en 2021 y 697 en 21 en 2024; sd de la diferencia de choque 0.089 / 0.046, frente a 0.111 / 0.080 entre secciones al azar del mismo estado).
- Regresión de la diferencia de choque sobre diferencias estatales (EE agrupados por frontera). 2021: la diferencia en la proporción de municipios ganados por Morena predice la diferencia de choque (+11 pp por 100 pp de diferencia, t=2.6); concurrencia de gubernatura n.s. 2024: nada (−1.8 pp, t=−0.4). Mismo patrón que §11.5: contexto partidista estatal relevante solo en 2021.
- Caso extremo: frontera Puebla–Tlaxcala, salto medio de 19 pp en 2021 y 5.8 pp en 2024 entre secciones contiguas (Tlaxcala es el estado más extremo en ambos años). Con geografía y cultura casi idénticas, esto solo se explica por el contexto político-administrativo de cada estado en esa elección. Pocas fronteras (25 y 21), así que es descripción, no estimación general.

**Eventos municipales con efectos fijos de sección y estado×año** (panel 1994-2024, 386 mil observaciones, 59 mil secciones, solo municipios con elección concurrente; EE agrupados por municipio; coeficientes en pp):

| Evento | todas | 1994-2012 | 2015-2024 | intermedias | presidenciales |
|---|---|---|---|---|---|
| Margen de victoria municipal (por unidad) | +2.0 (t=2.4) | +2.2 | +2.0 | +2.6 | +1.3 |
| Gana Morena | +0.7 (t=2.7) | n/d | −0.1 | +1.2 (t=2.3) | +0.8 (t=3.8) |
| Alternancia | −0.2 | +0.2 | −0.1 | −0.4 | −0.3 |
| Sede abierta | +0.2 | −0.9 | +0.4 | −0.2 | +0.2 |
| Reelección | +0.2 | n/d | +0.3 | +0.3 | +0.5 |

Las competencias municipales cerradas elevan la participación (≈2 pp por unidad de margen) y la presencia de Morena como ganador local se asocia a ≈1 pp más de abstención en la misma sección. Pero ningún efecto supera ≈2 pp frente a un sd del choque de 6-8 pp: **los eventos municipales documentados explican muy poco del choque**.

**Descomposición SVD municipio×elección** (2,442 municipios con las 11 elecciones 1994-2024, relativo al nivel nacional; a la manera del análisis de Moscú 2012-18): con el nivel municipal incluido, la primera componente explica 55% y las siguientes 17%, 9%, 5%. Sin el nivel municipal: 36%, 22%, 12%, 8%.
- PC1 cambia de signo con el tiempo (carga +0.45 en 1994 a −0.51 en 2021): redistribución gradual de la abstención entre municipios (los que abstenían más antes abstienen menos hoy).
- PC2 contrasta intermedias con presidenciales y su amplitud cambia por elección (0.70 en 2015, 0.35 en 2009, 0.26 en 2003, ≈−0.2 en 2018-2024): el contraste no es estable.
- Residuo tras rango 3: 31% de la varianza, con **correlación negativa entre elecciones consecutivas** (−0.14 con rango 1, −0.27 con rango 3). La estructura de bajo rango no recoge todo el movimiento, y lo que queda tiende a revertirse, aunque con signos alternantes en los pares ya probados (§11.3).

**Síntesis de causas (§11.4-11.6).** El choque es jurisdiccional (municipio > estado). Se asocia con el partido en el poder (clara en 2021, débil en 2024), con la competitividad municipal (≈+2 pp por unidad de margen) y con rasgos de cada estado que se ven en la frontera (Puebla–Tlaxcala). Los efectos de estos factores cambian de tamaño entre elecciones y los eventos municipales documentados dejan sin explicar la mayor parte de la varianza. Conclusión para el reporte: el choque es **parcialmente explicable a posteriori y no anticipable**; los datos candidatos que no se han probado (violencia política, programas sociales por municipio, gobernador por estado) pertenecen al mismo nivel jurisdiccional.

### 11.7 Qué se puede usar ex ante del año previo (2026-10-11)

`analysis/offyear_local.py`, `bandas.py`; tablas `offyear_local.csv`, `bandas.csv`.

- **Violencia del año previo** (nivel y cambio de homicidios, extorsión, robo, etc., SESNSP): ya probada en `extra_mun_test.csv`, sin mejora (§11 tabla).
- **Participación en elecciones municipales fuera de ciclo federal** (T-4 a T-1) frente a la elección municipal anterior del mismo municipio, como señal de movilización reciente. Coeficiente sobre el choque federal siguiente (pp por SD de cambio de participación local; con efectos fijos de estado):

| T | municipios | estados | coef (pp/SD) | t |
|---|---|---|---|---|
| 2015 | 886 | 17 | −0.86 | −2.7 |
| 2018 | 754 | 15 | −0.20 | −0.9 |
| 2021 | 393 | 7 | +0.13 | 0.3 |
| 2024 | 128 | 4 | −1.94 | −5.5 |

Signo negativo en 3 de 4 ciclos (más participación local reciente → menos sobre-abstención federal después), pero magnitud ≤1 pp salvo 2024 (4 estados) y cobertura de 5-30% de los municipios. Útil como indicio, no como predictor.
- **Bandas de incertidumbre por sección** (cuantiles 10-90% del residuo Ridge de un ciclo aplicados al siguiente): calibradas en 2021 cubren 92% en 2024 (ancho 19 pp) y calibradas en 2024 cubren solo 61% en 2021 (ancho 12.8 pp). Por tipo de sección o tipo×tamaño no mejoran (88%, 87%). Cobertura por estado con la banda global: 0.77-0.99 (2024), 0.23-0.87 (2021). **Regla:** para una intermedia como 2027 conviene calibrar con el ciclo de mayor error (2021, ±9.5 pp al 80%); es conservadora para presidenciales.

### 11.8 Acceso físico a votar: casillas y geometría de la sección (2026-10-11)

`analysis/extra_test7.py`; tabla `extra_acceso_test.csv`. Ya cubiertos antes: salud (`sin_servsalud`, `ic_asalud`), servicios de vivienda, internet/auto/PC, carencias CONEVAL, establecimientos de salud/educación (DENUE). Nuevo: número de casillas del año T-3, electores por casilla, proporción de casillas extraordinarias, área, densidad, compacidad y distancia al centro poblacional del municipio.

| Set | Δ R² 2021 (Ridge / LGBM) | Δ R² 2024 (Ridge / LGBM) | Techo estático 2021 / 2024 |
|---|---|---|---|
| REF S2 | 0.616 / 0.600 | 0.711 / 0.690 | 0.694 / 0.747 |
| + casillas | +0.002 / −0.003 | −0.016 / +0.001 | 0.705 / 0.752 |
| + geometría | 0.000 / −0.017 | −0.045 / +0.013 | 0.728 / 0.773 |
| + ambos | +0.002 / −0.015 | −0.047 / +0.007 | 0.732 / 0.773 |

Sin mejora ex ante; el techo estático sube 0.02-0.04 (geometría). Razón conceptual: un atributo fijo de acceso (distancia, transporte, salud, geometría) ya está incorporado en la abstención pasada de la sección; solo aportaría algo si cambiara en el tiempo, y la infraestructura externa (caminos, transporte, CLUES) cambia lentamente. No se descargaron esas fuentes externas.

### 11.9 Ecosistema de medios del hogar (2026-10-11)

`analysis/extra_test8.py`; tabla `extra_medios_test.csv`. Censo 2020 y 2010 por sección: proporción de viviendas con radio, TV, TV de paga (solo 2020), celular, teléfono fijo, internet, PC y sin radio ni TV (solo 2020); niveles 2020, 2010 y cambio 2010→2020. Antes solo se usaba internet y PC (en razones del censo 2020).

| Set | R² 2021 Ridge / LGBM | R² 2024 Ridge / LGBM | Techo estático 2021 / 2024 |
|---|---|---|---|
| REF S2 | 0.616 / 0.600 | 0.711 / 0.690 | 0.694 / 0.747 |
| + medios 2020 | 0.611 / 0.591 | 0.672 / 0.685 | 0.737 / 0.786 |
| + medios 2010 | 0.619 / 0.599 | 0.667 / 0.681 | n/d |
| + cambio 2010→2020 | 0.625 / 0.600 | 0.657 / 0.683 | 0.725 / 0.770 |
| + todo medios | 0.611 / 0.592 | 0.662 / 0.681 | 0.738 / 0.788 |

Sin mejora ex ante (Δ RMSE ≤ +0.005, el cambio 2010→2020 con Ridge 2021 es −0.0009, dentro de ruido); sí aporta dentro del año (techo estático +0.04, el mayor entre los grupos probados junto con DENUE y ECEG), señal de que el entorno mediático se asocia con la abstención pero con un efecto que cambia entre elecciones. Los datos de medios de la elección misma (pauta de radio y TV del INE por entidad, publicidad política en plataformas, uso de internet por entidad en ENDUTIH) no se descargaron; serían a lo más estatales y solo 2 elecciones comparables para validar.

### 11.10 Señales creativas: movilización fuera de ciclo y alineación política vertical (2026-10-11)

Código: `analysis/rm2022_test.py`, `alignment.py`, `alignment_pred.py`; tablas `alignment_state.csv`, `alignment_mun.csv`, `alignment_pred.csv`. Datos nuevos: Revocación de Mandato 2022 por casilla (INE, `data/raw/rm2022/`, bajada del botón de descarga de computosrm2022.ine.mx; solo 24,458 secciones porque se instalaron 57 mil casillas en vez de las ~163 mil usuales), gubernaturas 1961-2025 con fecha de toma de posesión (Magar `goed`).

**a) Participación en la Revocación de Mandato 2022 como capacidad de movilización → choque 2024.** Cubre 22,411 de las secciones de la prueba. Correlación con el residuo 2024: +0.21, pero esa asociación es estatal: con efectos fijos de estado el coeficiente cambia de signo (−0.29 pp por SD, t=−2.1). Validación cruzada dejando fuera estados completos (la medida honesta, 32 grupos): R² total 2024 de 0.747 → 0.749 (solo RM), 0.755 (+ voto Morena 2021) y 0.759 (+ votos «siga» y «revoque»). Ganancia ≤ +0.013, un solo ciclo validado (no hay análogo para 2021) y solo en 1/3 de las secciones. Una señal análoga para 2027 sería la elección judicial 2025 (el INE la publica por sección en SICEE; no se descargó).

**b) Alineación vertical.**
- *Estatal* (choque por estado, 5 elecciones 2012-2024, n=160, FE de año, EE por estado): gubernatura concurrente −2.7 pp (t=−3.2; −4.2 pp en intermedias, t=−3.4); gobernador del partido del presidente +3.1 pp en intermedias (t=2.0) y −0.9 en presidenciales (interacción +4.9, t=2.8), con signo que alterna por año.
- *Municipal* (panel 1994-2024, 684 mil observaciones, FE de sección y estado×año, EE por municipio): presidente municipal del partido del presidente de la República → **+0.9 a +1.1 pp** de abstención en la sección, estable entre épocas (1994-2012 +0.87, t=6.1; 2015-2024 +0.89, t=3.8; intermedias +1.3; presidenciales +0.5; todas t=8.5). Alineado con el gobernador: +0.5 (t=2.1) pero cambia de signo en 2015-2024 (−0.55).
- *Predicción* (rolling-origin con todos los objetivos pasados desde 2006): agregar gubernatura concurrente y alineaciones da en promedio de 5 pruebas −0.011 a +0.005 de R² (Ridge) y −0.007 a +0.001 (LGBM), con mínimos de −0.03 a −0.09. La gubernatura concurrente sube el R² de 2015 de 0.435 a 0.526 y baja el de 2021 de 0.466 a 0.396: el efecto existe pero su tamaño por elección no es estable.

**Lectura.** Hay una regularidad persistente (la alineación municipal con el presidente se asocia con ≈1 pp más de abstención durante 30 años) y una conocida con anticipación (gubernaturas en juego), pero su tamaño no alcanza para mover el R² frente a un choque de 6-8 pp, y el efecto de la concurrencia varía de una elección a otra.

### 11.11 Gasto de campaña por distrito (2026-10-11)

`analysis/gasto_test.py`; tabla `gasto_distrito.csv`; datos `data/raw/sif/` (INE, portal de fiscalización, descarga de reportes: gasto total y por rubro por candidato, diputaciones federales MR 2018, 2021, 2024; 300 distritos cada año, gasto medio por distrito 2.3 / 4.3 / 3.1 millones de pesos).

Choque distrital = media del residuo del Ridge honesto por distrito (sd 5.4 pp en 2021, 3.3 pp en 2024). Regresión ponderada con efectos fijos de estado (EE por estado), coeficientes en pp por SD:

| Variable | 2021 | 2024 |
|---|---|---|
| log gasto total por elector | +0.05 (t=0.2) | −0.02 (t=−0.1) |
| idem + abstención previa | +0.17 (t=0.8) | −0.01 (t=−0.1) |
| gasto del ciclo anterior (T-3) | +0.51 (t=1.1) | −0.24 (t=−1.3) |
| proporción del gasto en medios (radio/TV, internet, vía pública, diarios) | +0.58 (t=1.6) | −0.62 (t=−4.3) |

El gasto de candidatos a diputación no explica el choque distrital en ningún año; la proporción en medios cambia de signo. Limitaciones: es gasto reportado de las candidaturas (no incluye propaganda de partidos en periodo ordinario ni gasto nacional de las campañas presidenciales), es endógeno (los partidos gastan donde la contienda está cerrada) y su valor final solo se conoce después de la campaña. El gasto del propio INE en promoción del voto es nacional y no varía por distrito, por lo que no es estimable con estos datos.

### 10.1 Estado del arte: lo que se encontró (2026-10-11)

No se encontró un benchmark estándar de pronóstico de participación a nivel sección o casilla en México ni en otros países. Referencias más cercanas:

| Fuente | Verificación | Resultado relevante |
|---|---|---|
| Ansolabehere, Brown, Khanna, Phillips y Stewart, *Forecasting Turnout*, Harvard Data Science Review 6(4), oct-2024 | Resumen (el texto completo devolvió 403) | Compara modelos académicos de participación (registro, voto rezagado, demografía, competitividad, voto anticipado), ajustados con elecciones previas para predecir 2016 (desde 2012) y 2020 (desde 2016). El modelo más simple, de registro, supera a los demás. Interpretan que la tendencia de los registrados a votar en presidenciales es estable |
| Di Biase, tesis de maestría UTDT 2025, participación por mesa en la provincia de Buenos Aires, 2011-2023 (>240 mil mesas) | Texto extraído y leído (métodos y resultados) | Validación dejando una elección fuera (LOEO), 7 pliegues: RMSE Elastic Net 4.58 pp, XGBoost 4.96, Random Forest 5.01. Predictores incluyen la participación de las PASO del mismo año (voto obligatorio), así que no es comparable en nivel con este trabajo. Es una tesis, no un resultado publicado |
| Trabajos de estimación en áreas pequeñas (Chandra, Salvati, Chambers) y modelo bayesiano que combina encuestas con datos agregados | Solo títulos y resúmenes de buscador | Metodología para estimar participación donde las encuestas no llegan; no es pronóstico ex ante |

Coincidencia con lo observado aquí: el modelo lineal regularizado empata o supera a los árboles, y la persistencia (repetir la participación pasada del mismo tipo) es una línea base difícil de vencer.

### 11.12 Información intra-año: delitos de enero a mayo del año de la elección (2026-10-12)

`analysis/intrayear_crime.py`. SESNSP mensual: homicidio doloso, extorsión, robo y total, enero-mayo de T. Choque municipal (media del residuo del Ridge honesto, municipios con ≥3 secciones y >1,000 electores; ≈1,930 por año) ~ variable estandarizada + efectos fijos de estado (WLS, EE por estado). Coeficientes en pp por SD:

| Variable (ene-may de T) | 2021 | 2024 |
|---|---|---|
| cambio log de homicidios vs ene-may de T-1 | +0.06 (t=0.3) | +0.11 (t=0.7) |
| cambio de extorsión | −0.41 (t=−2.2) | −0.12 (t=−1.1) |
| cambio de robos | −0.48 (t=−1.8) | +0.21 (t=1.4) |
| cambio del total de delitos | −0.26 (t=−0.6) | +0.24 (t=1.6) |
| tasa de homicidios por 10 mil electores | +1.23 (t=5.9) | −0.05 (t=−0.4) |
| tasa de robos | +3.01 (t=5.3) | −0.94 (t=−2.7) |
| tasa del total de delitos | +3.47 (t=5.4) | −0.87 (t=−2.3) |

El cambio intra-año (el choque) no se asocia con el choque electoral; el nivel sí en 2021 y con signo contrario en 2024. Es la misma historia de relaciones que cambian entre elecciones, y el nivel de delitos ya está recogido por la abstención pasada de la sección.

### 11.13 Fuentes intra-año buscadas y no disponibles (2026-10-12)

Búsqueda de dos bases de movilización por distrito antes de la jornada:
- **Capacitación de funcionarios de casilla (ciudadanos sorteados, notificados, visitados y capacitados).** Solo se encontraron guías operativas del INE y cifras agregadas por entidad en notas de prensa (p. ej. INE Morelos 2024: 207,290 visitados y 38,178 capacitados). No apareció una base descargable por distrito para 2021 o 2024; los informes de integración de mesas directivas del INE podrían traer tablas distritales en PDF, sin verificar.
- **Representantes de partido ante casilla registrados.** El INE opera un sistema de registro (modelo aprobado para 2021 y 2024; 2.9 millones de solicitudes en 2021) pero no se encontró un archivo por distrito; las series publicadas encontradas son de 2008-2009 y 2011-2012.

No se probaron. Se probó y descartó la incidencia delictiva ene-may del año de la elección (§11.12).
