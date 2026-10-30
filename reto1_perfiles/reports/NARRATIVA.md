# Narrativa de los perfiles (borrador de trabajo, 2026-10-12)

Insumo para el documento técnico y las fichas. Este documento no es un entregable. Las cifras provienen de `INFORME.md` y de `acciones_perfiles.py` (`acciones_celdas.csv` y `acciones_distritos.csv`). Datos de 2024, salvo que se indique otra cosa.

## 0. Qué sostiene la estadística y qué no
| Afirmación de la narrativa | Respaldo (INFORME §5 y §5.1) | Fuerza |
|---|---|---|
| Los rasgos están bien medidos | Confiabilidad frente al ruido de muestreo: 0.99 (nivel), 0.82-0.85 (género), 0.84-0.89 (jóvenes) | Sólida |
| Los tres ejes son rasgos estables de cada territorio | Persistencia entre décadas corregida por ruido: 0.70, 0.85 y 0.64; dentro de cada municipio, 0.77 en el nivel | Sólida para nivel y género; moderada para jóvenes |
| Los perfiles aportan más que la geografía | Construidos con 2009-2018, añaden de 0.13 a 0.23 de R² sobre 2024 por encima del estado y de 0.05 a 0.11 por encima del municipio | Sólida |
| Los cinco perfiles se distinguen entre sí | η² de 0.55 a 0.61; contrastes por celda con IC95% de ±1 pp; k=5 es el más estable en el rango de 4 a 6 | Moderada: cortes de un continuo, no grupos naturales |
| Una sección está bien asignada | Mismo perfil en el 85% de las réplicas bootstrap; 69% de las secciones con confianza ≥ 0.8; 68% conserva el perfil entre décadas | Moderada: se publica la confianza de cada sección |
| Las estrategias tendrán efecto | Ninguno con estos datos; la evidencia experimental externa (E7, verificada) indica 0.25-0.9 pp para mensajes masivos y ≈4 pp por persona contactada en visitas | **Hipótesis.** Por eso se propone un piloto con medición |

Regla de redacción que se deriva de esta tabla: los perfiles se presentan como **prioridades de atención** con evidencia de persistencia, y las estrategias como **hipótesis a probar**. No se afirma que una estrategia "aumentará" la participación.

## 1. Hilo conductor
1. **El faltante es el mismo en todo el país.** En los cinco perfiles, el grupo con más no votantes son los **hombres de 25 a 34 años** (del 15% al 18% de los no votantes de cada perfil), seguidos por los hombres de 35 a 44 y de 18 a 24 años y por las mujeres de 25 a 34. A escala nacional, los hombres de 25 a 44 años son el 27% de quienes no votan y el 20% de la lista nominal.
2. **Lo que cambia entre territorios es la intensidad del faltante y su forma.** En el norte urbano todos votan menos; en las ciudades del centro, el faltante se concentra en los jóvenes; en el campo, en los hombres; en las ciudades consolidadas, en las mujeres jóvenes; y en las comunidades de alta participación, apenas existe.
3. **El perfil 5 sirve de referencia.** Los otros cuatro perfiles se comparan con lo que ya ocurre en secciones mexicanas reales (columna "frente al perfil 5"). La comparación es descriptiva: el perfil 5 es más rural, y parte de la diferencia puede deberse a eso.
4. **Lo que no es territorial se atiende a escala nacional.** La caída en las elecciones intermedias (6 a 18 pp) ocurre en todos los perfiles y no persiste por territorio. 2027 es una elección intermedia, así que la movilización de ese año debe ser nacional, y los perfiles indican **a quién y cómo** dirigirse dentro de esa campaña.

## 2. Los perfiles

Formato de cada ficha: quiénes son, dónde están, a quién dirigirse, qué hacer, cómo medirlo y qué se desconoce. "Frente al perfil 5" es la diferencia, en puntos porcentuales, con la misma celda de sexo y edad en el perfil 5.

