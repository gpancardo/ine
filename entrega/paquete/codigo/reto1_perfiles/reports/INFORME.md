# Reto 1. Perfiles ciudadanos de participación

Borrador de trabajo (revisado el 2026-10-14). Datos: Conteos Censales de Participación Ciudadana 2009-2024 (Plataforma CCPC, INE-DECEyEC), agregados por sección, sexo y edad; descriptores del Censo 2020 (ECEG) y resultados electorales por casilla. No se usan datos personales. Todo es reproducible con `reto1_perfiles/analysis/` (ver `README.md` de esta carpeta).

## 0. Resumen

- **Qué se hizo.** Se segmentaron 64,096 secciones electorales (92% de la lista nominal) en **cinco perfiles** según tres rasgos de participación: nivel, brecha de género (18-54 años) y brecha de jóvenes (18-34 frente a 55-74). Cada perfil se caracteriza por edad, sexo, región, historial de participación 2009-2024, escolaridad y conectividad (censo) y se acompaña de una estrategia, mensaje y canal.
- **Qué se encontró.** La participación se ordena en un continuo, no en grupos naturales (§5). Aun así, los tres rasgos son **persistentes** entre elecciones separadas (correlación de 0.5 a 0.7 entre 2009-2015 y 2018-2024), y los perfiles construidos solo con 2009-2018 explican parte de lo que ocurre en 2024 (32% de la varianza del nivel y 27% de la brecha de género, frente a ≈0% para grupos al azar y 27% y 10% para los 32 estados). En la brecha de jóvenes el estado explica más que el perfil (0.20 frente a 0.15); combinados, el perfil añade de 0.13 a 0.23 de R² sobre el estado (§5.1).
- **Hallazgo que corrige una intuición.** La *intermitencia* (votar en presidenciales y no en intermedias) es un fenómeno de todo el país, y **no persiste** como rasgo de cada territorio (correlación 0.28 en secciones y 0.07 en municipios entre ventanas). No se usó para segmentar ni para focalizar: las campañas para las intermedias deben ser nacionales, no dirigidas a territorios "intermitentes".
- **Hipótesis descartada.** La brecha masculina del perfil rural no se explica por hombres que siguen en la lista nominal pero ya no residen (la razón lista/censo es la misma para hombres y mujeres); su causa queda abierta.
- **Qué representación conserva información.** Con cinco segmentos, los grupos duros pierden cerca de la mitad de lo que predicen los rasgos continuos; las pertenencias suaves (arquetipos) no pierden nada. Los segmentos sirven para comunicar y los rasgos continuos para planear.
- **Dónde está el potencial.** Si cada brecha se cerrara hasta el nivel de secciones comparables, se recuperarían 7.7 millones de votos por elección por el nivel (IC95% 6.5-8.9), 3.8 millones por la brecha de género de los hombres de 18 a 54 años y 3.5 por los jóvenes. Solo 61 municipios (2.5%) concentran la mitad del potencial por nivel. La cifra depende sobre todo del punto de referencia (4.1 millones con la mediana de comparables, 11.9 con el percentil 90), más que del muestreo, y está sobreestimada donde la lista nominal incluye personas que ya no residen.

## 1. Datos y definiciones
- **Participación** = personas con marca de voto en el cuadernillo de la lista nominal entre las que tienen registro de captura (SV / (SV + NV)); se excluyen los no capturados (NS). No incluye casillas especiales ni voto en el extranjero. La lista nominal incluye a quienes ya no viven ahí o fallecieron, lo que sobreestima la abstención donde hay emigración.
- **Unidad**: sección electoral. Se usan las secciones presentes en 2015, 2018, 2021 y 2024 con al menos 800 registros en el conjunto (8% de la lista nominal queda fuera).
- Las tasas por grupo de edad y sexo dentro de una sección se observan directamente (son registros individuales agregados). Los descriptores de escolaridad, lengua indígena, internet y migración vienen del censo por sección: son **ecológicos** (características de la sección, no de las personas que votan o no).

