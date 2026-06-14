#!/usr/bin/env python3
"""
IPC — Índex de Preus al Consum (variació anual desembre-desembre).
Font: INE, taula 76134 (Tasa de variación del índice general nacional).

S'usa la TAULA i es localitza la sèrie pel nom ("Índice general. Variación anual")
en lloc de fixar un codi de sèrie: l'INE canvia els codis quan rebasa l'IPC (p. ex.
la sèrie antiga IPC251856 es va tancar al desembre de 2025 i va passar a IPC290750).
"""
from pathlib import Path

from _common import (DATA_DIR, fetch_ine, find_one, load_existing, period_label,
                     update_metadata, write_json)

OUT = DATA_DIR / "ipc.json"
SOURCE = "INE"
# Taula vigent (tota la sèrie històrica, des de 1961).
INE_IPC_TABLA = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/76134?nult=900"


def main() -> None:
    print("IPC: descarregant de l'INE (taula 76134)...")
    try:
        table = fetch_ine(INE_IPC_TABLA)
        serie_var = find_one(table, "Índice general. Variación anual")
        if not serie_var:
            raise RuntimeError("no s'ha trobat la sèrie de variació anual a la taula 76134")
        data = serie_var.get("Data") or []

        # Sèrie anual: variació interanual del mes de desembre (FK_Periodo == 12).
        serie = [{"any": it["Anyo"], "variacio_anual": it["Valor"]}
                 for it in data if it.get("FK_Periodo") == 12]
        serie.sort(key=lambda x: x["any"])

        # Últim valor disponible, sense dependre de l'ordre de la resposta.
        ultim = max(data, key=lambda it: (it["Anyo"], it["FK_Periodo"])) if data else None
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
