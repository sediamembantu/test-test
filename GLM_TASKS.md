# GLM Implementation Brief — CADI src/tools/

You are implementing four functions in an existing Python codebase.
Do not modify any file outside `src/tools/` and `src/schemas.py` (one change needed there).
Do not change function signatures. Do not add new tools.

---

## Repository Layout (read-only context)

```
src/
  schemas.py        ← Pydantic models. Read this. One field to add (see G4).
  tools/
    document.py     ← YOUR TASK G1
    flood_risk.py   ← YOUR TASK G2
    biodiversity.py ← YOUR TASK G3
    mapping.py      ← YOUR TASK G4
    geocode.py      ← DO NOT TOUCH
    transition.py   ← DO NOT TOUCH
  agent.py          ← DO NOT TOUCH
  report.py         ← DO NOT TOUCH
data/
  deal/nusantara_digital.pdf   ← the input PDF (exists)
  jrc/    ← empty (no raster files yet)
  wdpa/   ← empty (no shapefiles yet)
```

---

## G1 — `src/tools/document.py`: Real entity extraction

### Current problem
`parse_document()` returns `company_name="[EXTRACT FROM TEXT]"` and `assets=[]`.
The agent loop cannot proceed without real extracted data.

### What to implement

After extracting `raw_text` from the PDF (existing pymupdf code is fine),
make a **single Claude API call** to extract structured JSON.

Use this exact pattern:

```python
import json
import os
from anthropic import Anthropic

_client = Anthropic()  # module-level, reads ANTHROPIC_API_KEY from env

def _extract_with_llm(raw_text: str) -> dict:
    """Call Claude haiku to extract structured deal data from raw text."""
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "You are a financial document parser. "
            "Extract the requested fields and return ONLY valid JSON. "
            "No markdown, no explanation, just the JSON object."
        ),
        messages=[{
            "role": "user",
            "content": (
                "Extract from this deal document:\n\n"
                f"{raw_text[:6000]}\n\n"
                "Return JSON with exactly these keys:\n"
                '{"company_name": str, "company_registration": str, '
                '"sector": str, "headquarters": str, "deal_type": str, '
                '"valuation_myr": float, "target_irr": str, '
                '"assets": [{"name": str, "address": str, '
                '"capacity_mw": float, "status": str}], '
                '"financials": {"revenue_myr": [float], '
                '"ebitda_myr": [float], "capex_myr": [float]}}'
            ),
        }],
    )
    return json.loads(response.content[0].text)
```

Then populate `ParseDocumentOutput` from the returned dict:

```python
extracted = _extract_with_llm(raw_text)

assets = [
    Asset(
        name=a["name"],
        address=a["address"],
        capacity_mw=a.get("capacity_mw"),
        status=a.get("status"),
    )
    for a in extracted.get("assets", [])
]

financials = Financials(
    revenue_myr=extracted.get("financials", {}).get("revenue_myr", []),
    ebitda_myr=extracted.get("financials", {}).get("ebitda_myr", []),
    capex_myr=extracted.get("financials", {}).get("capex_myr", []),
)

return ParseDocumentOutput(
    company_name=extracted.get("company_name", "Unknown"),
    company_registration=extracted.get("company_registration"),
    sector=extracted.get("sector"),
    headquarters=extracted.get("headquarters"),
    deal_type=extracted.get("deal_type"),
    valuation_myr=extracted.get("valuation_myr"),
    target_irr=extracted.get("target_irr"),
    assets=assets,
    financials=financials,
    raw_text=raw_text,
)
```

Wrap `_extract_with_llm` in a try/except — if it fails for any reason,
fall back to the hardcoded placeholder values that exist today so the demo never crashes.

---

## G2 — `src/tools/flood_risk.py`: Location-aware fallback

### Current problem
Single hardcoded return regardless of location. Both assets get identical risk.
The demo needs Kulai (Johor) to show High risk and Cyberjaya to show Low risk.

### What to implement

Replace the placeholder return block (after the `if not jrc_files:` early return)
with location-aware logic. Keep the `_calculate_risk_level` and `_sample_rasters`
functions exactly as they are.

```python
# Location-aware fallback (used when JRC rasters are absent)
# Johor lowlands (lon < 102.5): flood-prone, High risk
# Selangor/KL (lon >= 102.5): elevated, Low risk
if lon < 102.5:
    depths = FloodDepths(rp10=0.3, rp50=0.8, rp100=1.5, rp500=2.8)
    notes = "Location-based estimate: Johor lowland flood zone"
else:
    depths = FloodDepths(rp10=0.0, rp50=0.1, rp100=0.2, rp500=0.5)
    notes = "Location-based estimate: Selangor elevated corridor"

return FloodRiskOutput(
    asset_name=input_data.asset_name,
    latitude=lat,
    longitude=lon,
    depths=depths,
    risk_level=_calculate_risk_level(depths),
    notes=notes,
)
```

The `if not jrc_files:` early return (Medium, no data) stays above this block.
When JRC rasters are eventually added, the existing TODO block below handles it.

---

## G3 — `src/tools/biodiversity.py`: Real geopandas query

### Current problem
Function always returns a hardcoded 2-point fallback regardless of coordinates.

### What to implement

Check if WDPA data exists first. If it does, run a real geopandas query.
If not, use smart hardcoded fallbacks based on known locations.

