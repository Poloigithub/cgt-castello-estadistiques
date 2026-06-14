#!/usr/bin/env python3
"""
Utilitats compartides pels scripts de fetch de l'INE.

Format de resposta de l'API INE (https://www.ine.es/dyngs/DataLab/es/manual.html):
    DATOS_TABLA -> [ {"COD","Nombre","Data":[ {"Fecha","Anyo","FK_Periodo","Valor"} ] } ]
    DATOS_SERIE -> {"COD","Nombre","Data":[ ... ] }

Notes importants:
  * `Fecha` ve en mil·lisegons epoch (NO en format YYYYMMDD).
  * El període es deriva de `Anyo` + `FK_Periodo`:
        1..12  -> mensual  (2025-04)
        19..22 -> trimestral (19=T1, 20=T2, 21=T3, 22=T4)  -> 2026T1
        28     -> anual     (2025)
  * Els elements de `Data` venen ordenats del més recent al més antic.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TRIMESTRE = {19: "T1", 20: "T2", 21: "T3", 22: "T4"}


def fetch_ine(url: str, retries: int = 3, timeout: int = 40) -> object:
    """Descarrega un recurs JSON de l'INE amb reintents."""
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "cgt-castello-estadistiques"})
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"No s'ha pogut descarregar {url}: {last_err}")


def period_label(item: dict) -> str:
    """Retorna l'etiqueta de període d'un element de Data."""
    anyo = item.get("Anyo")
    fk = item.get("FK_Periodo")
    if fk in TRIMESTRE:
        return f"{anyo}{TRIMESTRE[fk]}"
    if isinstance(fk, int) and 1 <= fk <= 12:
        return f"{anyo}-{fk:02d}"
    return str(anyo)


def first(series: dict):
    """Primer (més recent) valor d'una sèrie, o None."""
    data = series.get("Data") or []
    return data[0] if data else None


def by_name(table: list, predicate) -> list:
    """Filtra una taula (llista de sèries) pel nom amb una funció predicat."""
    return [s for s in table if predicate(s.get("Nombre", ""))]


def find_one(table: list, *needles: str):
    """Retorna la 1a sèrie el nom de la qual conté TOTS els fragments donats."""
    for s in table:
        n = s.get("Nombre", "")
        if all(x in n for x in needles):
            return s
    return None


def value_of(series) -> float:
    it = first(series) if series else None
    return it["Valor"] if it else None


def variations(series, latest_idx: int = 0, trim_idx: int = 1, anual_idx: int = 4):
    """Variació absoluta trimestral i anual a partir d'una sèrie ordenada (recent->antic)."""
    data = (series or {}).get("Data") or []

    def val(i):
        return data[i]["Valor"] if len(data) > i else None

    cur = val(latest_idx)
    out = {}
    if cur is not None and val(trim_idx) is not None:
        out["var_trim"] = round(cur - val(trim_idx), 2)
    if cur is not None and val(anual_idx) is not None:
        out["var_anual"] = round(cur - val(anual_idx), 2)
    return out


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_existing(path: Path) -> dict:
    """Carrega el JSON anterior (fallback si el fetch falla). {} si no existeix."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def update_metadata(dataset_key: str, period: str = None, source: str = None,
                    status: str = "ok") -> None:
    meta_path = DATA_DIR / "metadata.json"
    meta = load_existing(meta_path)
    meta.setdefault("datasets", {})
    ds = meta["datasets"].setdefault(dataset_key, {})
    ds["last_updated"] = datetime.now(timezone.utc).isoformat()
    if period is not None:
        ds["last_data_period"] = period
    if source is not None:
        ds["source"] = source
    ds["status"] = status
    write_json(meta_path, meta)


def set_last_run() -> None:
    meta_path = DATA_DIR / "metadata.json"
    meta = load_existing(meta_path)
    meta["last_run"] = datetime.now(timezone.utc).isoformat()
    write_json(meta_path, meta)
