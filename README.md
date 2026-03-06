# CADI — Climate-Aware Deal Intelligence

Agentic Due Diligence Pipeline for EPF Private Markets

**Purpose:** Demo-ready prototype for EPF Centre of Excellence for Analytics interview.

## What It Does

Takes a fictional private equity deal document (PDF), runs an agentic pipeline that:

1. Parses and extracts key entities (company, assets, locations, financials)
2. Geocodes physical asset locations
3. Assesses climate/flood risk per asset using open geospatial data
4. Scores transition risk by sector using NGFS scenarios
5. Generates a structured due diligence memo with embedded interactive map
6. Flags ESG gaps and red flags

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the agent
python -m src.agent --input data/deal/nusantara_digital.pdf --output output/
```

## Project Structure

```
cadi/
├── data/
│   ├── jrc/          # Pre-clipped JRC flood rasters
│   ├── wdpa/         # Malaysia protected areas
│   ├── ngfs/         # Transition risk lookup (JSON)
│   └── deal/         # Fictional deal PDF
├── src/
│   ├── agent.py      # Main agent loop
│   ├── tools/        # Individual tools
│   ├── report.py     # Memo generation
│   └── schemas.py    # Pydantic models
├── templates/        # Jinja2 templates
├── output/           # Generated reports
├── scripts/          # Utility scripts
└── tests/            # Unit tests
```

## License

MIT

## Disclaimer

**ALL deal data is fictional.** Zero real financial data. For demonstration purposes only.
