#!/usr/bin/env python3
"""
Add text annotations and labels to existing Plotly HTML visualizations.
Reads an HTML file, adds annotations, and saves a new version.

Usage: python3 add_annotations.py <input.html> <output.html>
"""

import sys
import re
from pathlib import Path


def add_world_annotations(html_content):
    """Add annotations for world map visualizations."""

    # Define key points to label (lon, lat, text, color)
    annotations = [
        # Major population peaks
        (116.4, 39.9, "Beijing/Tianjin<br>100M+ people", "cyan"),
        (121.5, 31.2, "Shanghai<br>Yangtze Delta", "cyan"),
        (139.7, 35.7, "Tokyo<br>40M people", "cyan"),
        (-74.0, 40.7, "NYC<br>Northeast Corridor", "cyan"),
        (-118.2, 34.1, "Los Angeles", "lightgreen"),
        (77.2, 28.6, "Delhi/NCR", "cyan"),
        (88.4, 22.6, "Kolkata/Bengal", "lightgreen"),
        (2.3, 48.9, "Paris/Europe", "lightgreen"),

        # Point Nemo (the wedge!)
        (-123.4, -48.9, "⬇ POINT NEMO<br>Most isolated point<br>on Earth", "yellow"),

        # Other interesting features
        (-100.0, 40.0, "Great Plains<br>(low potential)", "orange"),
        (45.0, 25.0, "Empty Quarter<br>Desert", "orange"),
    ]

    # Build Plotly annotation JSON
    annotation_json = "[\n"
    for lon, lat, text, color in annotations:
        annotation_json += f"""        {{
            x: {lon},
            y: {lat},
            text: "{text}",
            showarrow: true,
            arrowhead: 2,
            arrowsize: 1,
            arrowwidth: 2,
            arrowcolor: "{color}",
            ax: 40,
            ay: -40,
            font: {{
                size: 12,
                color: "{color}",
                family: "Arial, sans-serif"
            }},
            bgcolor: "rgba(0,0,0,0.7)",
            bordercolor: "{color}",
            borderwidth: 1,
            borderpad: 4
        }},\n"""
    annotation_json += "    ]"

    return annotation_json


def add_usa_annotations(html_content):
    """Add annotations for USA-specific visualizations."""

    annotations = [
        # Major US cities
        (-74.0, 40.7, "NYC-Boston<br>Megalopolis", "cyan"),
        (-87.6, 41.9, "Chicago", "lightgreen"),
        (-118.2, 34.1, "Los Angeles", "lightgreen"),
        (-122.4, 37.8, "SF Bay Area", "lightgreen"),
        (-95.4, 29.8, "Houston", "lightgreen"),
        (-104.9, 39.7, "Denver<br>(High Plains)", "yellow"),
        (-112.1, 33.4, "Phoenix<br>(Desert)", "yellow"),

        # Interesting low points
        (-117.0, 38.0, "Great Basin<br>Desert Valley", "orange"),
        (-100.0, 45.0, "Northern Plains<br>(Low Potential)", "orange"),
    ]

    annotation_json = "[\n"
    for lon, lat, text, color in annotations:
        annotation_json += f"""        {{
            x: {lon},
            y: {lat},
            text: "{text}",
            showarrow: true,
            arrowhead: 2,
            ax: 30,
            ay: -30,
            font: {{
                size: 11,
                color: "{color}"
            }},
            bgcolor: "rgba(0,0,0,0.7)",
            bordercolor: "{color}",
            borderwidth: 1
        }},\n"""
    annotation_json += "    ]"

    return annotation_json


def inject_annotations(html_content, annotation_type='world'):
    """Inject annotations into Plotly HTML."""

    # Generate appropriate annotations
    if annotation_type == 'usa':
        annotations_json = add_usa_annotations(html_content)
    else:
        annotations_json = add_world_annotations(html_content)

    # Find the Plotly.newPlot call and inject annotations
    # Look for the layout object
    pattern = r'(var\s+layout\s*=\s*\{[^}]*)(}\s*;)'

    def add_annotations_to_layout(match):
        layout_start = match.group(1)
        layout_end = match.group(2)

        # Check if annotations already exist
        if 'annotations' in layout_start:
            print("Warning: Annotations already exist in this file")
            return match.group(0)

        # Add annotations before the closing brace
        return f"{layout_start},\n    annotations: {annotations_json}{layout_end}"

    # Try to inject
    modified_html = re.sub(pattern, add_annotations_to_layout, html_content, flags=re.DOTALL)

    # If that didn't work, try alternative pattern
    if modified_html == html_content:
        # Look for scene object instead (for 3D plots)
        pattern2 = r'(scene\s*:\s*\{[^}]*)(}\s*,)'
        # For 3D plots, we need to add scene.annotations
        # Actually, Plotly 3D doesn't support annotations the same way
        # Let's add a title instead
        if 'world' in html_content.lower() or 'usa' in html_content.lower():
            pattern3 = r'(var\s+layout\s*=\s*\{)'
            modified_html = re.sub(
                pattern3,
                r'\1\n    title: {text: "Population Potential Field - Height shows gravitational pull of nearby populations", font: {size: 16}},',
                html_content
            )

    return modified_html


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 add_annotations.py <input.html> <output.html> [world|usa]")
        print()
        print("Example:")
        print("  python3 add_annotations.py output/world.html output/world_annotated.html world")
        print("  python3 add_annotations.py output/usa.html output/usa_annotated.html usa")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    annotation_type = sys.argv[3] if len(sys.argv) > 3 else 'world'

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Read input HTML
    print(f"Reading {input_file}...")
    with open(input_file, 'r') as f:
        html_content = f.read()

    # Inject annotations
    print(f"Adding {annotation_type} annotations...")
    modified_html = inject_annotations(html_content, annotation_type)

    # Write output
    print(f"Writing {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(modified_html)

    print("✓ Done!")
    print()
    print(f"Open {output_file} to see annotated visualization")


if __name__ == "__main__":
    main()
