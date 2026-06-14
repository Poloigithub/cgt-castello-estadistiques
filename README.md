# Resum estadístic — CGT Federació Intercomarcal de Castelló

Web estàtica que reprodueix els indicadors socioeconòmics del *Resum estadístic* de CGT
Castelló (EPA, IPC, demografia, empreses, cost laboral, salaris i SMI). Les dades
s'actualitzen automàticament cada setmana mitjançant **GitHub Actions** des de fonts
oficials i es publiquen amb **GitHub Pages**. La pàgina és llegible sense JavaScript
(amb enllaços als fitxers JSON en brut).

## Estructura

```
.github/workflows/update-data.yml   Acció setmanal d'actualització
data/*.json                         Dades (generades pels scripts; serveixen de fallback)
scripts/fetch_*.py                  Scripts de descàrrega per dataset
scripts/_common.py                  Utilitats compartides (INE, metadata, fallback)
index.html                          Web (render amb JS llegint data/*.json)
```

## Fonts i taules

| Dataset | Font | Taula / sèrie INE |
|---------|------|-------------------|
| IPC | INE | sèrie `IPC251856` (variació anual, general nacional) |
| EPA — CV | INE | taula `65291` (relació amb l'activitat per CCAA) |
| EPA — Castelló (sexe) | INE | taules `65345` (absoluts) i `65349` (taxes) |
| EPA — Castelló (sector) | INE | taula `65354` |
| EPA — comarques | GVA-ARGOS (PEGV) | pàgines HTML trimestrals IMTNS (estimacions àrees petites) |
| Cost laboral | INE-ETCL | taula `6061` (cost per treballador, CCAA i sector) |
| Salaris | INE-EES | taula `28191` (guany anual mitjà, CCAA i sexe) |
| Demografia (padró) | INE | taules `2865` (municipis Castelló) i `2853` (CCAA) |
| Empreses | INE-DIRCE | taula `4721` (empreses per municipi i activitat) |
| SMI | BOE / Ministeri de Treball | `scripts/fetch_smi.py` (manteniment manual) |

> Nota: la taula `6157` indicada al document original ja no existeix a l'API de l'INE; s'ha
> substituït per la `6061`. L'API de l'INE retorna `DATOS_TABLA` del més recent al més antic,
> però `DATOS_SERIE` a l'inrevés (tingut en compte als scripts).

## Execució en local

```bash
pip install -r scripts/requirements.txt
python3 scripts/fetch_ipc.py        # i la resta de fetch_*.py
python3 -m http.server              # i obrir http://localhost:8000
```

Cada script, si falla, conserva el JSON anterior i registra l'estat de l'error a
`data/metadata.json`; la web mostra un avís visual quan l'estat d'un dataset no és `ok`.

## Publicació a GitHub Pages

1. Puja el repositori a GitHub.
2. **Settings → Pages → Source: Deploy from branch → `main` / `/root`**.
3. L'acció `update-data.yml` s'executa cada dilluns (o manualment des de la pestanya
   *Actions → Run workflow*) i fa commit de les dades actualitzades.

## Manteniment manual

- **SMI** (`scripts/fetch_smi.py`): actualitzar la llista `SMI_DADES` quan es publique
  un nou Reial Decret al BOE.
- **Demografia — Cens / estudis / llars**: els blocs `cens`, `estudis` i `llars` de
  `data/demografia.json` són de manteniment manual (no tenen API anual estable). Edita
  el JSON i marca `_pendent: false` quan els òmpligues.
- **EPA comarques**: depèn de les pàgines IMTNS de PEGV, que canvien d'URL cada
  trimestre; l'script descobreix automàticament el trimestre més recent. Si la font no
  és accessible, conserva les dades anteriors i marca l'estat com a `manual`.
