# /// script
# dependencies = ["requests"]
# ///
"""Fuentes adicionales (idempotente). Run: uv run shared/download_extra.py
  - ECEG 2010 nacional (Censo 2010 sobre marco seccional 2016), INE cartografía
  - DENUE por entidad (INEGI, directorio de unidades económicas con coordenadas)
  - SESNSP incidencia delictiva municipal 2015-2025 (enlace SharePoint público convertido a download.aspx)
  - Magar (github.com/emagar/elecRetrns): casillas de diputados federales 1991-2024, elecciones municipales y de gubernatura (concurrencia, titulares)
  - INE Revocación de Mandato 2022 por casilla (computosrm2022.ine.mx)
  - INE fiscalización: gasto de campaña por candidato 2018, 2021, 2024 (fiscalizacion.ine.mx, descarga de reportes; los enlaces llevan un UUID y pueden cambiar)"""
import sys
from pathlib import Path
import requests
RAW = Path("data/raw"); S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"

def get(url, dest, min_bytes=100_000):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > min_bytes: return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = S.get(url, timeout=600, stream=True)
    if r.status_code != 200 or "text/html" in r.headers.get("content-type", ""):
        print(f"[WARN] no disponible: {url}"); return False
    tmp = dest.with_suffix(dest.suffix + ".part")
    with open(tmp, "wb") as f:
        for ch in r.iter_content(1 << 20): f.write(ch)
    if tmp.stat().st_size < min_bytes: tmp.unlink(); print(f"[WARN] archivo muy pequeño: {url}"); return False
    tmp.rename(dest); print("ok", dest, f"{dest.stat().st_size / 1e6:.1f} MB"); return True

if __name__ == "__main__":
    get("https://cartografia.ine.mx/mapoteca/estadisticos/ECEG/2010/ECEG%202010%20Nacional.xlsx", RAW / "eceg2010" / "ECEG_2010_Nacional.xlsx")
    get("https://sspcgob-my.sharepoint.com/personal/cni_sspc_gob_mx/_layouts/15/download.aspx?share=IQCIHz1ZZoXjRZ3IySsQQqgFAYKdzEOXXK1YXfhhEhyDMcs", RAW / "sesnsp" / "municipal_2015_2025.zip")
    names = {e: [f"denue_{e:02d}"] for e in range(1, 33)}; names[15] = ["denue_15_1", "denue_15_2"]  # Edomex viene partido en dos archivos
    missing = [e for e, ns in names.items() if not all(get(f"https://www.inegi.org.mx/contenidos/masiva/denue/{n}_csv.zip", RAW / "denue" / f"{n}.zip", 500_000) for n in ns)]
    MG = "https://raw.githubusercontent.com/emagar/elecRetrns/master/data/"
    for y in [1991, 1994, 1997, 2000, 2003, 2006, 2009, 2012, 2015, 2018, 2021, "2024-pre-trife"]:
        get(f"{MG}casillas/dip{y}.csv", RAW / "magar" / f"dip{y}.csv", 1_000_000)
    for f in ["aymu1970-on", "aymu1989-on.concurrence", "aymu1989-on.incumbents", "goed1961-on", "goed1970-on.incumbents"]:
        get(f"{MG}{f}.csv", RAW / "magar_mun" / f"{f}.csv", 10_000)
    get("https://computosrm2022.ine.mx/20220411_1845_REVOCACION_MANDATO_2022.zip", RAW / "rm2022" / "20220411_1845_REVOCACION_MANDATO_2022.zip", 1_000_000)  # extraer en data/raw/rm2022/x/
    SIF = "https://fiscalizacion.ine.mx/documents/82565/"
    for dest, path in {"g2018": "1140143/CF3-Anexo-Gasto-por-Rubro-Campa%C3%B1a-FEDERAL_2018_07_17.csv/a70dc932-941e-4a11-b0dd-aa903ea080f8", "oyg2018": "1140143/CF1-Anexo-Operaciones-de-Ingreso-y-Gasto-Campa%C3%B1a-FEDERAL_2018_07_17.csv/4590c66c-0632-4156-a7c2-172078990729",
                       "g2021": "1140143/PEFO_20-21_CAMPA%C3%91A_G_RUBRO.csv/94d5f1de-9ddd-4688-a595-b572a816ac2c", "oyg2021": "1140143/PEFO_20-21_CAMPA%C3%91A_OYG.csv/10b4e491-ea9a-4420-a1eb-033c593cd0b6",
                       "g2024": "1268544/PREFO_23-24_CAM_GxR_240624.csv/cce0750a-e105-4837-a339-dc581fdbe210", "oyg2024": "1268544/PREFO_23-24_CAM_OYG_240624.csv/1cd2ace9-0d47-40b1-bfc8-9ebce33205da"}.items():
        get(SIF + path, RAW / "sif" / f"{dest}.csv", 100_000)
    print("DENUE faltantes (revisar nombre de archivo en inegi.org.mx/app/descarga):", missing)