## 2. Método
1. **Rasgos con encogimiento.** Cada tasa se encoge hacia la tasa nacional del mismo subconjunto (30 observaciones ficticias) para controlar el ruido de celdas pequeñas.
2. **Elección de rasgos por persistencia.** De ocho rasgos candidatos se agrupó solo con los que se mantienen entre ventanas de elecciones separadas (§5): **nivel** relativo al nacional de cada elección, **brecha de género 18-54** (mujeres menos hombres) y **brecha de jóvenes** (18-34 menos 55-74). Quedaron como descripción: la caída de los 75+, la brecha de género 55+, la intermitencia y la tendencia 2018-2024.
3. **Segmentación.** K-means con k=5 sobre los tres rasgos estandarizados. La convocatoria pide de 4 a 6 perfiles; dentro de ese rango, k=5 es el más estable entre ventanas (ARI 0.34-0.39, IC95% por remuestreo de municipios, frente a 0.30-0.35 con k=4 y 0.27-0.31 con k=6) y predice 2024 mejor que k=4 en el 100% de las réplicas (R² medio 0.23-0.26 frente a 0.21-0.24; `elegir_k_ic.csv`). Un k mayor predice algo más (0.27-0.31 con k=8), pero pierde estabilidad y queda fuera del rango pedido.
4. **Alternativas probadas** (§5): árbol de decisión multisalida entrenado para predecir el perfil de 2024 (misma capacidad que K-means, R² medio 0.21 en ambos), mezcla gaussiana y Ward (fronteras distintas). También se compararon representaciones suaves (§5): con el mismo número de segmentos, los **arquetipos** (cada sección como mezcla de cinco perfiles extremos) conservan toda la información predictiva de los rasgos continuos, mientras que los grupos duros de K-means pierden cerca de la mitad. Se conservó K-means como segmentación comunicable porque equilibra los tres ejes, y se recomienda usar los rasgos continuos (o pertenencias suaves) para planear. Se le añadió un **conjunto de reglas explícitas** (árbol sustituto de 8 hojas, fidelidad 78% en validación cruzada por entidad; `reglas_segmentos.txt`) para clasificar cualquier sección o municipio con umbrales transparentes.

## 3. Los cinco perfiles
Todas las cifras de 2024 salvo que se indique. Fuentes: `tipologia_perfiles.csv`, `tipologia_curvas_2024.csv`, `tipologia_historial.csv`, `tipologia_regiones.csv`, `medios_perfiles.csv`. Figuras 1 a 3, 6 y 7.

| Perfil | Secciones | Lista nominal | Participación media 2015-2024 | Brecha de género 18-54 (M−H) | Jóvenes 18-34 frente a 55-74 | Región principal |
|---|---|---|---|---|---|---|
| 1. Baja participación del norte urbano | 11,330 | 19.3 M (21%) | 44% | 8 pp | −20 pp | Norte 48% |
| 2. Rezago juvenil urbano | 17,349 | 26.3 M (29%) | 52% | 11 pp | **−26 pp** | Centro 42% |
| 3. Rural con brecha masculina | 8,434 | 10.4 M (12%) | 60% | **19 pp** | −22 pp | Centro 34%, Sur y Sureste 27% |
| 4. Urbano de participación media-alta | 18,829 | 24.6 M (27%) | 62% | 8 pp | −20 pp | Centro 45% |
| 5. Alta participación comunitaria | 8,154 | 9.6 M (11%) | 67% | 11 pp | **−10 pp** | Occidente y Bajío 34%, Sur y Sureste 32% |

### 3.1 Baja participación del norte urbano
**Quiénes y dónde.** Ciudades del norte: Baja California (90% de su lista nominal está en este perfil), Chihuahua (69%), Durango (48%), Quintana Roo (45%) y Sonora (44%). 77% de las secciones son urbanas y 20% de la población nació en otra entidad, la proporción más alta de los cinco perfiles. **Participación**: la más baja en todas las elecciones (35% en 2009, 49% en 2024) y en todas las edades (hombres de 25 a 34 años, 35%; mujeres, 45%). Es el perfil donde los de 75 años y más participan relativamente mejor (−11 pp frente a 55-74). **Contexto**: 9.6 años de escolaridad, 55% de hogares con internet, 91% con celular, 92% con TV.
**Narrativa.** Una ciudadanía urbana, conectada y móvil, con una abstención estructural en todos los grupos de edad.
**Estrategia propuesta** (hipótesis de política pública; el análisis no estima su efecto):
- *Objetivo*: reducir la fricción práctica para votar, no solo informar.
- *Mensaje*: "tu voto cuenta donde vives": cómo actualizar el domicilio de la credencial y dónde votar.
- *Canal*: celular y redes (91% y 55% de hogares), centros de trabajo y escuelas. Evidencia: los SMS de recordatorio suben de 0.25 a 0.9 pp, más entre quienes votan poco (E7).
- *Indicador*: participación de 18 a 34 años; actualizaciones de domicilio.
Se debe verificar con datos de movilidad si el domicilio desactualizado es la causa; el dato censal solo muestra una alta proporción de población nacida en otra entidad.

