"""
Interactive map generation using Folium.
"""

from __future__ import annotations

from pathlib import Path

import folium

from ..schemas import Asset, MapInput, MapOutput

# Risk level to color mapping
RISK_COLOURS = {
    "Critical": "darkred",
    "High": "red",
    "Medium": "orange",
    "Low": "green",
}


def generate_map(input_data: MapInput) -> MapOutput:
    """
    Generate an interactive map with asset markers and risk-colored circles.

    Args:
        input_data: MapInput with assets, flood_risks, and options

    Returns:
        MapOutput with path to generated HTML map
    """
    assets = input_data.assets
    flood_risks = input_data.flood_risks or []

    if not assets:
        raise ValueError("No assets to map")

    # Filter assets with coordinates
    valid_assets = [a for a in assets if a.latitude is not None and a.longitude is not None]

    if not valid_assets:
        raise ValueError("No assets with valid coordinates")

    # Build risk lookup: asset_name → risk_level
    risk_lookup = {
        r.get("asset_name", ""): r.get("risk_level", "Medium")
        for r in flood_risks
    }

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
        risk_level = risk_lookup.get(asset.name, "Medium")
        colour = RISK_COLOURS.get(risk_level, "orange")

        # Popup content
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <b style="font-size: 14px;">{asset.name}</b><br>
            <i style="color: #666;">{asset.address}</i><br>
            <hr style="margin: 5px 0;">
            <b>Capacity:</b> {asset.capacity_mw or 'N/A'} MW<br>
            <b>Status:</b> {asset.status or 'Unknown'}<br>
            <b>Flood Risk:</b> <span style="color: {colour}; font-weight: bold;">{risk_level}</span>
        </div>
        """

        # Add standard marker
        folium.Marker(
            location=[asset.latitude, asset.longitude],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=asset.name,
            icon=folium.Icon(color="blue", icon="building", prefix="fa"),
        ).add_to(m)

        # Add risk-colored circle marker
        folium.CircleMarker(
            location=[asset.latitude, asset.longitude],
            radius=20,
            color=colour,
            fill=True,
            fill_color=colour,
            fill_opacity=0.3,
            popup=f"{asset.name}: {risk_level} flood risk",
        ).add_to(m)

    # Add legend
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
