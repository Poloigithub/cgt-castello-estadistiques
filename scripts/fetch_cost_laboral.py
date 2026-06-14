#!/usr/bin/env python3
"""
Cost Laboral — Enquesta Trimestral de Cost Laboral (ETCL).
Taula INE 6061 — Cost laboral per treballador, comunitat autònoma i sector.
Àmbits: Comunitat Valenciana i Total Nacional. Sectors: Indústria, Construcció, Serveis.
"""
from _common import (DATA_DIR, fetch_ine, find_one, load_existing, period_label,
                     update_metadata, variations, write_json)

OUT = DATA_DIR / "cost_laboral.json"
SOURCE = "INE-ETCL"
URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/6061?nult=6"

SECTORS = [("industria", "Industria"), ("construccio", "Construcción"), ("serveis", "Servicios")]
AMBITS = [("comunitat_valenciana", "Comunitat Valenciana"), ("espanya", "Total Nacional")]


def val(series, idx=0):
    if not series:
        return None
    data = series.get("Data") or []
    return data[idx]["Valor"] if len(data) > idx else None


def concept(table, ambit, sector, concepte):
    # "<ambit>. <sector>. <concepte>. Costes laborales. Euros."
    s = find_one(table, ambit + ".", ". " + sector + ".", concepte + ". Costes laborales")
    if s is None and ambit == "Total Nacional":
        s = find_one(table, "Nacional.", ". " + sector + ".", concepte + ". Costes laborales")
    return s


def main() -> None:
    print("Cost laboral: descarregant de l'INE (taula 6061)...")
    try:
        table = fetch_ine(URL)
        period = None
        out = {}
        for akey, alabel in AMBITS:
            out[akey] = {}
            for skey, slabel in SECTORS:
                total = concept(table, alabel, slabel, "Coste laboral total")
                salarial = concept(table, alabel, slabel, "Coste salarial total")
                altres = concept(table, alabel, slabel, "Otros costes")
                if period is None and total and total.get("Data"):
                    period = period_label(total["Data"][0])
                var = variations(total)
                out[akey][skey] = {
                    "cost_total": val(total),
                    "cost_salarial": val(salarial),
                    "altres_costos": val(altres),
                    "var_trim_total": var.get("var_trim"),
                    "var_anual_total": var.get("var_anual"),
                }
        out["periode"] = period
        write_json(OUT, out)
        update_metadata("cost_laboral", period or "?", SOURCE, "ok")
        print(f"Cost laboral: desat ({period}).")
    except Exception as e:  # noqa: BLE001
        if not load_existing(OUT):
            write_json(OUT, {"comunitat_valenciana": {}, "espanya": {}})
        update_metadata("cost_laboral", source=SOURCE, status=f"error: {e}")
        print(f"Cost laboral: ERROR -> {e}")
        raise


if __name__ == "__main__":
    main()
