# CADI Data Directory

This directory contains geospatial and reference data for the CADI pipeline.

## Directory Structure

```
data/
├── deal/          # Fictional deal documents (PDFs)
├── jrc/           # JRC Global Flood Maps (GeoTIFF)
├── wdpa/          # WDPA Protected Areas (GeoPackage/Shapefile)
└── ngfs/          # NGFS Transition Risk Lookup (JSON)
```

## Data Status

| Directory | Required | Status | Notes |
|-----------|----------|--------|-------|
| deal/ | ✅ Yes | ✅ Populated | Contains nusantara_digital.pdf |
| jrc/ | Optional | 🔲 Empty | Uses location-aware fallback |
| wdpa/ | Optional | 🔲 Empty | Uses hardcoded fallback |
| ngfs/ | ✅ Yes | ✅ Populated | Contains ngfs_lookup.json |

## Getting Geospatial Data

### JRC Flood Maps (Optional)

The pipeline works without JRC rasters using location-aware fallback values:
- Johor (lon > 102.5): High flood risk
- Selangor (lon <= 102.5): Low flood risk

To use real data:
```bash
python scripts/prep_geodata.py --download-jrc
```

### WDPA Protected Areas (Optional)

The pipeline works without WDPA data using hardcoded fallback values.

To use real data:
```bash
python scripts/prep_geodata.py --download-wdpa
```

## IMPORTANT

**ALL deal data is fictional.** Zero real financial data.
This is for demonstration purposes only.
