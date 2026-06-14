#!/usr/bin/env python3
"""
IPC — Índex de Preus al Consum (variació anual desembre-desembre).
Font: INE, sèrie IPC251856 (Nacional. Índice general. Variación anual).
"""
from pathlib import Path

from _common import (DATA_DIR, fetch_ine, load_existing, period_label,
                     update_metadata, write_json)

OUT = DATA_DIR / "ipc.json"
SOURCE = "INE"
INE_IPC_SERIE = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC251856?nult=300"


def main() -> None:
    print("IPC: descarregant de l'INE...")
    try:
        raw = fetch_ine(INE_IPC_SERIE)
        data = raw.get("Data", [])

        # Sèrie anual: variació interanual del mes de desembre (FK_Periodo == 12).
        serie = []
        for it in data:
            if it.get("FK_Periodo") == 12:
                serie.append({"any": it["Anyo"], "variacio_anual": it["Valor"]})
        serie.sort(key=lambda x: x["any"])

        # Últim valor disponible (qualsevol mes) com a referència actual.
        # Atenció: DATOS_SERIE retorna els elements del més antic al més recent.
        ultim = data[-1] if data else None
        ipc_data = {
            "serie_desembre_desembre": serie,
            "ultim_mes": {
                "periode": period_label(ultim) if ultim else None,
                "variacio_anual": ultim["Valor"] if ultim else None,
            },
        }
        write_json(OUT, ipc_data)
        period = ipc_data["ultim_mes"]["periode"] or (str(serie[-1]["any"]) if serie else "?")
        update_metadata("ipc", period, SOURCE, "ok")
        print(f"IPC: desat ({len(serie)} anys, últim {period}).")
    except Exception as e:  # noqa: BLE001
        if not load_existing(OUT):
            write_json(OUT, {"serie_desembre_desembre": [], "ultim_mes": {}})
        update_metadata("ipc", source=SOURCE, status=f"error: {e}")
        print(f"IPC: ERROR -> {e}")
        raise


if __name__ == "__main__":
    main()
