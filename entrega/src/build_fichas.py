"""Genera las 5 fichas de perfil (HTML -> PNG 2160x2700 y un PDF). Cifras tomadas de reto1_perfiles/reports/INFORME.md.
Run: python3 entrega/src/build_fichas.py"""
import subprocess, pathlib
D = pathlib.Path(__file__).parent
P = [
 dict(n=1, c="#c2552c", nombre="Baja participación del norte urbano", lema="«Nadie vota mucho»", ic="city",
  ln="19.3 M (21%)", sec="11,330", part=44, gen=8, jov=-20, h=35, m=45, net=55, esc="9.6", pot="3.55",
  donde="Baja California, Chihuahua, Durango, Quintana Roo, Sonora. 77% urbano; 20% nació en otra entidad.",
  quien="Todas las edades votan menos que en el resto del país. Los hombres de 25 a 34 años votan 35%; las mujeres, 45%.",
  obj="Reducir la fricción práctica para votar, no solo informar.", msg="«Tu voto cuenta donde vives»: dónde votar y cómo actualizar el domicilio de la credencial.",
  canal="Celular y redes (91% de hogares con celular), centros de trabajo y universidades.", ind="Participación de 18 a 34 años y actualizaciones de domicilio.",
  falta="Si el domicilio desactualizado es la causa (verificar con la DERFE)."),
 dict(n=2, c="#d9a21b", nombre="Rezago juvenil urbano", lema="«Votan los padres, no los hijos»", ic="phone",
  ln="26.3 M (29%)", sec="17,349", part=52, gen=11, jov=-26, h=39, m=53, net=52, esc="9.5", pot="1.30",
  donde="Veracruz, Estado de México, Aguascalientes, Sinaloa, Hidalgo; gran parte de León, Puebla y Culiacán. 76% urbano.",
  quien="La mayor distancia entre jóvenes y mayores: personas de 65 a 74 años votan más de 77%; hombres de 25 a 34, 39%.",
  obj="Sumar a las personas de 18 a 34 años (1.3 M de votos recuperables).", msg="Relevancia local del voto y de los cargos; información del primer voto.",
  canal="Redes y celular, escuelas, universidades, espacios laborales; pares y organizaciones juveniles; adultos mayores como multiplicadores en casa.", ind="Brecha entre 18-34 y 55-74 años en las secciones del perfil.",
  falta="Es el perfil de asignación menos firme: recalcular con cada CCPC."),
 dict(n=3, c="#3d7d4f", nombre="Rural con brecha masculina", lema="«Votan ellas, no ellos»", ic="field",
  ln="10.4 M (12%)", sec="8,434", part=60, gen=19, jov=-22, h=37, m=64, net=23, esc="7.6", pot="0.68",
  donde="Zacatecas, San Luis Potosí, Puebla, Querétaro, Guerrero. 63% rural; 13% con lengua indígena.",
  quien="La mayor brecha de género: hombres de 25 a 34 años, 37%; mujeres, 64%. Se cierra desde los 65 años.",
  obj="Primero entender, luego actuar: hombres de 25 a 44 años (0.8 M de votos por brecha de género).", msg="Cómo, dónde y cuándo votar, dirigido a hombres jóvenes y sus familias.",
  canal="TV y radio local o comunitaria, contacto presencial; las mujeres que votan, como mensajeras en la familia.", ind="Participación de hombres de 25 a 44 años.",
  falta="La causa. La hipótesis de emigración se probó y explica solo 10% de la brecha."),
 dict(n=4, c="#2f6aa3", nombre="Urbano de participación media-alta", lema="«Consolidado, con mujeres jóvenes por debajo»", ic="tower",
  ln="24.6 M (27%)", sec="18,829", part=62, gen=8, jov=-20, h=53, m=62, net=64, esc="11.1", pot="0.54",
  donde="Ciudad de México, Tlaxcala, Campeche, Yucatán. La mayor escolaridad y conectividad.",
  quien="Los hombres votan casi como en el perfil 5 (53% frente a 55%); las mujeres de 25 a 34 años, 62% frente a 71% (−8 pp).",
  obj="Mujeres de 25 a 34 años (≈0.20 M de votos) y accesibilidad para 75 años o más.", msg="Horario de casilla y tiempos de espera para mujeres con trabajo y cuidados a su cargo.",
  canal="Redes sociales y centros de trabajo; televisión e instituciones locales para mayores.", ind="Participación de mujeres de 25 a 34 años y de 75 o más.",
  falta="Por qué las mujeres jóvenes votan menos: puede ser un efecto urbano."),
 dict(n=5, c="#7b4ea3", nombre="Alta participación comunitaria", lema="«La referencia»", ic="group",
  ln="9.6 M (11%)", sec="8,154", part=67, gen=11, jov=-10, h=55, m=71, net=36, esc="8.6", pot="0.22",
  donde="Yucatán, Campeche, Chiapas, Zacatecas, Nuevo León. 44% rural; 13% con lengua indígena.",
  quien="La participación más alta desde 2009 (68% en 2024); los jóvenes votan casi como los adultos.",
  obj="Sostener la participación y documentar qué la mantiene entre los jóvenes.", msg="Reconocimiento y continuidad; accesibilidad para 75 años o más.",
  canal="TV, radio y liderazgos comunitarios; entrevistas con autoridades comunitarias.", ind="Que se mantenga; participación de 75 años o más.",
  falta="La comparación es descriptiva: este perfil es más rural."),
]
TX = {"#c2552c":"#c2552c","#d9a21b":"#8a6200","#3d7d4f":"#3d7d4f","#2f6aa3":"#2f6aa3","#7b4ea3":"#7b4ea3"}
FG = {"#d9a21b":"#1d1d1b"}
ICON = {
 "city": '<path d="M8 56V24h14v32M22 56V10h16v46M38 56V30h14v26M4 56h56" /><path d="M27 18h6M27 28h6M27 38h6" />',
 "phone": '<rect x="20" y="6" width="24" height="48" rx="5"/><path d="M28 48h8"/><circle cx="32" cy="22" r="5"/><path d="M24 36c2-6 14-6 16 0"/>',
 "field": '<path d="M4 50c10-10 18-10 28 0s18 10 28 0"/><path d="M4 38c10-10 18-10 28 0s18 10 28 0"/><path d="M32 26V10M32 16l-6-4M32 16l6-4M32 22l-6-4M32 22l6-4"/>',
 "tower": '<path d="M30 56V14l2-8 2 8v42M18 56V30h12M34 56V24h12v32M4 56h56"/><path d="M26 34h2M26 42h2M38 32h4M38 40h4"/>',
 "group": '<circle cx="32" cy="20" r="7"/><circle cx="14" cy="26" r="5"/><circle cx="50" cy="26" r="5"/><path d="M18 52c0-12 28-12 28 0M2 52c0-8 12-10 16-6M62 52c0-8-12-10-16-6"/>',
}
CSS = """
*{box-sizing:border-box} body{margin:0;font-family:Arial,'Liberation Sans',sans-serif;color:#1b1b1b;background:#fff}
.f{width:1080px;height:1350px;position:relative;overflow:hidden;page-break-after:always;background:#fff;border:0}
.top{height:250px;padding:30px 56px;display:flex;gap:28px;align-items:center}
.top svg{width:130px;height:130px;fill:none;stroke:currentColor;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round;flex:none}
.k{font-size:24px;letter-spacing:.14em;text-transform:uppercase;opacity:.9}
.top h1{margin:4px 0 4px;font-size:44px;line-height:1.05} .top p{margin:0;font-size:30px;font-style:italic}
.body{padding:26px 56px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:26px}
.kpi{border:2px solid #e3e3e3;border-radius:14px;padding:14px 16px}.kpi b{display:block;font-size:44px;line-height:1}.kpi span{font-size:19px;color:#555}
.row{display:grid;grid-template-columns:1fr 1fr;gap:30px}
h2{font-size:22px;letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px}
p.t{font-size:23px;line-height:1.38;margin:0 0 14px}
.bar{height:34px;border-radius:6px;margin:6px 0;color:#fff;font-size:21px;font-weight:700;line-height:34px;padding-left:10px;white-space:nowrap}
.cap{font-size:19px;color:#555;margin:0 0 6px}
.est{border-radius:16px;padding:20px 24px;margin-top:6px}.est p{margin:0 0 9px;font-size:22px;line-height:1.35}
.foot{position:absolute;left:56px;right:56px;bottom:28px;font-size:17px;color:#666;display:flex;justify-content:space-between;border-top:2px solid #eee;padding-top:10px}
"""
import csv
CUR = {}
for r in csv.DictReader(open(D.parent.parent / "reto1_perfiles/reports/tipologia_curvas_2024.csv")):
    CUR[(int(r["c"]), int(r["SEXO"]))] = [float(r[k]) * 100 for k in ("18-24","25-34","35-44","45-54","55-64","65-74","75+")]