### Perfil 1. Baja participación del norte urbano: "Nadie vota mucho"
- **Quiénes**: 19.3 millones de electores (21% de la lista nominal) en 11,330 secciones; 77% urbanas, con 20% de población nacida en otra entidad. Participación media 2015-2024: 44%, la más baja en todas las elecciones desde 2009 y en todas las edades.
- **Dónde**: es mayoritario en 46 distritos federales; 18 de ellos concentran la mitad del potencial (Chihuahua 3 y 2, Baja California 6 y 5, Sonora 2). Municipios: Tijuana, Juárez y Mexicali.
- **A quién**: hombres de 25 a 34 años (votan 35%; −20 pp frente al perfil 5) y mujeres de 25 a 34 (45%; −26 pp). Es el único perfil en que las mujeres jóvenes se alejan de la referencia más que los hombres.
- **Qué hacer** (hipótesis):
  - Recordatorios prácticos sobre dónde votar ("tu casilla"), con difusión en celular y redes (91% de los hogares tienen celular y 55%, internet).
  - Coordinación de las Juntas Distritales con los Módulos de Atención Ciudadana para promover la actualización del domicilio en la credencial. Antes, se debe comprobar con la DERFE si la credencial con domicilio desactualizado es frecuente en estas secciones: el censo solo muestra alta proporción de población nacida en otra entidad.
  - Presencia en centros de trabajo de la industria maquiladora y en universidades.
- **Indicador (CCPC 2027)**: participación de 18 a 44 años en las secciones del perfil, comparada con la de 2021 (intermedia con intermedia).
- **Potencial de referencia**: 3.55 millones de votos por nivel (IC95% 2.70-4.48).
- **Qué se desconoce**: si la causa es la movilidad residencial, el desinterés o la falta de oferta política local.

### Perfil 2. Rezago juvenil urbano: "Votan los padres, no los hijos"
- **Quiénes**: el perfil más numeroso, con 26.3 millones de electores (29%) en 17,349 secciones; 76% urbanas. Participación media: 52%. Tiene la mayor brecha entre jóvenes y adultos mayores (−26 pp): las personas de 65 a 74 años votan más de 77% y los hombres de 25 a 34, 39%.
- **Dónde**: es mayoritario en 92 distritos, la mayor huella territorial; 32 de ellos concentran la mitad del potencial juvenil. Estados: Veracruz, Estado de México, Aguascalientes, Sinaloa e Hidalgo.
- **A quién**: hombres de 25 a 34 años (39%; −16 pp frente al perfil 5) y mujeres de 25 a 34 (53%; −18 pp). Son la primera y la segunda celda con más no votantes del país: 1.7 y 1.3 millones.
- **Qué hacer** (hipótesis):
  - Información sobre el primer voto y el voto joven en preparatorias y universidades, en coordinación con la autoridad educativa.
  - Mensajes con pares como mensajeros, a través de organizaciones juveniles.
  - **Usar a los adultos mayores, que sí votan, como multiplicadores dentro del hogar** ("lleva a tu hijo a votar"). Se trata de una hipótesis derivada del contraste de edades, no de evidencia.
- **Indicador**: brecha entre jóvenes de 18 a 34 años y adultos de 55 a 74 en las secciones del perfil.
- **Potencial de referencia**: 1.30 millones de votos por jóvenes (1.13-1.51).
- **Qué se desconoce**: es el perfil con más secciones cerca de una frontera (13%), y la brecha de jóvenes es el eje menos persistente (r = 0.49). Su lista de secciones debe recalcularse con cada CCPC.

