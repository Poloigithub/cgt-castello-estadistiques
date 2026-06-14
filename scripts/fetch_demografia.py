#!/usr/bin/env python3
"""
Demografia — Padró municipal (Cifras Oficiales de Población, INE).
Taules INE:
  2865 — Castellón/Castelló: Població per municipis i sexe (municipi 12040 + total província)
  2853 — Població per comunitats i ciutats autònomes i sexe (Comunitat Valenciana)

Els indicadors de Cens (edat mitjana, índex de dependència, % estrangers, nivell
d'estudis, llars) no tenen API anual estable: es mantenen com a bloc manual amb el
seu període de referència i s'actualitzen a mà.
"""
from _common import (DATA_DIR, fetch_ine, find_one, load_existing, period_label,
                     update_metadata, write_json)

OUT = DATA_DIR / "demografia.json"
SOURCE = "INE / GVA-ARGOS"
T_MUNI = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2865?nult=2"
T_CCAA = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2853?nult=2"

# Superfície en km² per a la densitat (font: IGN/INE).
AREA_MUNICIPI = 108.78  # Castelló de la Plana


def vals(series):
    return [it["Valor"] for it in (series.get("Data") or [])] if series else []


def block(series):
    v = vals(series)
    actual = v[0] if v else None
    anterior = v[1] if len(v) > 1 else None
    var = round(actual - anterior, 0) if (actual is not None and anterior is not None) else None
    var_pct = round((actual - anterior) / anterior * 100, 2) if (var is not None and anterior) else None
    return actual, var, var_pct


def main() -> None:
    print("Demografia: descarregant padró de l'INE...")
    try:
        t2865 = fetch_ine(T_MUNI)
        t2853 = fetch_ine(T_CCAA)

        muni = find_one(t2865, "Castelló de la Plana. Total. Total habitantes.") or \
            find_one(t2865, "Castellón de la Plana. Total. Total habitantes.")
        prov = find_one(t2865, "Castellón/Castelló. Total. Total habitantes.")
        cv = find_one(t2853, "Comunitat Valenciana. Total. Total habitantes.")

        m_act, m_var, m_varpct = block(muni)
        p_act, _, _ = block(prov)
        c_act, _, _ = block(cv)
        period = period_label((muni.get("Data") or [{}])[0]) if muni else None

        prev = load_existing(OUT)
        padro = {
            "periode": period,
            "municipi": {
                "nom": "Castelló de la Plana",
                "poblacio": m_act,
                "variacio_anual": m_var,
                "variacio_anual_pct": m_varpct,
                "densitat_hab_km2": round(m_act / AREA_MUNICIPI, 1) if m_act else None,
                "superficie_km2": AREA_MUNICIPI,
            },
            "provincia": {"nom": "Castelló", "poblacio": p_act},
            "comunitat": {"nom": "Comunitat Valenciana", "poblacio": c_act},
            "pct_municipi_provincia": round(m_act / p_act * 100, 1) if (m_act and p_act) else None,
            "pct_provincia_comunitat": round(p_act / c_act * 100, 1) if (p_act and c_act) else None,
        }

        out = {
            "padro": padro,
            # Bloc de Cens / estudis / llars: manual (vegeu README). Es conserva el
            # que ja hi haguera per no perdre dades introduïdes a mà.
            "cens": prev.get("cens", {"_periode": "2021", "_font": "Cens 2021 (manual)", "_pendent": True}),
            "estudis": prev.get("estudis", {"_periode": "2022", "_pendent": True}),
            "llars": prev.get("llars", {"_periode": "2021", "_pendent": True}),
        }
        write_json(OUT, out)
        update_metadata("demografia", period or "?", SOURCE, "ok")
        print(f"Demografia: desat (padró {period}, municipi {m_act}).")
    except Exception as e:  # noqa: BLE001
        if not load_existing(OUT):
            write_json(OUT, {"padro": {}})
        update_metadata("demografia", source=SOURCE, status=f"error: {e}")
        print(f"Demografia: ERROR -> {e}")
        raise


if __name__ == "__main__":
    main()