AGES = ["18-24","25-34","35-44","45-54","55-64","65-74","75+"]
def chart(p):
    W, H, L, B = 470, 205, 44, 30
    X = lambda i: L + i * (W - L - 18) / 6
    Y = lambda v: 14 + (90 - v) * (H - 14 - B) / 60
    g = "".join(f'<line x1="{L}" x2="{W-10}" y1="{Y(v)}" y2="{Y(v)}" stroke="#e6e6e6"/><text x="{L-8}" y="{Y(v)+5}" font-size="15" text-anchor="end" fill="#777">{v}</text>' for v in (30, 50, 70, 90))
    xs = "".join(f'<text x="{X(i)}" y="{H-10}" font-size="14" text-anchor="middle" fill="#777">{a}</text>' for i, a in enumerate(AGES))
    def line(sex, col, lab):
        v = CUR[(p["n"] - 1, sex)]
        pts = " ".join(f"{X(i)},{Y(x)}" for i, x in enumerate(v))
        dots = "".join(f'<circle cx="{X(i)}" cy="{Y(x)}" r="4" fill="{col}"/>' for i, x in enumerate(v))
        return f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="4"/>{dots}<text x="{X(0)+4}" y="{Y(v[0])+(-12 if sex==1 else 26)}" font-size="16" font-weight="700" fill="{col}">{lab}</text>'
    return f'<svg viewBox="0 0 {W} {H}" width="100%">{g}{xs}{line(0,"#555","Hombres")}{line(1,TX[p["c"]],"Mujeres")}</svg>'
