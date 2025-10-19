#!/usr/bin/env python3
"""
Create an HTML gallery of images for evaluation via Claude Pro web interface.
Opens the gallery in your browser so you can screenshot and paste into Claude.

Usage: python3 create_image_gallery.py <image_folder> [criteria]
"""

import sys
import base64
from pathlib import Path
import webbrowser


def create_gallery_html(image_folder, criteria=None):
    """Create an HTML gallery with all images and evaluation criteria."""

    image_folder = Path(image_folder)
    if not image_folder.exists():
        print(f"Error: Folder {image_folder} does not exist")
        sys.exit(1)

    # Find all images
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    image_files = sorted([
        f for f in image_folder.iterdir()
        if f.suffix.lower() in image_extensions
    ])

    if not image_files:
        print(f"Error: No image files found in {image_folder}")
        sys.exit(1)

    print(f"Found {len(image_files)} images:")
    for img in image_files:
        print(f"  - {img.name}")
    print()

    # Default criteria
    if criteria is None:
        criteria = """These are 3D visualizations of POPULATION POTENTIAL FIELDS - mathematical models showing how population density creates "gravity wells" across geography, similar to gravitational or electromagnetic potential fields.

Key context:
- Height/color represents the population potential at each point (sum of pop/distance from all census tracts)
- Major cities (NYC, LA, Tokyo, etc.) should appear as clear peaks/hotspots
- Unpopulated areas (deserts, oceans, mountains) should show as valleys with low values
- The "lines in the desert, not on Main Street" principle: grid lines and artifacts should be visible in empty areas, not obscuring population centers
- These may be used for scientific papers, 3D printing, or public engagement

Please evaluate which visualization(s) work BEST as MAPS and ANALYTICAL TOOLS:

1. GEOGRAPHIC CLARITY:
   - Can you identify major population centers and their relative importance?
   - Is the geographic context clear (coastlines, borders, continental shapes)?
   - Does the map tell a story about human settlement patterns?

2. DATA READABILITY:
   - Is the height/color encoding effective for understanding magnitude differences?
   - Can you distinguish between major cities, medium cities, and rural areas?
   - Are the low-value areas (deserts/oceans) clearly differentiated from populated regions?

3. TECHNICAL QUALITY:
   - Are mesh artifacts, grid lines, or triangulation visible? (Bad in cities, OK in deserts)
   - Does the camera angle effectively show both geographic context and 3D relief?
   - Is the color scheme effective or distracting?

4. FITNESS FOR PURPOSE:
   - Scientific publication: Clear, professional, informative
   - 3D printing: Good dynamic range, printable geometry, recognizable when physical
   - Public engagement: Compelling, understandable without expertise, tells a story

Please:
1. Rank images by effectiveness as population maps (not just aesthetic appeal)
2. Identify which image(s) best reveal human geography patterns
3. Note specific cities/regions you can identify in each
4. Explain what works and what fails in each visualization
5. Recommend which would work best for: (a) scientific papers, (b) 3D prints, (c) public talks"""

    # Embed images as base64 (compress PNGs to JPEGs for smaller file size)
    embedded_images = []
    try:
        from PIL import Image
        import io
        has_pil = True
    except ImportError:
        has_pil = False
        print("Note: Install Pillow for image compression (pip3 install Pillow)")

    for img_path in image_files:
        # Try to compress large images
        if has_pil and img_path.suffix.lower() == '.png':
            try:
                img = Image.open(img_path)
                # Resize if very large
                max_size = 1200
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                # Convert to JPEG with compression
                buffer = io.BytesIO()
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert transparent images to white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                img.convert('RGB').save(buffer, format='JPEG', quality=85, optimize=True)
                img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                mime_type = 'image/jpeg'
            except Exception as e:
                print(f"Warning: Could not compress {img_path.name}: {e}")
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                mime_type = 'image/png'
        else:
            with open(img_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            ext = img_path.suffix.lower()
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/png')

        embedded_images.append({
            'name': img_path.name,
            'data': f'data:{mime_type};base64,{img_data}'
        })

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Image Evaluation Gallery</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 20px 0;
            color: #333;
        }}
        .criteria {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
            white-space: pre-wrap;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 14px;
            line-height: 1.6;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .image-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .image-card img {{
            width: 100%;
            height: auto;
            border-radius: 4px;
            display: block;
        }}
        .image-name {{
            margin-top: 10px;
            font-weight: 600;
            color: #333;
            text-align: center;
        }}
        .instructions {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .instructions h2 {{
            margin-top: 0;
            color: #856404;
        }}
        .instructions ol {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .instructions li {{
            margin: 8px 0;
        }}
    </style>
</head>
<body>
    <div class="instructions">
        <h2>📸 How to evaluate with Claude Pro</h2>
        <ol>
            <li>Take a screenshot of this entire page (⌘+Shift+4 on Mac, then press Space to capture window)</li>
            <li>Go to <a href="https://claude.ai" target="_blank">claude.ai</a> in a new tab</li>
            <li>Upload the screenshot and paste the evaluation criteria below</li>
            <li>Claude will analyze all the images and give you detailed feedback!</li>
        </ol>
    </div>

    <div class="header">
        <h1>🎨 Image Evaluation Gallery ({len(image_files)} images)</h1>
        <div class="criteria">
<strong>EVALUATION CRITERIA:</strong>

{criteria}
        </div>
    </div>

    <div class="gallery">
"""

    # Add each image
    for i, img in enumerate(embedded_images, 1):
        html += f"""        <div class="image-card">
            <img src="{img['data']}" alt="{img['name']}">
            <div class="image-name">Image {i}: {img['name']}</div>
        </div>
"""

    html += """    </div>
</body>
</html>
"""

    # Write HTML file
    output_path = Path("output/image_evaluation_gallery.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ Created gallery: {output_path}")
    print()
    print("Opening in your browser...")
    webbrowser.open(output_path.absolute().as_uri())
    print()
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Screenshot the browser window that just opened")
    print("2. Go to https://claude.ai")
    print("3. Upload the screenshot")
    print("4. Copy/paste the evaluation criteria shown in the page")
    print("5. Claude will analyze all images and rank them!")
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_image_gallery.py <image_folder> [criteria]")
        print()
        print("Example:")
        print("  python3 create_image_gallery.py ~/Desktop/")
        print("  python3 create_image_gallery.py output/ 'Pick the most 3D-printable visualization'")
        sys.exit(1)

    image_folder = sys.argv[1]
    criteria = sys.argv[2] if len(sys.argv) > 2 else None

    create_gallery_html(image_folder, criteria)


if __name__ == "__main__":
    main()
