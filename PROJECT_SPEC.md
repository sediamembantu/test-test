# Climate-Aware Deal Intelligence (CADI)

## Due Diligence Pipeline for EPF Private Markets

**Purpose:** Demo-ready prototype for EPF Centre of Excellence for Analytics interview. Demonstrates how data science + AI can transform private market due diligence with integrated climate risk assessment.

**Not for production.** Designed to run reliably for a 2-minute screen-recorded demo.

**No Anthropic API key required.** Pipeline uses regex extraction and hardcoded fallbacks throughout.

---

## 1. What It Does

Takes a fictional private equity deal document (PDF), runs a fixed 7-step pipeline:

1. Parses and extracts key entities (company, assets, locations, financials) via regex + pymupdf
2. Geocodes physical asset locations (Nominatim + hardcoded fallbacks)
3. Assesses flood risk per asset using JRC data (location-based fallback when rasters absent)
4. Checks proximity to protected areas using WDPA (hardcoded fallback when data absent)
5. Scores transition risk by sector using NGFS scenarios (inline lookup)
6. Generates an interactive Folium map
7. Produces a structured due diligence memo (HTML + Markdown)

---

## 2. Fictional Deal: Nusantara Digital Sdn Bhd

A proposed investment in a 300MW data centre campus in Malaysia.

### Company Profile

- **Name:** Nusantara Digital Sdn Bhd
- **SSM Registration:** 202401012345 (fictional)
- **Sector:** Data centre / digital infrastructure
- **Founded:** 2023
- **HQ:** Kuala Lumpur

### Deal Terms

- **Deal type:** Equity stake acquisition (30%)
- **Valuation:** RM 2.8 billion
- **Target IRR:** 12-15% over 10 years
- **Anchor tenant:** Fictional hyperscaler ("CloudAsia") on 15-year lease

### Physical Assets (Two Sites)

**Primary Campus — Kulai, Johor**
- Address: Lot 1234, Jalan Perindustrian Kulai, 81000 Kulai, Johor
- Capacity: 250MW
- Status: Phase 1 (100MW) operational, Phase 2 under construction
- Coordinates (approx): 1.6580° N, 103.6000° E
- Why this location: Real DC corridor (near YTL, Vernet, SEA Gateways builds). Flood-prone lowland area — agent should flag this.

**DR Site — Cyberjaya, Selangor**
- Address: Block C, Cyberjaya Technology Park, 63000 Cyberjaya, Selangor
- Capacity: 50MW
- Status: Operational
- Coordinates (approx): 2.9228° N, 101.6538° E
- Why this location: Established DC hub, lower flood risk — contrasts with Kulai site.

### Financials (Fictional)

| Metric | 2023 | 2024 (proj) | 2025 (proj) |
|--------|------|-------------|-------------|
| Revenue (RM mil) | 180 | 420 | 680 |
| EBITDA (RM mil) | 72 | 185 | 310 |
| Capex (RM mil) | 800 | 650 | 400 |
| Occupancy rate | 65% | 78% | 90% |

### ESG Profile (Deliberately Incomplete)

- Power source: TNB grid (Malaysia ~60% fossil fuel)
- Scope 2 emissions: Not disclosed (agent should flag)
- Water usage for cooling: "Industry standard" (vague — agent should flag)
- Renewable energy plan: 20MW rooftop solar "under consideration"
- Proximity to sensitive areas: Near Sungai Skudai wetlands (agent should flag)

---

## 3. Architecture

### Three Layers

```
Deal PDF
  → Layer 1: Document Intelligence Agent
    → Parse, extract entities, geocode
      → Layer 2: Climate Risk Engine
        → Flood risk (JRC), transition risk (NGFS), biodiversity check
          → Layer 3: Report Generator
            → Memo (DOCX/HTML) + Interactive Map (Folium)
```

### Layer 1 — Document Intelligence Agent

- **Orchestrator:** Simple Python script with Claude API tool-calling (no LangGraph/LangChain)
- **Agent loop:** while loop with tool dispatch — Claude decides which tool to call next
- **Input:** Deal PDF (fictional, self-generated)

**Tools the agent calls:**

| Tool | Library | Purpose |
|------|---------|---------|
| `parse_document` | `unstructured` or `pymupdf` | Extract text from PDF, classify sections |
| `extract_entities` | `spacy` (en_core_web_sm) or Claude NER via prompt | Pull company names, locations, financials, dates |
| `geocode_address` | Nominatim (OpenStreetMap) | Convert addresses to lat/lon. Free, no API key. |
| `validate_financials` | Custom logic | Cross-check figures across document sections |

