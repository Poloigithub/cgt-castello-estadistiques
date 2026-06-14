#!/usr/bin/env python3
"""
DIRCE — Directori Central d'Empreses.
Taula INE 4721 — Empreses per municipi i activitat principal.
Es desa la distribució per sector d'empreses de Castelló de la Plana.
"""
from _common import (DATA_DIR, fetch_ine, find_one, load_existing, period_label,
                     update_metadata, write_json)

OUT = DATA_DIR / "empreses.json"
SOURCE = "INE-DIRCE"
URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/4721?nult=1"

MUNI = "Castelló de la Plana. Total. Total de empresas. "

# clau -> fragment del nom de la categoria CNAE a l'INE
SUBSECTORS = [
    ("comerc_transport_hostaleria", "Comercio al por mayor"),
    ("informacio_comunicacions", "Información y comunicaciones"),
    ("financeres_assegurances", "Actividades financieras"),
    ("immobiliaries", "Actividades inmobiliarias"),
    ("professionals_administratives", "Actividades profesionales"),
    ("educacio_sanitat_socials", "Secciones P y Q"),
    ("oci_altres_serveis", "Secciones R y S"),
]


def val(series):
    if not series:
        return None
    data = series.get("Data") or []
    return data[0]["Valor"] if data else None


def main() -> None:
    print("Empreses (DIRCE): descarregant de l'INE (taula 4721)...")
    try:
        table = fetch_ine(URL)
        total_s = find_one(table, MUNI + "Total CNAE.")
        industria = val(find_one(table, MUNI + "Industrias extractivas"))
        construccio = val(find_one(table, MUNI + "Construcción. Empresas"))
        total = val(total_s)
        serveis = round(total - (industria or 0) - (construccio or 0)) if total else None

        subsectors = {}
        for key, frag in SUBSECTORS:
            subsectors[key] = val(find_one(table, MUNI + frag))

        period = period_label((total_s.get("Data") or [{}])[0]) if total_s else None
        out = {
            "periode": period,
            "ambit": "Castelló de la Plana (municipi)",
            "total": total,
            "sectors": {
                "industria": industria,
                "construccio": construccio,
                "serveis": serveis,
            },
            "subsectors_serveis": subsectors,
        }
        write_json(OUT, out)
        update_metadata("empreses", period or "?", SOURCE, "ok")
        print(f"Empreses: desat ({period}, total {total}).")
    except Exception as e:  # noqa: BLE001
        if not load_existing(OUT):
            write_json(OUT, {"total": None, "sectors": {}})
        update_metadata("empreses", source=SOURCE, status=f"error: {e}")
        print(f"Empreses: ERROR -> {e}")
        raise


if __name__ == "__main__":
    main()
