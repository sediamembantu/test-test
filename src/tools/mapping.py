"""
Interactive map generation using Folium.
"""

from __future__ import annotations

from pathlib import Path

import folium

from ..schemas import Asset, MapInput, MapOutput


def generate_map(input_data: MapInput) -> MapOutput:
    """
    Generate an interactive map with asset markers.

    Args:
        input_data: MapInput with assets and options

    Returns:
        MapOutput with path to generated HTML map
    """
    assets = input_data.assets

    if not assets:
        raise ValueError("No assets to map")

    # Filter assets with coordinates
    valid_assets = [a for a in assets if a.latitude is not None and a.longitude is not None]

    if not valid_assets:
        raise ValueError("No assets with valid coordinates")

    # Calculate center point
    lats = [a.latitude for a in valid_assets]
    lons = [a.longitude for a in valid_assets]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="cartodbpositron",
    )

    # Add markers for each asset
    for asset in valid_assets:
        popup_html = f"""
        <b>{asset.name}</b><br>
        <i>{asset.address}</i><br>
        Capacity: {asset.capacity_mw or 'N/A'} MW<br>
        Status: {asset.status or 'Unknown'}
        """
        folium.Marker(
            location=[asset.latitude, asset.longitude],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=asset.name,
            icon=folium.Icon(color="blue", icon="building", prefix="fa"),
        ).add_to(m)

    # TODO: Add flood risk overlay if requested
    # if input_data.flood_data:
    #     _add_flood_overlay(m)

    # Fit bounds to include all markers
    bounds = (min(lats), min(lons), max(lats), max(lons))
    m.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]], padding=20)

    # Save map
    output_path = Path(input_data.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_path))

    return MapOutput(
        map_path=str(output_path),
        asset_count=len(valid_assets),
        bounds=bounds,
    )
