#!/usr/bin/env python3
"""
Prepare geodata for CADI demo.
Clips JRC flood rasters and WDPA protected areas to Malaysia extent.

Usage:
    python scripts/prep_geodata.py --download-jrc
    python scripts/prep_geodata.py --clip-jrc /path/to/global/flood.tif
    python scripts/prep_geodata.py --download-wdpa
"""

import argparse
from pathlib import Path

# Malaysia bounding box (Peninsular only for demo)
MALAYSIA_BBOX = {
    "min_lat": 1.2,
    "max_lat": 6.8,
    "min_lon": 99.5,
    "max_lon": 104.5,
}

DATA_DIR = Path(__file__).parent.parent / "data"
JRC_DIR = DATA_DIR / "jrc"
WDPA_DIR = DATA_DIR / "wdpa"


def clip_jrc_raster(input_path: str, output_name: str, return_period: int):
    """Clip a JRC flood raster to Malaysia extent."""
    try:
        import rasterio
        from rasterio.windows import from_bounds
    except ImportError:
        print("ERROR: rasterio not installed. Run: pip install rasterio")
        return False

    output_path = JRC_DIR / f"{output_name}_rp{return_period}.tif"
    
    with rasterio.open(input_path) as src:
        # Transform bbox to source CRS
        window = from_bounds(
            MALAYSIA_BBOX["min_lon"],
            MALAYSIA_BBOX["min_lat"],
            MALAYSIA_BBOX["max_lon"],
            MALAYSIA_BBOX["max_lat"],
            src.transform,
        )
        
        # Read clipped data
        data = src.read(window=window)
        
        # Update transform for clipped extent
        transform = src.window_transform(window)
        
        # Write output
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=data.shape[1],
            width=data.shape[2],
            transform=transform,
            compress="lzw",
        )
        
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)
    
    print(f"Clipped {input_path} -> {output_path}")
    return True


def download_wdpa_malaysia():
    """Download WDPA Malaysia extract from Protected Planet."""
    import requests
    
    # WDPA API endpoint (this is a placeholder - actual API requires registration)
    # For demo, we'll create a placeholder message
    print("""
    To download WDPA Malaysia data:
    
    1. Visit: https://www.protectedplanet.net/en/thematic-areas/wdpa?tab=WDPA
    2. Select Malaysia from the country filter
    3. Download as Shapefile or GeoPackage
    4. Place the file in: data/wdpa/
    
    Alternative: Use the WDPA API with a registered key.
    """)
    
    # Create placeholder
    placeholder = WDPA_DIR / "README.txt"
    placeholder.write_text("""
    Place WDPA Malaysia extract here.
    
    Required files:
    - wdpa_malaysia.gpkg (GeoPackage)
    OR
    - wdpa_malaysia.shp, .dbf, .shx, .prj (Shapefile)
    
    Download from: https://www.protectedplanet.net/
    """)
    print(f"Created placeholder: {placeholder}")


def download_jrc_flood_maps():
    """Download JRC Global Flood Maps for Malaysia region."""
    print("""
    To download JRC flood maps:
    
    1. Visit: https://data.jrc.ec.europa.eu/collection/id-0054
    2. Select tiles covering Malaysia (SE Asia region)
    3. Download return periods: RP10, RP50, RP100, RP500
    4. Clip to Malaysia extent using: python scripts/prep_geodata.py --clip-jrc
    
    Alternative sources:
    - Copernicus Climate Data Store
    - Google Earth Engine (JRC/GFW/v1)
    
    For demo purposes, the pipeline uses hardcoded fallback values.
    Real JRC data is optional but recommended for production.
    """)
    
    # Create placeholder
    placeholder = JRC_DIR / "README.txt"
    placeholder.write_text("""
    Place clipped JRC flood rasters here.
    
    Expected files:
    - flood_rp10.tif  (10-year return period)
    - flood_rp50.tif  (50-year return period)
    - flood_rp100.tif (100-year return period)
    - flood_rp500.tif (500-year return period)
    
    Each raster should be clipped to Malaysia extent:
    - Latitude: 1.2 to 6.8
    - Longitude: 99.5 to 104.5
    
    Download from: https://data.jrc.ec.europa.eu/collection/id-0054
    """)
    print(f"Created placeholder: {placeholder}")


def main():
    parser = argparse.ArgumentParser(description="Prepare geodata for CADI demo")
    parser.add_argument("--download-jrc", action="store_true", help="Show JRC download instructions")
    parser.add_argument("--download-wdpa", action="store_true", help="Show WDPA download instructions")
    parser.add_argument("--clip-jrc", type=str, metavar="INPUT.tif", help="Clip JRC raster to Malaysia extent")
    parser.add_argument("--return-period", type=int, default=100, help="Return period for clipping (default: 100)")
    parser.add_argument("--output-name", type=str, default="flood", help="Output filename prefix")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    JRC_DIR.mkdir(parents=True, exist_ok=True)
    WDPA_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.download_jrc:
        download_jrc_flood_maps()
    elif args.download_wdpa:
        download_wdpa_malaysia()
    elif args.clip_jrc:
        clip_jrc_raster(args.clip_jrc, args.output_name, args.return_period)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