### 3.2 Rezago juvenil urbano
**Quiénes y dónde.** El perfil más numeroso (29% de la lista nominal): Veracruz (48% de su lista nominal), Estado de México (47%), Aguascalientes (45%), Sinaloa (44%), Hidalgo (41%) y gran parte de León, Puebla y Culiacán. 76% urbano. **Participación**: 52% en promedio. **La mayor brecha entre jóvenes y adultos mayores** (−26 pp): los hombres de 25 a 34 años votan 39% y las mujeres 53%, frente a más de 77% en ambos sexos de 65 a 74 años. **Contexto**: 52% de hogares con internet, 88% con celular.
**Narrativa.** Territorios donde la participación depende de las generaciones mayores y se cae entre los menores de 45 años, especialmente los hombres jóvenes.
**Estrategia propuesta**:
- *Objetivo*: sumar a quienes tienen entre 18 y 34 años (1.3 millones de votos recuperables).
- *Mensaje*: relevancia local y concreta del voto y de los cargos que se eligen, con información práctica sobre el primer voto.
- *Canal*: redes sociales y celular; escuelas, universidades y espacios laborales.
- *Mensajeros*: pares y organizaciones juveniles.
- *Indicador*: brecha de jóvenes y participación de hombres de 25 a 34 años.

### 3.3 Rural con brecha masculina
**Quiénes y dónde.** 63% de secciones rurales: Zacatecas (28% de su lista nominal), San Luis Potosí (25%), Puebla (22%), Querétaro (21%) y Guerrero (21%). **Participación**: 60% en promedio (4 pp sobre el nivel nacional). **La mayor brecha de género** (19 pp): hombres de 25 a 34 años, 37%; mujeres, 63%; la brecha se cierra desde los 65 años. **Contexto**: la menor escolaridad (7.6 años), 13% con lengua indígena, solo 23% de hogares con internet y 15% con computadora; TV en 85% de los hogares, radio en 60%, celular en 77%; 9% sin radio ni TV.
**Narrativa.** Comunidades con baja conectividad donde los hombres en edad de trabajar casi no votan y las mujeres sí. **Se probó la hipótesis de que haya hombres en la lista nominal que ya no viven ahí (emigración) y no se sostiene**: la razón entre la lista nominal 2024 y la población residente de 18 años o más del Censo 2020 es igual para hombres y mujeres (1.17 y 1.17), y ajustar la lista de los hombres a la cobertura de las mujeres explicaría solo 10% de la brecha (16.9 pp pasan a 15.2 pp). Es una verificación de compatibilidad con datos del censo, no una medición de migración: no descarta ausencias temporales ni laborales. La causa de la brecha queda **sin explicar** y requiere otras fuentes o trabajo cualitativo antes de diseñar acciones sobre ella (`migracion_hipotesis.csv`).
**Estrategia propuesta**:
- *Objetivo*: entender y atender a los hombres de 25 a 44 años (0.8 millones de votos por brecha de género).
- *Mensaje*: información práctica sobre cómo, dónde y cuándo votar, dirigida a los hombres jóvenes y a sus familias.
- *Canal*: TV, radio local y comunitaria, actividades presenciales y mensajes a las familias (las mujeres, que votan 63%, como multiplicadoras). Evidencia: el contacto en persona tiene el efecto más alto documentado (≈4 pp entre contactados) y es el canal que llega donde solo 23% de los hogares tiene internet (E7).
- *Indicador*: participación de los hombres de 25 a 44 años.
- Antes de escalar, un piloto o estudio cualitativo en las secciones del perfil para identificar las barreras (por ejemplo, horario de trabajo el día de la elección).

### 3.4 Urbano de participación media-alta
**Quiénes y dónde.** 27% de la lista nominal: Ciudad de México (59% de su lista nominal), Tlaxcala (52%), Campeche (35%) y Yucatán (35%). **Participación**: 62% en promedio, con la menor brecha de género (8 pp) y los mayores logros educativos (11.1 años), 64% con internet y 11% de población de 65 años o más. **Participación 2024 de 75+**: mujeres 66%, hombres 72%.
**Narrativa.** Ciudadanía consolidada y conectada, donde el rezago está en las mujeres jóvenes.
**Estrategia propuesta**:
- *Objetivo principal*: mujeres de 25 a 34 años. Votan 63%, frente a 71% en el perfil 5, mientras que los hombres de esa edad están cerca de la referencia (53% frente a 55%; `acciones_celdas.csv`). Si votaran como las del perfil 5 se sumarían ≈0.20 millones de votos (2.4 millones × 8.3 pp). (Los 0.76 millones del criterio de género de la §6 miden otra cosa: hombres de 18 a 54 años que votan menos que las mujeres de su sección.)
- *Objetivo secundario*: accesibilidad para los adultos de 75 años o más (0.17 millones).
- *Mensaje*: información práctica (horario de la casilla, tiempo de espera) para mujeres con trabajo y cuidados a su cargo; información de accesibilidad.
- *Canal*: redes sociales y centros de trabajo; televisión e instituciones locales para los adultos mayores.
- *Indicador*: participación de las mujeres de 25 a 34 años y de las de 75 años o más.

