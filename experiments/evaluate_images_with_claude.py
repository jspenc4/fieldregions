#!/usr/bin/env python3
"""
Script to send multiple PNG images to Claude API for evaluation.
Asks Claude to pick the nicest/best visualization based on aesthetic criteria.
"""

import anthropic
import base64
import os
import sys
from pathlib import Path


def encode_image(image_path):
    """Encode an image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(image_file.read()).decode("utf-8")


def get_image_media_type(image_path):
    """Determine the media type based on file extension."""
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return media_types.get(ext, 'image/png')


def evaluate_images(image_folder, criteria=None):
    """
    Send images to Claude API for evaluation.

    Args:
        image_folder: Path to folder containing images
        criteria: Optional custom evaluation criteria
    """
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # Find all image files in the folder
    image_folder = Path(image_folder)
    if not image_folder.exists():
        print(f"Error: Folder {image_folder} does not exist")
        sys.exit(1)

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

    # Build the message content with all images
    content = []

    # Add each image
    for i, image_path in enumerate(image_files, 1):
        image_data = encode_image(image_path)
        media_type = get_image_media_type(image_path)

        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data,
            },
        })
        content.append({
            "type": "text",
            "text": f"Image {i}: {image_path.name}"
        })

    # Add the evaluation prompt
    if criteria is None:
        criteria = """
Please evaluate these visualizations and pick the nicest one. Consider:
- Visual clarity and readability
- Aesthetic appeal and color choices
- How well the visualization conveys the underlying data
- Overall composition and balance
- Whether the visualization is compelling and interesting

Please:
1. Rank the images from best to worst
2. Explain what makes the top choice stand out
3. Provide specific feedback on what works well and what could be improved for each
"""

    content.append({
        "type": "text",
        "text": criteria
    })

    # Call Claude API
    print("Sending images to Claude API for evaluation...")
    print()

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",  # Use the latest Sonnet model
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]
    )

    # Print Claude's response
    print("=" * 80)
    print("CLAUDE'S EVALUATION:")
    print("=" * 80)
    print()
    print(message.content[0].text)
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python evaluate_images_with_claude.py <image_folder> [criteria]")
        print()
        print("Example:")
        print("  python evaluate_images_with_claude.py output/renders/")
        print()
        print("  python evaluate_images_with_claude.py output/ 'Pick the most 3D-printable visualization'")
        sys.exit(1)

    image_folder = sys.argv[1]
    criteria = sys.argv[2] if len(sys.argv) > 2 else None

    evaluate_images(image_folder, criteria)


if __name__ == "__main__":
    main()
