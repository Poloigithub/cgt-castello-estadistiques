#!/usr/bin/env python3
"""
SMI — Salari Mínim Interprofessional.
No hi ha API oficial directa: la sèrie es manté manualment al repositori i
s'actualitza quan es publica un nou Reial Decret (BOE / Ministerio de Trabajo).
"""
from pathlib import Path

from _common import DATA_DIR, update_metadata, write_json

OUT = DATA_DIR / "smi.json"
SOURCE = "Ministerio de Trabajo / BOE"

# Valors en € (14 pagues). Actualitzar manualment amb cada nou RD.
SMI_DADES = [
    {"any": 2021, "dia": 31.66, "mes": 950.00, "any_total": 13300.00, "var_pct": 0.0},
    {"any": 2022, "dia": 33.33, "mes": 1000.00, "any_total": 14000.00, "var_pct": 5.3},
    {"any": 2023, "dia": 36.00, "mes": 1080.00, "any_total": 15120.00, "var_pct": 8.0},
    {"any": 2024, "dia": 37.80, "mes": 1134.00, "any_total": 15876.00, "var_pct": 5.0},
    {"any": 2025, "dia": 39.47, "mes": 1184.00, "any_total": 16576.00, "var_pct": 4.4},
]


def main() -> None:
    smi_data = {
        "serie": SMI_DADES,
        "_nota": "Actualitzat manualment. Font: BOE / Ministerio de Trabajo.",
    }
    write_json(OUT, smi_data)
    update_metadata("smi", str(SMI_DADES[-1]["any"]), SOURCE, "manual")
    print(f"SMI: desat ({len(SMI_DADES)} anys, últim {SMI_DADES[-1]['any']}).")


if __name__ == "__main__":
    main()