### 3.5 Alta participación comunitaria
**Quiénes y dónde.** 44% de secciones rurales y 17% mixtas: Yucatán (43% de su lista nominal), Campeche (36%), Chiapas (30%), Zacatecas (28%) y Nuevo León (22%); 13% con lengua indígena. **Participación**: la más alta desde 2009 (52%) hasta 2024 (68%); **los jóvenes participan casi como los adultos** (brecha de −10 pp, la menor): hombres de 25 a 34 años, 55%; mujeres, 71%. El 75+ cae más (−15 pp frente a 55-74). **Contexto**: 36% con internet, 79% con celular, 86% con TV; 9% sin radio ni TV.
**Narrativa.** Comunidades con una cultura de participación que alcanza a todas las edades; el perfil de referencia para los demás.
**Estrategia propuesta**:
- *Objetivo*: sostener la participación y documentar qué la mantiene en los jóvenes (para replicarla en el perfil 2).
- *Mensaje*: reconocimiento y continuidad.
- *Canal*: TV, radio y liderazgos comunitarios.
- *Indicador*: participación de los 75+ (acceso físico).

## 4. Hallazgos transversales (nacionales, 2024)
- **Género**: las mujeres participan 64.2% y los hombres 54.8%. La brecha (+9 a +14 pp de 18 a 54 años) se invierte desde los 65 años. Es estable en las seis elecciones.
- **Edad**: el piso está en los 25-34 años (49.6%; los 18-24 votan 50.4%), no en los más jóvenes; el máximo, en 65-74 años (76.1%).
- **Quién falta**: los de 18 a 44 años son 66% de los no votantes y 57% de la lista nominal; los hombres de 25 a 44 años, 27% de los no votantes y 20% de la lista nominal.
- **Mujeres de 75 años o más**: participan menos que los hombres en los cinco perfiles (6 a 8 pp). Es el único hallazgo de edad con el mismo signo en todos los perfiles.
- **Intermitencia**: la caída en intermedias va de 6 a 18 pp según el ciclo, y es común a todos los perfiles (figura 6). Como el rasgo no persiste en cada territorio (§5), la recomendación es **campañas nacionales de movilización para las intermedias, sin focalizar por territorio**.

## 5. Calidad estadística
**Persistencia de los rasgos** (correlación entre ventanas disjuntas A = 2009-2015 y B = 2018-2024; `confiabilidad_rasgos.csv`):

Tasas sin encogimiento y todas las secciones; con encogimiento y el umbral de 800 registros de la tipología, las correlaciones suben a 0.69, 0.71 y 0.55 (§5.1).

| Rasgo | Secciones | Municipios | Uso |
|---|---|---|---|
| Nivel relativo | 0.70 | 0.67 | agrupación |
| Brecha de género 18-54 | 0.65 | 0.73 | agrupación |
| Brecha de jóvenes | 0.49 | 0.67 | agrupación |
| Caída de 75+ | 0.23 | 0.55 | descripción |
| Intermitencia | 0.28 | 0.07 | descripción; no se usa para focalizar |

**Validez temporal** (grupos construidos con 2009-2018; resultados de 2024; `validacion_tipologia.csv`). R² ponderado por registros entre secciones:

| Rasgo de 2024 | Grupos del pasado (k=5) | Grupos al azar | Estados (32) | Regresión lineal sobre los rasgos continuos |
|---|---|---|---|---|
| Nivel relativo | 0.32 | −0.01 | 0.27 | 0.56 |
| Brecha de jóvenes | 0.15 | 0.00 | 0.20 | 0.27 |
| Brecha de género 18-54 | 0.27 | 0.00 | 0.10 | 0.47 |
| Control: intermitencia 2024−2021 | 0.09 | −0.02 | 0.39 | 0.10 |

La validación usa ventanas sin elecciones comunes. Una primera versión (grupos con 2012-2021) daba 0.35 de R² para la intermitencia porque compartía el término 2021 con el resultado; era un artefacto y se corrigió.

