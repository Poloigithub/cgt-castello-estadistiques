#!/usr/bin/env python3
"""
EPA per comarques de Castelló.

L'INE no publica l'EPA per comarca: les estimacions per "àrees petites" les
publica la GVA (PEGV/ARGOS) en pàgines HTML trimestrals (IMTNS). Aquest script
descobreix la pàgina del trimestre més recent, extrau les taxes d'activitat,
ocupació i atur (amb variació trimestral i anual) de les 8 comarques de Castelló
i les escriu dins data/epa.json (clau "comarques").

Si la font no és accessible, conserva les comarques anteriors i marca l'estat
com a "manual" a metadata.json.
"""
import html
import re
from datetime import datetime

from _common import DATA_DIR, load_existing, update_metadata, write_json
import requests

OUT = DATA_DIR / "epa.json"
SOURCE = "GVA-ARGOS (PEGV)"
URL_TPL = ("https://pegv.gva.es/auto/produccion/web/IMTNS/UC_{y}T{q}/"
           "ultimascifrasAREAS_{y}_{q}.htm")

# Nom a la pàgina PEGV -> nom de presentació (valencià) i ordre del document.
COMARQUES = [
    ("Els Ports", "Els Ports"),
    ("L'Alt Maestrat", "L'Alt Maestrat"),
    ("El Baix Maestrat", "El Baix Maestrat"),
    ("L'Alcalatén", "L'Alcalatén"),
    ("La Plana Alta", "La Plana Alta"),
    ("La Plana Baixa", "La Plana Baixa"),
    ("El Alto Mijares", "L'Alt Millars"),
    ("El Alto Palancia", "L'Alt Palància"),
]


def num(token: str):
    token = token.strip()
    if not token or "no disponible" in token.lower():
        return None
    m = re.search(r"-?\d+(?:,\d+)?", token)
    return float(m.group(0).replace(",", ".")) if m else None


def parse_block(text: str) -> dict:
    """Extreu les 3 taxes + variacions del text d'un data-title."""
    out = {}
    sections = {
        "activitat": r"Tasa de actividad(.*?)(?:Tasa de ocupaci|$)",
        "ocupacio": r"Tasa de ocupaci\w+(.*?)(?:Tasa de paro|$)",
        "desocupacio": r"Tasa de paro(.*?)$",
    }
    for key, pat in sections.items():
        m = re.search(pat, text, re.S)
        if not m:
            continue
        seg = m.group(1)
        tasa = re.search(r"Tasa:\s*([^\t\n%]+)%", seg)
        trim = re.search(r"trimestral:\s*([^\t\n(]+)", seg)
        anual = re.search(r"anual:\s*([^\t\n(]+)", seg)
        out[f"taxa_{key}"] = num(tasa.group(1)) if tasa else None
        out[f"var_trim_{key}"] = num(trim.group(1)) if trim else None
        out[f"var_anual_{key}"] = num(anual.group(1)) if anual else None
    return out


def find_latest_page():
    """Prova trimestres recents fins trobar una pàgina existent."""
    now = datetime.utcnow()
    q = (now.month - 1) // 3 + 1
    y = now.year
    for _ in range(8):
        url = URL_TPL.format(y=y, q=q)
        try:
            r = requests.get(url, timeout=30,
                             headers={"User-Agent": "cgt-castello-estadistiques"})
            if r.status_code == 200 and "Tasa de paro" in r.text:
                return url, r.content, f"{y}T{q}"
        except Exception:  # noqa: BLE001
            pass
        q -= 1
        if q == 0:
            q = 4
            y -= 1
    return None, None, None


def main() -> None:
    print("Comarques (PEGV/ARGOS): cercant la pàgina més recent...")
    prev = load_existing(OUT)
    try:
        url, content, periode = find_latest_page()
        if not content:
            raise RuntimeError("cap pàgina IMTNS recent accessible")
        h = content.decode("utf-8", errors="replace")

        # Cada cel·la de comarca porta un atribut data-title amb el detall.
        titles = re.findall(r'data-title="(.*?)"', h, re.S)
        decoded = []
        for t in titles:
            t = t.replace("&#010;", "\n").replace("&#009;", "\t")
            decoded.append(html.unescape(t))

        comarques = []
        for page_name, display in COMARQUES:
            # El nom apareix a la 1a línia, sovint amb un prefix numèric ("01 Els Ports").
            block = next((d for d in decoded if page_name in d.split("\n", 1)[0]), None)
            row = {"nom": display}
            if block:
                row.update(parse_block(block))
            comarques.append(row)

        found = sum(1 for c in comarques if c.get("taxa_activitat") is not None)
        if found == 0:
            raise RuntimeError("no s'ha pogut extraure cap taxa comarcal")

        epa = prev or {}
        epa["comarques"] = comarques
        epa["comarques_periode"] = periode
        write_json(OUT, epa)
        update_metadata("epa_comarques", periode, SOURCE, "ok")
        print(f"Comarques: desat ({found}/8 comarques, període {periode}).")
    except Exception as e:  # noqa: BLE001
        # Fallback: conserva o crea estructura placeholder.
        epa = prev or {}
        if not epa.get("comarques"):
            epa["comarques"] = [{"nom": d} for _, d in COMARQUES]
            epa["comarques_periode"] = None
            write_json(OUT, epa)
        update_metadata("epa_comarques", source=SOURCE, status=f"manual: {e}")
        print(f"Comarques: FALLBACK (placeholder) -> {e}")


if __name__ == "__main__":
    main()
