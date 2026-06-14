#!/usr/bin/env python3
"""
Salaris — Enquesta d'Estructura Salarial (EES).
Taula INE 28191 — Salari anual mitjà/medià i percentils, per CCAA i sexe.
Es desa el guany anual mitjà (Media) per a Comunitat Valenciana i Espanya, amb
sèrie històrica i el % CV/Espanya. (Periodicitat bianual; pot tindre buits.)
"""
from _common import (DATA_DIR, fetch_ine, find_one, load_existing,
                     update_metadata, write_json)

OUT = DATA_DIR / "salaris.json"
SOURCE = "INE-EES"
URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/28191?nult=12"

AMBITS = [("espanya", "Total Nacional"), ("comunitat_valenciana", "Comunitat Valenciana")]
SEXES = [("ambdos", "Ambos sexos"), ("homes", "Hombres"), ("dones", "Mujeres")]


def serie_media(table, sexe, ambit):
    s = find_one(table, sexe + ". " + ambit + ". Dato base. Media.")
    if not s:
        return []
    out = [{"any": it["Anyo"], "valor": it["Valor"]} for it in (s.get("Data") or [])]
    out.sort(key=lambda x: x["any"])
    return out


def main() -> None:
    print("Salaris: descarregant de l'INE (taula 28191)...")
    try:
        table = fetch_ine(URL)
        guany = {}
        ultim_any = None
        for akey, alabel in AMBITS:
            guany[akey] = {}
            for skey, slabel in SEXES:
                serie = serie_media(table, slabel, alabel)
                guany[akey][skey] = serie
                if serie:
                    ultim_any = max(ultim_any or 0, serie[-1]["any"])

        # % CV/Espanya per a l'últim any disponible (ambdós sexes).
        pct = None
        try:
            esp = {x["any"]: x["valor"] for x in guany["espanya"]["ambdos"]}
            cv = {x["any"]: x["valor"] for x in guany["comunitat_valenciana"]["ambdos"]}
            anys = sorted(set(esp) & set(cv))
            if anys:
                a = anys[-1]
                pct = round(cv[a] / esp[a] * 100, 1) if esp[a] else None
        except Exception:  # noqa: BLE001
            pct = None

        out = {
            "guany_anual_mitja": guany,
            "ultim_any": ultim_any,
            "pct_cv_espanya_ambdos": pct,
            "_nota": "Guany anual mitjà (Media). Desglossaments addicionals (sector, "
                     "ocupació, contracte, edat, nacionalitat, guany/hora) requereixen "
                     "altres taules EES i poden afegir-se més endavant.",
        }
        write_json(OUT, out)
        update_metadata("salaris", str(ultim_any) if ultim_any else "?", SOURCE, "ok")
        print(f"Salaris: desat (últim any {ultim_any}, % CV/Espanya {pct}).")
    except Exception as e:  # noqa: BLE001
        if not load_existing(OUT):
            write_json(OUT, {"guany_anual_mitja": {}})
        update_metadata("salaris", source=SOURCE, status=f"error: {e}")
        print(f"Salaris: ERROR -> {e}")
        raise


if __name__ == "__main__":
    main()