**Comparación de métodos** (rasgos 2009-2018, validación cruzada por entidad, R² medio de los tres rasgos de 2024; `comparacion_segmentaciones.csv`): K-means 0.207 y árbol de decisión 0.209 con 5 segmentos; azar −0.03; regresión lineal sobre los rasgos continuos 0.404. **Segmentar descarta cerca de la mitad de la información predictiva** del continuo; por eso se publican también los tres rasgos continuos por sección y municipio para la planeación.
**Estructura de los datos** (`robustez_tipologia.csv`): la silueta de la solución (0.231) apenas supera la de datos sin grupos con la misma covarianza (0.221): es una **partición de un continuo**, no grupos naturales. Es insensible a decisiones de cálculo (encogimiento de 0 a 100 y umbrales de 400 a 1,500 registros: ARI de 0.88 a 1.00 frente a la solución base), pero las fronteras dependen del algoritmo (ARI con mezcla gaussiana 0.41 y con Ward 0.30) y entre ventanas de tiempo (ARI 0.36; 68% de las secciones conservan su perfil). Las conclusiones se apoyan en los **ejes** (nivel, género, jóvenes), no en los cortes exactos.
**Intervalos de las cifras de potencial**: remuestreo de municipios (500 réplicas); sensibilidad al punto de referencia: el potencial por nivel va de 4.1 millones (mediana de comparables) a 11.9 (percentil 90).

**Comparación de algoritmos con el mismo número de segmentos (k=5)** (mismo protocolo: rasgos 2009-2018, resultados 2024, validación cruzada por entidad; cada codificación predice por regresión lineal sobre sus pertenencias; `comparacion_algoritmos.csv`):

| Algoritmo | R² nivel | R² jóvenes | R² género | R² medio |
|---|---|---|---|---|
| K-means (pertenencia dura) | 0.25 | 0.13 | 0.24 | 0.21 |
| Árbol de decisión supervisado | 0.37 | 0.05 | 0.21 | 0.21 |
| K-means a nivel municipal | 0.05 | 0.04 | 0.16 | 0.08 |
| Mezcla gaussiana (pertenencias suaves) | 0.35 | 0.17 | 0.31 | 0.28 |
| Arquetipos (pertenencias suaves) | 0.52 | 0.24 | 0.45 | **0.40** |
| Cota: regresión sobre los 3 rasgos continuos | 0.52 | 0.24 | 0.45 | 0.40 |
| Cota: regresión sobre el perfil completo de 14 celdas (sexo × edad), 5 componentes principales | 0.52 | **0.37** | 0.42 | **0.44** |

- Los arquetipos igualan a la cota de los tres rasgos porque con cinco vértices las pertenencias reproducen exactamente la posición de la sección en el espacio de tres rasgos: **la pérdida de información viene de forzar una pertenencia dura**, no del algoritmo de agrupación. K-means a nivel municipal rinde mucho peor a nivel sección: la heterogeneidad interna de los municipios importa.
- El perfil completo de 14 celdas aporta información adicional sobre la brecha de jóvenes (0.37 frente a 0.24); queda pendiente segmentar sobre ese perfil (`PLAN.md`).
- Estabilidad entre ventanas (acuerdo tras emparejar segmentos): K-means 0.68, mezcla gaussiana 0.69, arquetipos 0.49 (en promedio una sección pertenece 36% a su arquetipo principal: las secciones son mezclas, no tipos puros).
- **¿Hay modos naturales?** HDBSCAN (mínimo 500 secciones) no encuentra ningún grupo (100% ruido); mean-shift con ancho de banda grueso encuentra 5 modos, resultado que depende de ese ancho. Es coherente con un continuo sin grupos separados.

**Limitaciones.** (1) Falacia ecológica en los descriptores del censo (escolaridad, internet, lengua indígena, migración). (2) El denominador es la lista nominal (ver §1). (3) Los perfiles son descriptivos, no causales; las estrategias son propuestas, sin efecto estimado. (4) Los votos recuperables son referencias contra secciones comparables (mismo tipo U/M/R), no pronósticos, y no consideran costo ni factibilidad; los criterios se solapan y no se suman. Sus intervalos solo reflejan el remuestreo de municipios; la incertidumbre dominante es el punto de referencia (§6), y donde la lista nominal incluye personas que ya no residen (norte, zonas de emigración) el potencial está sobreestimado. (5) Las secciones creadas después de 2015 no tienen las cuatro elecciones y quedan sin perfil.

## 5.1 Ruido, persistencia y valor sobre la geografía
`rigor_perfiles.py`: bootstrap paramétrico con 100 réplicas (cada celda sección × sexo × edad × elección se vuelve a muestrear como binomial con su tasa observada) y remuestreo de municipios para los contrastes.

**Ruido de muestreo frente a cambio real** (`rigor_confiabilidad.csv`). La confiabilidad es la proporción de la varianza entre secciones que no es ruido de muestreo:

| Rasgo | Confiabilidad (2009-2015 / 2018-2024) | Persistencia observada | Persistencia corregida por atenuación |
|---|---|---|---|
| Nivel | 0.99 / 0.99 | 0.69 | 0.70 |
| Brecha de género 18-54 | 0.82 / 0.85 | 0.71 | 0.85 |
| Brecha de jóvenes | 0.84 / 0.89 | 0.55 | 0.64 |
| Intermitencia | 0.95 / 0.94 | 0.29 | 0.31 |