def card(p):
    c = p["c"]; tint = c + "1f"; tx = TX[c]; fg = FG.get(c, "#fff")
    hb = f'<div class="bar" style="width:{p["h"]*1.3}%;background:#555">Hombres 25-34: {p["h"]}%</div>'
    mb = f'<div class="bar" style="width:{p["m"]*1.3}%;background:{tx}">Mujeres 25-34: {p["m"]}%</div>'
    return f'''<section class="f"><div class="top" style="background:{c};color:{fg}"><svg viewBox="0 0 64 64">{ICON[p["ic"]]}</svg>
<div><div class="k">Perfil {p["n"]} de 5</div><h1>{p["nombre"]}</h1><p>{p["lema"]}</p></div></div>
<div class="body"><div class="kpis">
<div class="kpi"><b>{p["part"]}%</b><span>participación media 2015-2024</span></div>
<div class="kpi"><b>{p["ln"].split(" ")[0]} M</b><span>de electores ({p["ln"].split("(")[1][:-1]} de la lista nominal)</span></div>
<div class="kpi"><b>{p["gen"]} pp</b><span>brecha de género 18-54 (mujeres − hombres)</span></div>
<div class="kpi"><b>{p["jov"]} pp</b><span>jóvenes 18-34 frente a 55-74 años</span></div></div>
<div class="row"><div><h2 style="color:{tx}">Quiénes y dónde</h2><p class="t">{p["quien"]}</p><p class="t">{p["donde"]}</p></div>
<div><h2 style="color:{tx}">Participación 2024, 25 a 34 años</h2>{mb}{hb}
<p class="cap" style="margin-top:10px">Participación 2024 por edad (%)</p>{chart(p)}
<p class="cap" style="margin-top:6px">Hogares con internet: {p["net"]}% · Escolaridad: {p["esc"]} años</p>
<p class="cap">Votos recuperables por nivel: {p["pot"]} M por elección</p></div></div>
<div class="est" style="background:{tint};border-left:8px solid {c};margin-top:20px"><h2 style="color:{tx}">Estrategia (hipótesis a probar)</h2>
<p><b>Objetivo.</b> {p["obj"]}</p><p><b>Mensaje.</b> {p["msg"]}</p><p><b>Canal.</b> {p["canal"]}</p><p><b>Indicador (CCPC 2027).</b> {p["ind"]}</p></div>
<p class="t" style="margin-top:16px"><b>Lo que aún no sabemos.</b> {p["falta"]}</p></div>
<div class="foot"><span>Fuente: CCPC 2009-2024 (INE) y Censo 2020. Datos agregados, sin datos personales.</span><span>Los perfiles son descriptivos, no causales.</span></div></section>'''
html = f'<!doctype html><meta charset="utf-8"><title>Fichas de perfil</title><style>@page{{size:1080px 1350px;margin:0}}{CSS}</style>' + "".join(card(p) for p in P)
(D / "fichas.html").write_text(html)
