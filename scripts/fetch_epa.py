#!/usr/bin/env python3
"""
EPA — Enquesta de Població Activa (Comunitat Valenciana i província de Castelló).

Taules INE (resoltes via TABLAS_OPERACION/EPA):
  65291 — Població de 16+ per relació amb l'activitat, sexe i CCAA  (valors absoluts CV)
  65345 — Població de 16+ per relació amb l'activitat, sexe i província (Castelló)
  65349 — Taxes d'activitat, atur i ocupació per província i sexe (Castelló)
  65354 — Ocupats per sector econòmic i província (Castelló)

Les dades comarcals NO les publica l'INE -> les gestiona fetch_comarques (ARGOS).
"""
from _common import (DATA_DIR, fetch_ine, find_one, load_existing, period_label,
                     update_metadata, variations, write_json)

OUT = DATA_DIR / "epa.json"
SOURCE = "INE"
BASE = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{}?nult=6"


def val(series, idx=0):
    if not series:
        return None
    data = series.get("Data") or []
    return data[idx]["Valor"] if len(data) > idx else None


def pct(num, den):
    if num is None or den in (None, 0):
        return None
    return round(num / den * 100, 1)


def cv_block(t65291):
    def s(cat):
        return find_one(t65291, "Ambos sexos. Comunitat Valenciana. " + cat + ". Total. Valor absoluto.")
    poblacio = val(s("Total"))
    actius = val(s("Activos"))
    ocupats = val(s("Ocupados"))
    desocupats = val(s("Parados"))
    ocup_serie = s("Ocupados")
    var = variations(ocup_serie)
    return {
        "periode": period_label((ocup_serie.get("Data") or [{}])[0]) if ocup_serie else None,
        "ocupats_milers": ocupats,
        "desocupats_milers": desocupats,
        "actius_milers": actius,
        "taxa_activitat": pct(actius, poblacio),
        "taxa_desocupacio": pct(desocupats, actius),
        "var_trim_ocupats": var.get("var_trim"),
        "var_anual_ocupats": var.get("var_anual"),
    }


def sex_block(t65345, t65349, sexe):
    def absser(cat):
        # 65345: "<sexe>. Castellón/Castelló. Total. <cat>. Valor absoluto."
        return find_one(t65345, sexe + ".", "Castell", ". " + cat + ". Valor absoluto.")

    def rate(tipus):
        # 65349: "Tasa de <tipus>. ... Castelló ... <sexe> ..."
        return find_one(t65349, "Tasa de " + tipus, sexe, "Castell")

    poblacio = val(absser("Total"))
    actius = val(absser("Activos"))
    ocupats = val(absser("Ocupados"))
    desocupats = val(absser("Parados"))
    inactius = val(absser("Inactivos"))
    return {
        "poblacio_16_mes": poblacio,
        "actives": actius,
        "ocupades": ocupats,
        "desocupades": desocupats,
        "inactives": inactius,
        "taxa_activitat": val(rate("actividad")),
        "taxa_ocupacio": val(rate("empleo")),
        "taxa_desocupacio": val(rate("paro")),
    }


def sector_block(t65354):
    def s(sector):
        return find_one(t65354, "Castell", "Ocupados. Ambos sexos. " + sector + ". Valor absoluto.")
    total = s("Total")
    return {
        "periode": period_label((total.get("Data") or [{}])[0]) if total else None,
        "total": val(total),
        "agricultura": val(s("Agricultura")),
        "industria": val(s("Industria")),
        "construccio": val(s("Construcción")),
        "serveis": val(s("Servicios")),
    }


def main() -> None:
    print("EPA: descarregant de l'INE...")
    try:
        t65291 = fetch_ine(BASE.format(65291))
        t65345 = fetch_ine(BASE.format(65345))
        t65349 = fetch_ine(BASE.format(65349))
        t65354 = fetch_ine(BASE.format(65354))

        cv = cv_block(t65291)
        cast = {
            "periode": cv["periode"],
            "ambdos_sexes": sex_block(t65345, t65349, "Ambos sexos"),
            "homes": sex_block(t65345, t65349, "Hombres"),
            "dones": sex_block(t65345, t65349, "Mujeres"),
        }
        sector = sector_block(t65354)

        # Preserva el bloc comarcal generat per fetch_comarques (si existeix).
        prev = load_existing(OUT)
        epa = {
            "cv_resum": cv,
            "castello_provincia": cast,
            "ocupats_sector_castello": sector,
            "comarques": prev.get("comarques", []),
            "comarques_periode": prev.get("comarques_periode"),
        }
        write_json(OUT, epa)
        update_metadata("epa", cv["periode"] or "?", SOURCE, "ok")
        print(f"EPA: desat (CV {cv['periode']}, ocupats Castelló {sector['total']} mil).")
    except Exception as e:  # noqa: BLE001
        if not load_existing(OUT):
            write_json(OUT, {"cv_resum": {}, "castello_provincia": {},
                             "ocupats_sector_castello": {}, "comarques": []})
        update_metadata("epa", source=SOURCE, status=f"error: {e}")
        print(f"EPA: ERROR -> {e}")
        raise


if __name__ == "__main__":
    main()
