# CADI — Climate-Aware Deal Intelligence

Climate-integrated due diligence pipeline for EPF Private Markets demo.

**Purpose:** Demo prototype for EPF Centre of Excellence for Analytics interview.

---

## What It Does

Takes a fictional private equity deal document (PDF) and runs a 7-step pipeline:

1. Parses and extracts key entities (company, assets, locations, financials)
2. Geocodes physical asset locations (Nominatim + hardcoded fallbacks)
3. Assesses flood risk per asset using JRC data (location-based fallback)
4. Checks proximity to protected areas (WDPA + hardcoded fallback)
5. Scores transition risk by sector using NGFS scenarios
6. Generates an interactive Folium map
7. Produces a structured due diligence memo (HTML + Markdown)

**No external API key required.** All tools have hardcoded fallbacks — demo never fails.

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.agent --input data/deal/nusantara_digital.pdf --output output/
```

Output: `output/memo.html`, `output/map.html`, `output/agent_results.json`

---

## Project Structure

```
cadi/
├── data/
│   ├── jrc/          # Pre-clipped JRC flood rasters (optional — fallback active)
│   ├── wdpa/         # Malaysia protected areas (optional — fallback active)
│   ├── ngfs/         # Transition risk lookup (inline in transition.py)
│   └── deal/         # Fictional deal PDF (Nusantara Digital Sdn Bhd)
├── src/
│   ├── agent.py      # Fixed 7-step sequential pipeline
│   ├── tools/        # Individual tool modules
│   │   ├── document.py     # PDF parsing + regex entity extraction
│   │   ├── geocode.py      # Nominatim + hardcoded fallbacks
│   │   ├── flood_risk.py   # JRC raster query + location fallback
│   │   ├── biodiversity.py # WDPA proximity + hardcoded fallback
│   │   ├── transition.py   # NGFS sector risk lookup (inline data)
│   │   └── mapping.py      # Folium interactive map
│   ├── report.py     # Jinja2 memo → HTML/Markdown/DOCX
│   └── schemas.py    # Pydantic models for all tool I/O
├── templates/
│   └── memo_template.md    # Jinja2 report template
├── scripts/
│   └── generate_deal_pdf.py  # Generates the fictional deal PDF
├── web/              # Vercel frontend (planned — see PROJECT_SPEC.md §14)
├── api/              # Vercel FastAPI backend (planned)
├── output/           # Generated reports (gitignored)
└── tests/            # Unit tests (planned)
```

---

## Work Division

| Bot | Tasks | Status |
|-----|-------|--------|
| GLM | G1–G4: scaffolding, schemas, tools, deal PDF | Done |
| Claude | Pipeline rewrite, API removal, end-to-end validation | Done |
| GLM | G5–G7: Vercel web layer (FastAPI + SSE + frontend) | Pending |

See `PROJECT_SPEC.md` §14 for Vercel spec and §15 for G5–G7 task breakdown.

---

## Disclaimer

**ALL deal data is fictional.** Zero real financial data. For demonstration purposes only.
