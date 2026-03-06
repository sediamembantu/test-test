# CADI — Task Coordination

## How This Works
- **GLM** owns `src/tools/` — implements the actual logic
- **Claude** owns `src/agent.py`, `src/report.py`, `templates/`, `tests/`
- **`src/schemas.py`** is shared — neither agent changes it without this file being updated first
- **You** update the status column as work moves

---

## Ownership Reference

| Path | Owner |
|------|-------|
| `src/tools/*.py` | GLM |
| `src/agent.py` | Claude |
| `src/report.py` | Claude |
| `templates/` | Claude |
| `tests/` | Claude |
| `src/schemas.py` | SHARED — agree before changing |
| `data/` | Neither (static assets) |
| `output/` | Neither (generated, not committed) |

---

## Tasks

### GLM — src/tools/

| # | File | Task | Status |
|---|------|------|--------|
| G1 | `document.py` | Call Claude API (haiku) to extract structured JSON from raw PDF text. Populate `ParseDocumentOutput` with real company name, assets list, financials. Currently returns hardcoded `"[EXTRACT FROM TEXT]"` and empty `assets=[]`. | `pending` |
| G2 | `flood_risk.py` | Replace single hardcoded return with location-aware fallback: lon < 102.5 (Johor/Kulai) → High risk depths; else (Selangor) → Low risk depths. Keep rasterio skeleton for real data later. | `pending` |
| G3 | `biodiversity.py` | Replace hardcoded 2-point fallback with a real geopandas query against `data/wdpa/` when the file exists. Keep fallback for when data is absent. | `pending` |
| G4 | `mapping.py` | Add risk-coloured `CircleMarker` behind each asset marker (Critical=darkred, High=red, Medium=orange, Low=green). Add HTML legend bottom-right. | `pending` |

---

### Claude — orchestration, reporting, tests

| # | File | Task | Status |
|---|------|------|--------|
| C1 | `agent.py` | Uncomment and wire `generate_report` in the TOOLS dict. Import `generate_report` and `ReportInput` from `src.report`. | `pending` |
| C2 | `requirements.txt` | Add `requests` (used in geocode.py) and `markdown` (used in report.py) — both missing. | `pending` |
| C3 | `tests/test_geocode.py` | Test known Kulai address returns fallback coords without hitting Nominatim. Test unknown address raises on network failure. | `pending` |
| C4 | `tests/test_flood_risk.py` | Test Kulai coords → `risk_level="High"`. Test Cyberjaya coords → `risk_level="Low"`. | `pending` |
| C5 | `tests/test_transition.py` | Test "data centre" → High. Test unknown sector → Medium. Test case-insensitivity. | `pending` |

---

## Shared Contract — schemas.py

No changes without updating this table first.

| Schema | Current fields | Proposed change | Agreed |
|--------|---------------|-----------------|--------|
| `MapInput` | `assets`, `flood_data`, `output_path` | Add `flood_risks: list[dict] = []` for G4 colour coding | `pending` |

---

## Definition of Done

Pipeline runs end-to-end without errors:
```bash
python -m src.agent --input data/deal/nusantara_digital.pdf --output output/
pytest tests/ -v
```

Output directory contains:
- `agent_results.json`
- `map.html` with coloured markers
- `dd_memo.md` or `dd_memo.html`
