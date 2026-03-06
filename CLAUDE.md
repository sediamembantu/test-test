# CADI — Climate-Aware Deal Intelligence

## Project Context
Demo prototype for EPF interview. Fixed pipeline: deal PDF → entity extraction → climate risk → DD memo.

**No Anthropic API key required.** Pipeline is fully self-contained with hardcoded fallbacks.

## Stack
- Python 3.11+
- Virtual environment: `python -m venv .venv`
- Package management: `pip install -r requirements.txt`
- Linting: ruff
- Testing: pytest
- Type checking: Pydantic models for all tool I/O

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Conventions
- Use pathlib for all file paths
- Type hints on all functions
- Docstrings on public functions
- Each tool is a standalone module in src/tools/
- Tools are pure functions: input → output, no side effects
- Pipeline orchestration in src/agent.py only (fixed sequential — no LLM agent loop)

## Key Libraries
- pymupdf: PDF parsing + text extraction
- folium: Interactive map generation
- shapely: Geometry operations
- geopandas: Vector geospatial (WDPA — optional, fallback active)
- rasterio: GeoTIFF raster queries (JRC — optional, fallback active)
- jinja2: Report templating
- pydantic: Schema validation for all tool I/O
- rich: Terminal output formatting
- fastapi + sse-starlette: Vercel web layer (planned, see §14)

## Data Locations
- data/jrc/ — Pre-clipped JRC flood rasters (GeoTIFF) — optional, fallback active
- data/wdpa/ — Malaysia protected areas (GeoPackage) — optional, fallback active
- data/ngfs/ — Transition risk lookup — data is inline in src/tools/transition.py
- data/deal/ — Fictional deal PDF (Nusantara Digital Sdn Bhd)

## Testing
```bash
pytest tests/
```
Each tool has independent unit tests. Mock external APIs (Nominatim) in tests.

## Running the Pipeline
```bash
source .venv/bin/activate
python -m src.agent --input data/deal/nusantara_digital.pdf --output output/
```

## Important
- ALL deal data is fictional. Zero real financial data.
- No Anthropic API key needed — removed. Pipeline uses regex + fallbacks throughout.
- Geocoding has hardcoded fallbacks — demo must never fail on API timeout.
- JRC rasters and WDPA data are optional — location-based fallbacks are always active.
- Vercel web layer planned: see PROJECT_SPEC.md §14 and §15 (GLM tasks G5–G7).