### Perfil 3. Rural con brecha masculina: "Votan ellas, no ellos"
- **Quiénes**: 10.4 millones de electores (12%) en 8,434 secciones; 63% rurales y 13% con hablantes de lengua indígena. Participación media: 60%. Tiene la mayor brecha de género (19 pp): los hombres de 25 a 34 años votan 37% y las mujeres, 64%. El 77% de los hombres es económicamente activo.
- **Dónde**: es mayoritario en 39 distritos; 17 concentran la mitad del potencial (Guanajuato 1 y 2, Guerrero 5, Aguascalientes 1, Estado de México 9). Estados: Zacatecas, San Luis Potosí, Puebla, Querétaro y Guerrero.
- **A quién**: hombres de 18 a 44 años. Los de 25 a 34 años representan el 18% de los no votantes del perfil, la mayor concentración de los cinco perfiles; su participación está 18 pp por debajo del perfil 5. Las mujeres de la misma edad están solo 7 pp por debajo.
- **Qué hacer** (hipótesis):
  - **Primero entender, luego actuar.** Un estudio cualitativo breve de las Juntas Distritales en algunas secciones del perfil, con preguntas sobre el horario de trabajo del domingo, el trabajo fuera de la comunidad y la distancia a la casilla.
  - Mensajes por TV y radio local o comunitaria (solo 23% de los hogares tiene internet), con las mujeres que votan como mensajeras dentro de la familia.
  - Si se confirma la barrera del horario de trabajo, mensajes sobre el horario de la casilla y acuerdos con empleadores locales.
- **Indicador**: participación de los hombres de 25 a 44 años.
- **Potencial de referencia**: 0.81 millones de votos por brecha de género (0.74-0.86).
- **Qué se desconoce**: la causa. La hipótesis de los emigrantes que siguen en la lista nominal se probó y no se sostiene (explica 10% de la brecha).

### Perfil 4. Urbano de participación media-alta: "Ciudadanía consolidada, con mujeres jóvenes por debajo"
- **Quiénes**: 24.6 millones de electores (27%) en 18,829 secciones; 80% urbanas, con la mayor escolaridad (11.1 años) y la mayor conectividad (64% con internet). Participación media: 62%. Estados: Ciudad de México, Tlaxcala, Campeche y Yucatán.
- **Dónde**: es mayoritario en 88 distritos.
- **A quién** (corrige el informe): los hombres de este perfil votan casi como los del perfil 5 (25 a 34 años: 53% frente a 55%). La diferencia está en las **mujeres de 25 a 34 años** (63% frente a 71%; −8 pp). Su brecha de género es pequeña porque las mujeres jóvenes votan menos, no porque los hombres voten más. Si las mujeres de 25 a 34 años votaran como las del perfil 5 se sumarían ≈0.20 millones de votos (2.4 millones × 8.3 pp), más que los adultos de 75 años o más (0.17 millones). Los 0.76 millones del criterio de género corresponden a otra cosa: los hombres de 18 a 54 años que votan menos que las mujeres de su sección, una brecha común a todos los perfiles.
- **Qué hacer** (hipótesis):
  - Información práctica dirigida a mujeres jóvenes con trabajo y cuidados a su cargo (horario de casilla, tiempo de espera), en redes sociales y centros de trabajo.
  - Mantener la línea de accesibilidad para personas de 75 años o más (las mujeres de 75+ votan 66%, frente a 72% de los hombres).
- **Indicador**: participación de las mujeres de 25 a 34 años y de las mujeres de 75 años o más.
- **Qué se desconoce**: por qué las mujeres jóvenes de este perfil votan menos que las del perfil 5. Puede ser un efecto urbano y no algo propio del perfil.

### Perfil 5. Alta participación comunitaria: "El perfil de referencia"
- **Quiénes**: 9.6 millones de electores (11%) en 8,154 secciones; 44% rurales y 17% mixtas, con 13% de hablantes de lengua indígena. Tiene la participación más alta en cada elección desde 2009 (68% en 2024) y la menor brecha de jóvenes (−10 pp).
- **Dónde**: es mayoritario en 35 distritos. Estados: Yucatán, Campeche, Chiapas, Zacatecas y Nuevo León.
- **A quién**: no es prioridad de movilización. Su caída más marcada está en los mayores de 75 años (−15 pp frente a 55-74), atribuible al acceso físico.
- **Qué hacer**:
  - **Documentar qué sostiene la participación de sus jóvenes**: entrevistas de las Juntas Distritales con autoridades comunitarias y personas funcionarias de casilla. Lo aprendido alimenta los mensajes de los perfiles 2 y 4.
  - Facilitar el voto de las personas de 75 años o más (acompañamiento, información de accesibilidad).
