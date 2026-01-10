#!/bin/bash
# Generate PWA icons from a source image using ImageMagick
# Usage: ./generate-icons.sh source-image.png

SOURCE_IMAGE=${1:-"../../src/assets/react.svg"}

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is not installed. Please install it first:"
    echo "  Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "  macOS: brew install imagemagick"
    echo ""
    echo "For now, using placeholder blue icons..."

    # Create placeholder blue icons with text
    for size in 72 96 128 144 152 192 384 512; do
        # Create a blue square with white text showing the size
        convert -size ${size}x${size} xc:#2563eb \
                -gravity center \
                -pointsize $((size / 4)) \
                -fill white \
                -annotate +0+0 "AW\n${size}" \
                "icon-${size}x${size}.png"
        echo "Created icon-${size}x${size}.png"
    done

    exit 0
fi

# Generate icons at various sizes
SIZES=(72 96 128 144 152 192 384 512)

for SIZE in "${SIZES[@]}"; do
    convert "$SOURCE_IMAGE" \
        -resize ${SIZE}x${SIZE} \
        -background none \
        -gravity center \
        -extent ${SIZE}x${SIZE} \
        "icon-${SIZE}x${SIZE}.png"
    echo "Generated icon-${SIZE}x${SIZE}.png"
done

echo "Icon generation complete!"