Los rasgos están medidos con precisión. La persistencia incompleta del nivel y de la brecha de jóvenes es **cambio real** entre décadas, no error de medición. La intermitencia está bien medida y aun así no persiste: su exclusión del agrupamiento no se debe a ruido.

**Dónde ocurre el cambio** (`rigor_persistencia_niveles.csv`). La posición relativa de una sección dentro de su municipio persiste más (nivel: 0.77) que su posición nacional (0.69) y que el promedio de los municipios (0.67) o de los estados (0.58). La parte transitoria es, sobre todo, un desplazamiento de jurisdicciones completas entre elecciones. Coincide con el resultado del Reto 2: los choques de participación son municipales y estatales. En la práctica, **el orden de prioridad entre secciones de un mismo municipio o distrito es más confiable que el orden nacional**.

**Techo alcanzable en la validación** (`rigor_techo_r2.csv`). Con una sola elección como resultado, la proporción de la varianza de 2024 que no es ruido es 0.99 en el nivel, 0.72 en la brecha de género y 0.81 en la de jóvenes. Los R² de validación de §5 (0.32, 0.27 y 0.15) deben leerse contra ese techo. Por ejemplo, la segmentación captura el 38% de la varianza no aleatoria de la brecha de género de 2024, y los rasgos continuos, el 65%.

**Valor de los perfiles sobre la geografía** (`rigor_dentro_estado.csv`; perfiles construidos con 2009-2018, rasgos de 2024, R² ponderado en muestra; con ~2,400 efectos fijos de municipio sobre 64,000 secciones, el sobreajuste en muestra es del orden de 0.04, menor que el aporte del perfil):

| Rasgo de 2024 | Perfil | Estado | Estado + perfil | Municipio | Municipio + perfil |
|---|---|---|---|---|---|
| Nivel | 0.32 | 0.29 | 0.52 | 0.60 | 0.71 |
| Brecha de género | 0.27 | 0.11 | 0.33 | 0.46 | 0.54 |
| Brecha de jóvenes | 0.15 | 0.21 | 0.34 | 0.55 | 0.60 |

El perfil del pasado añade de 0.13 a 0.23 de R² por encima de los 32 estados, y de 0.05 a 0.11 por encima de los ~2,400 municipios. Contiene información sobre diferencias dentro de cada jurisdicción que la geografía administrativa no captura. En la brecha de jóvenes, el estado por sí solo explica más que el perfil, pero ambos son complementarios.

**Incertidumbre de la asignación** (`rigor_asignacion.csv`). Ante el ruido de muestreo, una sección cae en su mismo perfil en el 85% de las réplicas (mediana 93%), y el 69% de las secciones lo hace en al menos el 80%. La confianza es menor en el perfil 2 (64% de las secciones con confianza ≥ 0.8). Se publica la confianza de cada sección para que las Juntas prioricen las secciones con asignación firme.

**Contrastes con intervalos** (`rigor_contrastes.csv`). Las diferencias de cada celda sexo × edad con el perfil de referencia tienen IC95% de ±1 pp aproximadamente (remuestreo de municipios). Por ejemplo, las mujeres de 25 a 34 años del perfil 4 votan 8.3 pp menos que las del perfil 5 (IC95% de 7.5 a 9.2), y los hombres de 25 a 34 años del perfil 3, 18.0 pp menos (17.0 a 18.9).

## 5.2 Datos del INEGI: qué se usó y qué falta
- **Usado como descriptor** (Censo 2020 por sección, difundido por el INE en la ECEG): escolaridad, analfabetismo, lengua indígena, nacidos en otra entidad, internet, computadora, celular, radio, TV, TV de paga, población de 65 años o más y población de 18 a 24 (`tipologia_perfiles.csv`, `medios_perfiles.csv`); y por sexo, la población de 18+ (prueba de migración, §3.3). Cambio 2010-2020 en internet y celular (`medios_perfiles.csv`).
- **Probado en el Reto 2 sin mejora predictiva** (pero con valor descriptivo): DENUE (actividad económica), ECEG 2010 y su cambio, CONEVAL (pobreza, ingreso, seguridad social). No se han incorporado a la caracterización de los perfiles.
- **Pendiente** (`PLAN.md`): variables del censo desagregadas por sexo que ya están en la ECEG (escolaridad, ocupación e inactividad de hombres y mujeres), ENDUTIH (uso de internet por sexo y edad, a nivel estatal), Encuesta Nacional de Cultura Cívica (ENCUCI, INEGI-INE) y DENUE para la estructura económica local. Todas tienen resolución estatal o municipal y deben tratarse como descriptores, no como criterios de agrupación.