- **Indicador**: que la participación se mantenga, y la participación de 75+.

## 3. Mensajes transversales
- **Hombres de 25 a 44 años**: son el faltante común a todos los perfiles. Pueden atenderse con una línea nacional de mensajes cuyo canal se adapte al perfil: redes en los perfiles 1, 2 y 4, y radio y TV locales en los perfiles 3 y 5.
- **Elección intermedia**: la movilización es nacional y no se focaliza por territorio, porque la intermitencia no persiste en cada sección.
- **Mujeres de 75 años o más**: votan entre 6 y 8 pp menos que los hombres de su edad en los cinco perfiles; es el único hallazgo de edad con el mismo signo en todos. La acción corresponde a la accesibilidad de las casillas.

## 4. Cómo se vuelve proyecto del INE
1. **Clasificar**: ocho reglas con umbrales (`reglas_segmentos.txt`; fidelidad de 78% validada por entidad) asignan cualquier sección a un perfil con su CCPC. No requieren software ni datos personales.
2. **Distribuir**: cada Junta Distrital recibe su perfil mayoritario, la lista de secciones con su confianza de asignación (`rigor_asignacion.csv`) y las celdas de sexo y edad a priorizar (`acciones_distritos.csv` y `politica_distritos.csv`). Entre 11 y 32 distritos concentran la mitad del potencial de cada perfil, lo que permite empezar por pocos. El orden de prioridad entre secciones de un mismo municipio es más estable que el orden nacional (persistencia 0.77 frente a 0.69), así que la priorización debe hacerse dentro de cada jurisdicción.
3. **Probar en 2027**: un piloto aleatorizado por sección dentro del perfil, medido con la CCPC 2027.
   - Con 250 secciones por brazo, el efecto mínimo detectable en una intermedia es de 1.4 a 1.7 pp; con 1,000, de 0.7 a 0.8 pp (`potencia_piloto.csv`).
   - Los efectos experimentales de los mensajes masivos son de 0.25 a 0.9 pp entre las personas que los reciben (SMS en Finlandia, Dinamarca y EE. UU.; `evidencia_intervenciones.md`). Medido sobre toda la sección, el efecto se diluye en proporción a la cobertura: si el mensaje llega a la mitad de la lista nominal, un efecto de 0.9 pp se vuelve ≈0.45 pp. Por eso, **un piloto de mensajes requiere al menos 1,000 secciones por brazo y medir el resultado en la celda objetivo** (por ejemplo, hombres de 25 a 44 años), donde se concentra el efecto; con 250 solo detectaría intervenciones presenciales.
   - En México ya se aleatorizaron volantes por sección (Chong et al., 2015, 2,360 secciones): el diseño es factible, la información neutral no tuvo efecto y la información negativa redujo la participación. Los mensajes del piloto deben ser prácticos y neutrales.
4. **Actualizar**: los perfiles se recalculan con cada publicación de la CCPC. Las reglas se mantienen salvo que la fidelidad caiga.

## 5. Salvaguardas para el texto
- **Neutralidad**: el voto por partido no aparece en las fichas ni en las estrategias.
- **Falacia ecológica**: "las secciones del perfil 3 tienen baja escolaridad" es correcto; "los hombres que no votan tienen baja escolaridad" no lo es.
- **Nombres de perfil**: describen la participación, no estigmatizan. Se debe evitar presentar el perfil 1 como "apático".
- **Potencial**: es una referencia frente a secciones comparables, no una meta ni un pronóstico. Los criterios no se suman.

## 6. Pendientes para cerrar la narrativa
- Confirmar con la DERFE la hipótesis del domicilio desactualizado (perfil 1) antes de presentarla como acción.
- Revisar los nombres y las frases de los perfiles con alguien de comunicación (las fichas son iconográficas).
