# CADI — Climate-Aware Deal Intelligence

## Project Context
Demo prototype for EPF interview. Agentic pipeline: deal PDF → entity extraction → climate risk → DD memo.

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
- Agent orchestration in src/agent.py only

## Key Libraries
- anthropic: Claude API client
- pymupdf: PDF parsing
- rasterio: GeoTIFF raster queries
- geopandas: Vector geospatial operations
- folium: Map generation
- shapely: Geometry
- python-docx: DOCX report output (stretch)

## Data Locations
- data/jrc/ — Pre-clipped JRC flood rasters (GeoTIFF)
- data/wdpa/ — Malaysia protected areas (GeoPackage)
- data/ngfs/ — Transition risk lookup (JSON)
- data/deal/ — Fictional deal PDF

## Testing
```bash
pytest tests/
```
Each tool has independent unit tests. Mock external APIs (Nominatim) in tests.

## Running the Agent
```bash
source .venv/bin/activate
python -m src.agent --input data/deal/nusantara_digital.pdf --output output/
```

## Important
- ALL deal data is fictional. Zero real financial data.
- Geocoding has hardcoded fallbacks — demo must never fail on API timeout.
- JRC rasters are pre-clipped to Peninsular Malaysia only.