## 6. Potencial por perfil y por municipio
Votos por elección que se recuperarían (millones; IC95%; criterios no sumables; `politica_grupos_ic.csv`; figuras 4 y 5):

| Perfil | Nivel | Brecha de género (hombres 18-54) | Jóvenes 18-34 | 75+ |
|---|---|---|---|---|
| 1. Norte urbano | 3.55 (2.70-4.48) | 0.67 (0.54-0.80) | 1.45 (1.11-1.80) | 0.08 |
| 2. Rezago juvenil urbano | 2.73 (2.33-3.18) | 1.17 (0.99-1.38) | 1.30 (1.13-1.51) | 0.13 |
| 3. Rural con brecha masculina | 0.68 (0.62-0.76) | 0.81 (0.74-0.86) | 0.39 (0.35-0.43) | 0.08 |
| 4. Urbano medio-alto | 0.54 (0.47-0.62) | 0.76 (0.66-0.87) | 0.30 (0.27-0.34) | 0.17 |
| 5. Alta participación comunitaria | 0.22 (0.19-0.25) | 0.42 (0.39-0.45) | 0.08 (0.07-0.08) | 0.07 |
| **Total** | **7.73 (6.54-8.92)** | **3.82 (3.47-4.20)** | **3.52 (3.03-4.02)** | **0.54** |

**Municipios con mayor potencial** (miles de votos; `politica_municipios.csv`, `politica_distritos.csv`): por nivel, Tijuana (271), Juárez (257), Mexicali (160), León (137), Puebla (136), Zapopan, Culiacán y Ecatepec; por brecha de género, Iztapalapa (62), Ecatepec (57), León, Tijuana y Puebla; por jóvenes, Tijuana (104), Juárez (95), Mexicali (60), Hermosillo (51), Puebla y León. 61 municipios (2.5%) concentran la mitad del potencial por nivel.

## 7. Neutralidad
El INE es un organismo imparcial: la segmentación, la caracterización y las estrategias **no usan voto por partido ni resultados de partidos**. Los únicos datos externos a la CCPC son descriptores del Censo 2020 y 2010 por sección (ECEG, difundida por el INE), usados para describir los perfiles y no para formarlos.

## 8. Archivos
- Informe y figuras: `reports/INFORME.md`, `reports/fig/fig1` a `fig7`.
- Tipología y descripción: `tipologia_secciones.csv` (perfil por sección), `tipologia_perfiles.csv`, `tipologia_curvas_2024.csv`, `tipologia_historial.csv`, `tipologia_regiones.csv`, `tipologia_estados.csv`, `medios_perfiles.csv`, `reglas_segmentos.txt`.
- Calidad: `confiabilidad_rasgos.csv`, `elegir_k.csv`, `validacion_tipologia.csv`, `comparacion_segmentaciones.csv`, `robustez_tipologia.csv`, `tipologia_k.csv`.
- Política pública: `politica_grupos.csv`, `politica_grupos_ic.csv`, `politica_sensibilidad.csv`, `politica_municipios.csv`, `politica_distritos.csv`, `politica_secciones.csv`.
- Tablero para Juntas: `tablero.html` (abrir en cualquier navegador). Evidencia externa: `evidencia_intervenciones.md`.

## 9. Cierre del análisis (2026-10-12)

**E1, cambio de algoritmo: no se adopta.** Con el perfil completo de 14 celdas (sexo × edad), K-means da R² medio 0.15 y mezcla gaussiana 0.18, por debajo de los tres rasgos (0.40). Solo la regresión lineal sobre esas 14 celdas sube a 0.44, y la mejora (+0.03) está casi toda en la brecha de jóvenes (0.37 frente a 0.24). Se conserva la segmentación de tres rasgos; el perfil de 14 celdas se reporta como cota y como indicio de que la brecha de jóvenes tiene más detalle por sexo (`comparacion_algoritmos.csv`).

**E1b, diferenciación de los perfiles** (`diferenciacion_perfiles.csv`, `diferenciacion_centroides.csv`, `diferenciacion_eta2.csv`). Sobre rasgos estandarizados: η² de 0.61 en nivel, 0.55 en brecha de género y 0.55 en brecha de jóvenes. Distancia mínima entre centroides de 1.40 a 1.84 desviaciones estándar. Solo 11% de las secciones (ponderadas por lista nominal) están cerca de una frontera (distancia al segundo centroide ≤ 1.1 veces la del más cercano). La separación es moderada, no nula: los perfiles son diferenciables sin ser grupos naturales (§5).

**E2/E3, pertenencias suaves** (`tipologia_pertenencias.csv`). Cada sección recibe pesos de cinco arquetipos que suman 1 (el ajuste reproduce los tres rasgos con residuo medio de 0.012 DE). La pertenencia principal media es 0.36. La tabla cruzada con los perfiles K-means muestra que la mayoría de cada perfil cae en un arquetipo, pero los cortes no coinciden exactamente. Para planear, usar los pesos; para comunicar, los cinco perfiles.