```python
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

WDPA_PATH = Path(__file__).parent.parent.parent / "data" / "wdpa"

def check_biodiversity(input_data: BiodiversityInput) -> BiodiversityOutput:
    lat = input_data.latitude
    lon = input_data.longitude
    point = Point(lon, lat)

    # Try real WDPA query first
    wdpa_files = list(WDPA_PATH.glob("*.gpkg")) + list(WDPA_PATH.glob("*.shp"))
    if wdpa_files:
        try:
            gdf = gpd.read_file(wdpa_files[0])
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            gdf["distance_km"] = gdf.geometry.distance(point) * 111  # approx degrees→km
            nearest = gdf.loc[gdf["distance_km"].idxmin()]
            distance = float(nearest["distance_km"])
            return BiodiversityOutput(
                asset_name=input_data.asset_name,
                nearest_protected_area=str(nearest.get("NAME", "Unknown")),
                distance_km=round(distance, 2),
                protected_area_type=str(nearest.get("DESIG_ENG", "Protected Area")),
                risk_flag=distance < 10.0,
                notes="WDPA Malaysia dataset",
            )
        except Exception:
            pass  # Fall through to hardcoded fallback

    # Hardcoded fallback — keyed by proximity to known coordinates
    # Kulai (1.658, 103.6) is near Sungai Skudai wetlands
    # Cyberjaya (2.9228, 101.6538) is not near protected areas
    if lat < 2.5:  # Johor
        return BiodiversityOutput(
            asset_name=input_data.asset_name,
            nearest_protected_area="Sungai Skudai Wetlands",
            distance_km=4.2,
            protected_area_type="Wetland / Ramsar candidate",
            risk_flag=True,
            notes="Hardcoded fallback — WDPA data not loaded",
        )
    else:  # Selangor / KL
        return BiodiversityOutput(
            asset_name=input_data.asset_name,
            nearest_protected_area="Putrajaya Wetlands",
            distance_km=18.5,
            protected_area_type="Urban wetland park",
            risk_flag=False,
            notes="Hardcoded fallback — WDPA data not loaded",
        )
```

---

## G4 — `src/tools/mapping.py` + `src/schemas.py`: Coloured risk markers

### Schema change required first (src/schemas.py)

Add one optional field to `MapInput`:

```python
class MapInput(BaseModel):
    """Input for generate_map tool."""
    assets: list[Asset] = Field(..., description="Assets to plot")
    flood_data: bool = Field(True, description="Include flood risk overlay")
    output_path: str = Field("output/map.html", description="Output HTML path")
    flood_risks: list[dict] = Field(default_factory=list, description="Flood risk results for colour coding")
```

This is a backwards-compatible addition (has a default). Agent can pass it or not.

### What to implement in mapping.py

After placing each `folium.Marker`, also add a `folium.CircleMarker`.
Build a lookup dict from `flood_risks` at the top of the function.

```python
RISK_COLOURS = {
    "Critical": "darkred",
    "High": "red",
    "Medium": "orange",
    "Low": "green",
}

# Build risk lookup: asset_name → risk_level
risk_lookup = {r.get("asset_name", ""): r.get("risk_level", "Medium")
               for r in input_data.flood_risks}

# Inside the asset loop, after folium.Marker:
risk_level = risk_lookup.get(asset.name, "Medium")
colour = RISK_COLOURS.get(risk_level, "orange")

folium.CircleMarker(
    location=[asset.latitude, asset.longitude],
    radius=20,
    color=colour,
    fill=True,
    fill_color=colour,
    fill_opacity=0.3,
    popup=f"{asset.name}: {risk_level} flood risk",
).add_to(m)
```

Add an HTML legend to the map:

```python
legend_html = """
<div style="position:fixed; bottom:30px; right:30px; z-index:1000;
     background:white; padding:12px; border-radius:6px;
     border:1px solid #ccc; font-size:13px; line-height:1.8;">
  <b>Flood Risk</b><br>
  <span style="color:darkred">&#9632;</span> Critical<br>
  <span style="color:red">&#9632;</span> High<br>
  <span style="color:orange">&#9632;</span> Medium<br>
  <span style="color:green">&#9632;</span> Low
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
```

---

## Definition of Done

All four tasks complete when:

```bash
# No import errors
python -c "from src.tools.document import parse_document; print('OK')"
python -c "from src.tools.flood_risk import assess_flood_risk; print('OK')"
python -c "from src.tools.biodiversity import check_biodiversity; print('OK')"
python -c "from src.tools.mapping import generate_map; print('OK')"

# Flood risk returns correct levels
python -c "
from src.schemas import FloodRiskInput
from src.tools.flood_risk import assess_flood_risk
kulai = assess_flood_risk(FloodRiskInput(latitude=1.658, longitude=103.6, asset_name='Kulai'))
cyber = assess_flood_risk(FloodRiskInput(latitude=2.9228, longitude=101.6538, asset_name='Cyber'))
assert kulai.risk_level == 'High', kulai.risk_level
assert cyber.risk_level == 'Low', cyber.risk_level
print('Flood risk: OK')
"
```

Commit to branch: `glm/tools-implementation` (or whatever branch you're on).
Do NOT push to `claude/review-project-spec-JKSll` — that is Claude's branch.
