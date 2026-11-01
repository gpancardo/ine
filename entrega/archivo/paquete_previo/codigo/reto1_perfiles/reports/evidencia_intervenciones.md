# Evidencia de intervenciones de movilización (E7, cerrado el 2026-10-14)

Propósito: respaldar las estrategias de `INFORME.md` §3 con evidencia experimental externa. Ninguna cifra de aquí se estima con los datos de la CCPC; el informe no afirma efectos de intervención. Cada cifra se confirmó en el texto del artículo (resultados o resumen) o en una síntesis escrita por los propios autores, como se indica.

| Intervención | Efecto (participación) | Fuente | Dónde se confirmó |
|---|---|---|---|
| **Volantes con información a nivel sección, México (Jalisco, Morelos, Tabasco, municipales 2009)** | Información de gasto o pobreza municipal (placebos): sin efecto. Información de corrupción: −1.3 pp (ee 0.32) sobre 52% de control; −7 pp con corrupción alta | Chong, De La O, Karlan y Wantchekon (2015), *Journal of Politics* 77(1): 55-71, doi:10.1086/678766 | Texto completo (sección de resultados; 2,360 secciones aleatorizadas) |
| SMS de recordatorio a jóvenes de 18-29 años (Finlandia, elecciones de condado 2022) | +0.9 pp sobre 30.8% de control; efecto mayor en votantes de baja propensión; derrame de ≈1.4 pp a familiares del mismo hogar | Hirvonen, Lassander, Sääksvuori y Tukiainen (2025), *Political Behavior*, doi:10.1007/s11109-024-09954-6 | Resultados del artículo |
| Cuatro experimentos de SMS (Dinamarca, >300,000 votantes) | Efecto agrupado +0.74 pp (rango 0.33-1.82) | Bhatti, Dahlgaard, Hansen y Hansen (2016), *Journal of Elections, Public Opinion and Parties* | Resumen del artículo |
| SMS masivo en EE. UU. (intermedias 2018, ≈7.1 millones de personas) | +0.25 pp | Haenschen y coautores, *Political Behavior* (2026) | **Solo nota de prensa de la universidad**; falta título y DOI. No citar en el documento técnico sin confirmarlo |
| Segunda llamada de recordatorio a personas ya contactadas (EE. UU.) | +1.2 pp | Huber, Gerber, Fang y Reardon (2020), *American Politics Research*, doi:10.1177/1532673X20935786 | Resumen del artículo |
| Correo con presión social (Michigan, primaria 2006, 180,002 hogares) | Control 29.7%; deber cívico 31.5%; "te estamos estudiando" 32.2%; tu historial 34.5%; historial de tus vecinos 37.8% | Gerber, Green y Larimer (2008), *American Political Science Review* 102(1): 33-48 | Sección de resultados |
| Síntesis de ≈200 experimentos (EE. UU.) | Visita domiciliaria: +4.3 pp entre contactados (51 experimentos; ≤1 pp sobre el grupo objetivo si se contacta a 25%); correo no partidista: <0.5 pp; llamada comercial: <1 pp; llamada de voluntario: ≈3 pp | Gerber y Huber (2016), *Stanford Social Innovation Review*, "Getting Out the Vote Is Tougher Than You Think" | Texto del artículo (síntesis de los autores, no metaanálisis revisado por pares) |

Se retiraron de la versión anterior: el "metaanálisis de Mann y Haenschen (2024)" (no se encontró; la cifra venía de un blog de proveedor), el experimento de Nueva Haven sin cifras, y el orden de autores de Huber et al. (estaba invertido).

## Implicaciones para las estrategias del informe
1. **Los mensajes masivos funcionan poco, pero son baratos y escalables.** SMS y correo mueven de 0.25 a 0.9 pp. Es el orden de magnitud que conviene esperar de una campaña de la DECEyEC por perfil, y coincide con el efecto mínimo detectable del piloto (`potencia_piloto.py`: 0.7-0.8 pp con ~1,000 secciones por brazo). Un piloto más chico no podría distinguir ese efecto del ruido.
2. **El efecto se concentra en los que menos votan** (Finlandia): esto respalda dirigir los mensajes a las celdas de baja participación (hombres de 25 a 34 años, perfiles 1 a 3), no a los perfiles que ya votan.
3. **El contacto personal es de 4 a 10 veces más eficaz que el masivo**, pero llega a pocas personas. Es la opción adecuada para el perfil 3 (rural, baja conectividad), donde las redes no llegan (23% de hogares con internet).
4. **Contenido neutral, sin información negativa.** En México, informar sobre corrupción *redujo* la participación, y la información neutral sobre el gasto no tuvo efecto. Esto respalda la recomendación de mensajes prácticos (cómo, dónde, cuándo), y evitar mensajes de desconfianza institucional.
5. **La presión social mueve mucho (+8 pp), pero no es apropiada para el INE**: exponer el historial de voto de los vecinos choca con la protección de datos y con la neutralidad del Instituto. Se menciona solo como cota superior.
6. **El experimento mexicano muestra que aleatorizar por sección y medir con datos oficiales es viable**: es el mismo diseño del piloto propuesto, y la CCPC permite medir el efecto por sexo y edad, algo que Chong et al. no podían hacer.

Ninguna de estas cifras proviene de un perfil de la tipología; en México solo existe evidencia sobre volantes informativos. Por eso las estrategias se presentan como hipótesis y se propone el piloto aleatorizado antes de escalar.