**E4, descriptores del censo por sexo** (`descriptores_sexo.csv`, ECEG 2020, ponderados por lista nominal). Brechas relevantes por perfil:

| Perfil | Analfabetismo M / H | Escolaridad M / H (años) | PEA M / H | Inactivas M / H |
|---|---|---|---|---|
| 1. Norte urbano | 3.9% / 3.0% | 9.5 / 9.7 | 51% / 77% | 49% / 22% |
| 2. Rezago juvenil urbano | 5.2% / 3.5% | 9.4 / 9.6 | 50% / 76% | 50% / 24% |
| 3. Rural con brecha masculina | **11.6% / 8.7%** | **7.6 / 7.7** | **41% / 77%** | **59% / 22%** |
| 4. Urbano medio-alto | 3.9% / 2.6% | 10.9 / 11.3 | 51% / 73% | 49% / 26% |
| 5. Alta participación comunitaria | 9.2% / 6.9% | 8.5 / 8.7 | 43% / 76% | 57% / 24% |

La participación económica de los hombres es casi igual en los cinco perfiles (73-77%), así que no explica la brecha masculina del perfil 3. Lo que distingue al perfil 3 es la inactividad de las mujeres (59%, la mayor) y el analfabetismo de ambos sexos. Una lectura compatible, no probada: las mujeres del perfil 3 tienen más disponibilidad el día de la elección, y los hombres, que trabajan como en los demás perfiles, enfrentan barreras de horario o de traslado propias del medio rural. El piloto cualitativo de §3.3 debe distinguir ambas cosas.

**E6, cohortes aproximadas** (`cohortes.csv`). Se compara 18-24 años en la elección t con 25-34 años en t+6, siempre entre elecciones del mismo tipo (intermedia con intermedia, presidencial con presidencial). Es una aproximación de bandas, no un seguimiento individual. Cambio total: +0.3 pp (2009→2015), −0.4 pp (2012→2018), +3.3 pp (2015→2021) y −5.3 pp (2018→2024). No hay una tendencia sistemática de maduración de la cohorte: la brecha joven-adulto se mueve con el ciclo, no con la edad. En 2018→2024 cae más entre los hombres (−8.0 pp) que entre las mujeres (−2.7 pp). Un primer intento usaba t+9, pero eso cambia el tipo de elección y se descartó.

**E7, evidencia de intervenciones** (`evidencia_intervenciones.md`, cerrado el 2026-10-14). Cifras confirmadas en el texto de cada artículo. SMS de recordatorio: +0.9 pp en jóvenes de Finlandia (Hirvonen et al., 2025), +0.74 pp agrupado en Dinamarca (Bhatti et al., 2016), mayor en quienes votan poco. Segunda llamada: +1.2 pp (Huber et al., 2020). Visita domiciliaria: ≈4.3 pp entre contactados (síntesis de Gerber y Huber, 2016). En México, los volantes con información neutral por sección no movieron la participación y los de información de corrupción la redujeron 1.3 pp (Chong et al., 2015). Se retiró la cita a un metaanálisis de Mann y Haenschen (2024) que no se encontró. Implicaciones: mensajes prácticos y neutrales, contacto presencial en el perfil 3, y un piloto de al menos 1,000 secciones por brazo para mensajes masivos.

**E9, revisión de cifras.** Se cruzaron las cifras principales contra los CSV: 64,096 secciones, 91.8% de la lista nominal de 2024, potencial de 7.73 M (nivel), 3.82 M (género) y 3.52 M (jóvenes), y R² de validación (0.32, 0.15, 0.27 y 0.09). Todas coinciden con su fuente. Se corrigió la pertenencia principal a 36%.

**E8, tablero con mapa** (`tablero.html`, generado por `tablero.py`). Un solo archivo HTML (8.4 MB; Leaflet incrustado) que funciona sin servidor; sin conexión solo falta el mapa base. Mapa de distritos, municipios o secciones (cartografía electoral del INE) coloreado por perfil o por votos recuperables por 1,000 electores; un clic en un distrito o municipio baja a sus secciones. Además filtra por entidad, distrito, municipio, perfil y confianza de asignación; agrupa por distrito, municipio o sección; muestra la mezcla de perfiles y los votos recuperables por criterio; y descarga la selección en CSV. Sus totales nacionales coinciden con la §6.

## 10. Pendiente
Validación de las hipótesis de política con la DECEyEC y la DERFE (domicilio desactualizado en el perfil 1, accesibilidad para 75+), y la causa de la brecha masculina del perfil 3, que requiere trabajo cualitativo.