### Layer 2 — Climate Risk Engine

Triggered by agent once physical assets are geocoded.

**Tools:**

| Tool | Library/Data | Purpose |
|------|-------------|---------|
| `assess_flood_risk` | `rasterio` + JRC GeoTIFF | Query flood depth at asset lat/lon for 10yr/50yr/100yr/500yr return periods |
| `assess_transition_risk` | Hardcoded NGFS lookup table | Score by sector (data centre = high energy, high transition risk) |
| `check_biodiversity` | `geopandas` + WDPA shapefile | Proximity to protected areas / wetlands |
| `generate_map` | `folium` | Interactive map with asset markers + flood risk overlay |

**Returns:** Structured risk scores + map HTML back to agent.

### Layer 3 — Report Generator

- Agent synthesizes all findings into structured memo
- **Output format:** Markdown → DOCX (via python-docx) or standalone HTML
- **Sections:**
  1. Executive Summary
  2. Deal Overview
  3. Asset Description & Location Analysis
  4. Climate Risk Assessment (with embedded map or link)
  5. ESG Gap Analysis
  6. Red Flags & Recommendations

---

## 4. Open Data Resources

### Must-Have

| Resource | What | Format | Size Consideration |
|----------|------|--------|--------------------|
| **JRC Global Flood Maps** | Flood depth at various return periods | GeoTIFF rasters | PRE-CLIP to Peninsular Malaysia only. Keep ~50MB tile covering Johor + Selangor. Do NOT download global dataset. |
| **Nominatim API** | Geocoding | REST API | Free, no key, rate-limited (1 req/sec). For demo, hardcode fallback coordinates. |

### Nice-to-Have

| Resource | What | Format | Notes |
|----------|------|--------|-------|
| WDPA (Protected Planet) | Protected areas / Ramsar wetlands | Shapefile | Clip to Malaysia only |
| NGFS scenarios | Transition risk by sector | Published tables | Hardcode as Python dict — no need for API |
| Malaysia building footprints | Global Building Atlas | GeoJSON | Asset validation, visual context on map |
| OpenDOSM | District-level economic data | CSV/API | Context enrichment (optional) |

### Data Preparation (Do Before Phone Development)

1. Download JRC flood map tiles for Peninsular Malaysia (RP10, RP100, RP500)
2. Clip to bounding box: lat 1.2-6.8, lon 99.5-104.5
3. Upload clipped rasters to VPS
4. Download WDPA Malaysia extract
5. Prepare NGFS lookup table as JSON/Python dict

---

## 5. Tech Stack

### Core Dependencies

```
# Python packages
anthropic          # Claude API for agent orchestration
pymupdf            # PDF parsing (lighter than unstructured)
spacy              # NER (optional — Claude can do this via prompting)
rasterio           # Read JRC GeoTIFF rasters
geopandas          # Geospatial operations, WDPA
folium             # Interactive maps
shapely            # Geometry operations
pyproj             # Coordinate transforms
python-docx        # Report generation (DOCX output)
# OR jinja2        # Report generation (HTML output)
```

### Not Using

- **LangChain/LangGraph** — overkill for this scope. Simple while loop with tool dispatch.
- **Streamlit** — nice but adds complexity. Demo via terminal + output files.
- **GPU anything** — all CPU, runs on VPS.
- **Docker** — unnecessary for a demo.
- **Database** — all in-memory / file-based.

### Agent Design

```python
# Pseudocode for agent loop
tools = {
    "parse_document": parse_document,
    "extract_entities": extract_entities,
    "geocode_address": geocode_address,
    "assess_flood_risk": assess_flood_risk,
    "assess_transition_risk": assess_transition_risk,
    "check_biodiversity": check_biodiversity,
    "generate_map": generate_map,
    "generate_report": generate_report,
}

messages = [{"role": "user", "content": system_prompt + document_text}]

while True:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        tools=tool_definitions,
        messages=messages,
    )
    
    if response.stop_reason == "end_turn":
        break
    
    # Execute tool calls, append results to messages
    for block in response.content:
        if block.type == "tool_use":
            result = tools[block.name](**block.input)
            messages.append(tool_result(block.id, result))
```

---

## 6. Project Structure

```
cadi/
├── CLAUDE.md              # Claude Code project instructions
├── pyproject.toml         # uv project config
├── README.md
├── data/
│   ├── jrc/               # Pre-clipped flood rasters
│   ├── wdpa/              # Malaysia protected areas
│   ├── ngfs/              # Transition risk lookup (JSON)
│   └── deal/              # Fictional deal PDF
├── src/
│   ├── agent.py           # Main agent loop + orchestrator
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── document.py    # PDF parsing + entity extraction
│   │   ├── geocode.py     # Nominatim geocoding with fallback
│   │   ├── flood_risk.py  # JRC raster querying
│   │   ├── transition.py  # NGFS sector risk lookup
│   │   ├── biodiversity.py # WDPA proximity check
│   │   └── mapping.py     # Folium map generation
│   ├── report.py          # Memo generation (markdown/DOCX/HTML)
│   └── schemas.py         # Pydantic models for tool I/O
├── templates/
│   └── memo_template.md   # Report template with Jinja2 placeholders
├── output/                # Generated memos and maps
├── scripts/
│   ├── generate_deal_pdf.py  # Creates the fictional deal document
│   └── prep_geodata.py       # Clips JRC/WDPA to Malaysia extent
└── tests/
    ├── test_geocode.py
    ├── test_flood_risk.py
    └── test_agent.py
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | None (raw Claude API tool-calling) | Simpler to debug on phone, no framework overhead, cleaner demo |
| PDF parsing | `pymupdf` over `unstructured` | Lighter install, sufficient for known document structure |
| NER approach | Claude via prompting over spaCy | One fewer dependency, better at Malaysian entity formats (SSM numbers, Malay place names) |
| Map library | `folium` | HTML output, no server needed, embeds in report |
| Report format | Markdown → HTML (primary), DOCX (optional) | HTML is self-contained, viewable anywhere. DOCX as bonus. |
| Flood data | JRC over Fathom | Fully open, you already know it, sufficient for demo |
| Geocoding | Nominatim + hardcoded fallbacks | No API key. Fallbacks ensure demo never fails on geocoding. |
| Risk scoring | Simple categorical (Low/Medium/High/Critical) | Audience understands traffic lights. No need for continuous scores. |

---

## 8. Build Plan (Phone-First via SSH + Claude Code)

### Phase 1 — Skeleton (Day 1)

- [ ] Create GitHub private repo
- [ ] Set up project structure with uv
- [ ] Write CLAUDE.md with project conventions
- [ ] Create pyproject.toml with all dependencies
- [ ] Write Pydantic schemas for tool inputs/outputs

### Phase 2 — Fictional Deal Document (Day 1)

- [ ] Write `generate_deal_pdf.py` to produce the Nusantara Digital deal PDF
- [ ] Include all details from Section 2 above
- [ ] Ensure extractable text (not images of text)
- [ ] Review PDF looks realistic

### Phase 3 — Individual Tools (Day 2-3)

Build and test each tool independently:

- [ ] `document.py` — parse PDF, extract text by section
- [ ] `geocode.py` — Nominatim lookup with hardcoded fallback coordinates
- [ ] `flood_risk.py` — query JRC raster at given lat/lon, return depths by return period
- [ ] `transition.py` — NGFS lookup by sector code
- [ ] `biodiversity.py` — distance to nearest WDPA polygon
- [ ] `mapping.py` — generate folium map with markers + flood overlay
- [ ] Unit tests for each tool

### Phase 4 — Agent Orchestration (Day 3-4)

- [ ] Write tool definitions for Claude API
- [ ] Implement agent loop in `agent.py`
- [ ] System prompt instructs agent on workflow and tool selection logic
- [ ] Test end-to-end with deal PDF
- [ ] Add human-readable logging so demo shows agent "thinking"

### Phase 5 — Report Generation (Day 4-5)

- [ ] Create memo template (Jinja2 markdown)
- [ ] Implement report generation from agent's collected findings
- [ ] Embed or link map HTML in report
- [ ] Generate DOCX version (stretch goal)

### Phase 6 — Polish & Record (Day 5-6)

- [ ] End-to-end run, fix edge cases
- [ ] Add timing/progress indicators for demo visibility
- [ ] Screen record successful run
- [ ] Prepare 2-minute narration script
- [ ] Record backup video

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Live demo fails | Pre-record a backup video. Always have it ready. |
| Geocoding API timeout | Hardcode fallback coordinates for both sites |
| JRC raster file too large | Pre-clip to 50MB covering Johor + Selangor only |
| Claude API rate limit / timeout | Cache a successful agent run's output. Demo can replay from cache. |
| Panel thinks "we need a manager, not a coder" | Frame as "this is what my team would deliver in 6 months." Show roadmap + team structure alongside demo. |
| IP concerns with BNM data | 100% fictional data. Zero BNM connection. State this explicitly. |
| Phone development too slow | Prioritise: tools first, agent second, report last. Each phase produces something testable. |
| spaCy model download fails on VPS | Skip spaCy entirely, use Claude for NER via tool prompts |

---

## 10. Demo Script (2 Minutes)

**0:00-0:15** — "This is CADI — Climate-Aware Deal Intelligence. It takes a deal document and automatically produces a climate-risk-integrated due diligence assessment."

**0:15-0:45** — Show the input PDF briefly. Run the agent. Show agent tool calls appearing in terminal (parse → extract → geocode → flood risk → transition risk → biodiversity → map → report).

**0:45-1:15** — Show the output map. Zoom into Kulai site. "The agent identified that the primary site sits in a JRC 100-year flood zone. It also flagged proximity to Sungai Skudai wetlands."

**1:15-1:45** — Show the generated memo. Highlight the risk scoring table and the ESG gap flags. "The agent automatically identified that Scope 2 emissions and water usage were not adequately disclosed."

**1:45-2:00** — "This was built in [X] days using open data and open-source tools. With a team of 3-4 data scientists, EPF could operationalise this across its entire private markets pipeline within 6 months."

---

## 11. Interview Framing

This demo is NOT the pitch. It supports the pitch. The pitch is:

1. **EPF needs a data science capability for private markets** — manual DD is slow, climate risk is increasingly mandated, alternative data is untapped
2. **Here's what that capability looks like** — [show demo]
3. **Here's the 12-month roadmap** — Phase 1: aggregated analytics (quick wins). Phase 2: agentic DD pipeline. Phase 3: member analytics + engagement
4. **Here's the team I'd build** — 2 data engineers, 2 data scientists, 1 ML engineer, embedded with investment teams
5. **Here's how I know this works** — [reference BNM experience, synthetic data work, privacy frameworks]

The demo proves you can execute. The roadmap proves you can lead.

---

## 12. Stretch Goals (If Time Permits)

- Side-by-side comparison of two deal sites (Kulai vs Cyberjaya risk profiles)
- Integration with Malaysia's SSM company registry (MYDATA) for entity verification
- Cost-of-risk calculation: estimated insurance premium uplift due to flood exposure
- Carbon footprint estimate based on TNB grid emission factor × projected power consumption

---

## 14. Vercel Web Demo (Priority Feature)

**Goal:** Live web demo at a single Vercel URL — user clicks "Run Analysis", watches pipeline process step-by-step, then views the map and memo in-browser.

### Architecture

```
Vercel (single deploy)
├── web/index.html         — Plain HTML/JS frontend, no framework
├── api/index.py           — FastAPI app (Vercel Python serverless)
│   └── GET /run           — SSE endpoint: streams pipeline steps live
└── vercel.json            — Routes: /api/* → Python, /* → static web/
```

### User Flow

1. Page loads with "Run Analysis" button (pre-loaded Nusantara Digital PDF)
2. Click → SSE stream opens, steps appear one by one in terminal-style log:
   ```
   ✓ Step 1/7 — Parsing deal document...
   ✓ Step 2/7 — Geocoding: Kulai (1.6580, 103.6000) [fallback]
   ⚠ Step 3/7 — Flood risk: Kulai HIGH (RP100=1.5m)
   ⚠ Step 4/7 — Biodiversity: Kulai flagged (4.2km from wetlands)
   ✓ Step 5/7 — Transition risk: Data Centre → High
   ✓ Step 6/7 — Map generated
   ✓ Step 7/7 — Memo generated
   ```
3. Results appear below: tabs for **[ Map ]** and **[ Memo ]**
   - Map tab: folium HTML embedded in iframe
   - Memo tab: rendered HTML memo inline

### Key Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Backend framework | FastAPI | SSE support, Vercel Python runtime compatible |
| Streaming | Server-Sent Events (SSE) | Simple, no websocket overhead, works in plain HTML |
| Frontend | Plain HTML/JS | No build step, no framework, instant deploy |
| Heavy deps (rasterio, geopandas) | Excluded from web deploy | All tools use fallbacks — not needed at runtime |
| PDF | Pre-bundled in repo | Demo must never fail on upload issues |

### New Files Required

```
web/
└── index.html             — Frontend UI
api/
└── index.py               — FastAPI SSE endpoint
requirements-web.txt       — Slim deps for Vercel (no rasterio/geopandas)
vercel.json                — Routing config
```

### Dependencies (requirements-web.txt)

```
fastapi
uvicorn
pymupdf
folium
shapely
pydantic
jinja2
requests
markdown
sse-starlette
python-multipart
```

### Demo Script Integration

The Vercel URL replaces the terminal screen-record for the demo. Show the browser instead — more polished, shareable after the interview.

---

## 13. CLAUDE.md for This Project

```markdown
# CADI — Climate-Aware Deal Intelligence

## Project Context
Demo prototype for EPF interview. Agentic pipeline: deal PDF → entity extraction → climate risk → DD memo.

## Stack
- Python 3.11+, managed by uv
- Linting: ruff
- Testing: pytest
- Type checking: Pydantic models for all tool I/O

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
- pytest tests/
- Each tool has independent unit tests
- Mock external APIs (Nominatim) in tests

## Important
- ALL deal data is fictional. Zero real financial data.
- Geocoding has hardcoded fallbacks — demo must never fail on API timeout.
- JRC rasters are pre-clipped to Peninsular Malaysia only.
```

---

## 15. GLM Task Breakdown — G5–G7 (Vercel Web Layer)

These tasks implement the Vercel demo described in Section 14.
**Prerequisite:** Section 14 fully read before starting. Branch: `claude/check-progress-9GSr5`.

---

### G5 — Slim requirements + FastAPI SSE backend

**File:** `api/index.py`
**File:** `requirements-web.txt`

Create `requirements-web.txt` with only what the web layer needs (no rasterio/geopandas):

```
fastapi
uvicorn
sse-starlette
pymupdf
folium
shapely
pydantic>=2.0.0
jinja2
requests
markdown
python-multipart
fpdf2
```

Create `api/index.py` — FastAPI app with one SSE endpoint:

```python
GET /api/run
```

- Streams pipeline steps as SSE events using `sse-starlette`
- Each event: `{"step": 3, "total": 7, "message": "Flood risk: Kulai HIGH ⚠️", "done": false}`
- Final event includes: `{"done": true, "map_html": "<folium html...>", "memo_html": "<memo html...>"}`
- Uses the existing `src/` pipeline internally — import and call `run_agent_sse()` variant
- PDF is pre-bundled at `data/deal/nusantara_digital.pdf` — no upload needed

**Important:** The SSE variant of the pipeline must `yield` step events rather than using `rich` console output. Add a `run_agent_sse()` generator function to `src/agent.py` alongside the existing `run_agent()`.

---

### G6 — Vercel config + routing

**File:** `vercel.json`

```json
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "web/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "web/$1" }
  ]
}
```

Ensure `web/` is served as static files and `api/` routes to Python.

---

### G7 — Frontend UI

**File:** `web/index.html`

Single-file plain HTML/JS — no framework, no build step. Sections:

1. **Header:** "CADI — Climate-Aware Deal Intelligence" + subtitle
2. **Run button:** "Analyse Nusantara Digital" → calls `GET /api/run` via EventSource
3. **Terminal log panel:** Steps stream in one by one with icons (✓ / ⚠ / spinner)
   - Each SSE event appends a line
   - Auto-scrolls to bottom
4. **Results tabs** (hidden until stream completes):
   - **Map** tab: `<iframe>` containing the folium HTML (injected via `srcdoc`)
   - **Memo** tab: `<div>` with memo HTML injected directly
5. **Styling:** Dark terminal panel for logs, clean white card for results. No external CSS frameworks — inline `<style>` only.

**UX requirement:** Results tabs must only appear after `done: true` event received. Map iframe height: 500px. Memo div should be scrollable with max-height.

---

### G5–G7 Acceptance Criteria

- [ ] `vercel --prod` deploys without error
- [ ] Clicking "Analyse" streams all 7 steps visibly
- [ ] Map tab shows Kulai (red marker) and Cyberjaya (green marker)
- [ ] Memo tab shows company name, risk table, ESG gaps, red flags
- [ ] Page works on mobile (basic responsive)
- [ ] No console errors in browser
