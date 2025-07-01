"""Grid visualization for life weeks tracking."""

from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from ..core.life_tracker import get_weeks_lived
from ..utils.config import (
    CELL_SIZE,
    COLORS,
    FONT_SIZE,
    MAX_YEARS,
    PADDING,
    WEEKS_PER_YEAR,
)


def calculate_grid_dimensions() -> Tuple[int, int]:
    """Calculate the dimensions of the visualization grid.

    :returns: Tuple of (width, height) in pixels.
    :rtype: Tuple[int, int]
    """
    width = (WEEKS_PER_YEAR * CELL_SIZE) + (2 * PADDING)
    height = (MAX_YEARS * CELL_SIZE) + (2 * PADDING)
    return width, height


def generate_visualization(birth_date: str) -> BytesIO:
    """Generate a visual representation of weeks lived.

    Creates a grid where:
    - Each cell represents one week
    - Each row represents one year (52 weeks)
    - Green cells represent weeks lived
    - Empty cells represent weeks not yet lived
    - Years are labeled on the vertical axis
    - Weeks are labeled on the horizontal axis (every 4th week)
    - A legend is included at the bottom

    :param birth_date: Birth date in YYYY-MM-DD format
    :type birth_date: str
    :returns: BytesIO object containing the generated image.
    :rtype: BytesIO
    """
    width, height = calculate_grid_dimensions()
    image = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(image)

    # Draw grid and cells
    weeks_lived = get_weeks_lived(birth_date)
    current_week = 0

    # Prepare font
    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    # Draw vertical axis (years)
    for year in range(MAX_YEARS):
        y = PADDING + (year * CELL_SIZE)
        draw.text((5, y), str(year), fill=COLORS["axis"], font=font)

    # Draw horizontal axis (weeks)
    for week in range(0, WEEKS_PER_YEAR, 4):  # Label every 4th week
        x = PADDING + (week * CELL_SIZE)
        draw.text((x, 5), str(week + 1), fill=COLORS["axis"], font=font)

    # Draw cells
    for year in range(MAX_YEARS):
        for week in range(WEEKS_PER_YEAR):
            x = PADDING + (week * CELL_SIZE)
            y = PADDING + (year * CELL_SIZE)
            # Draw cell border
            draw.rectangle(
                [x, y, x + CELL_SIZE - 1, y + CELL_SIZE - 1], outline=COLORS["grid"]
            )
            # Fill cell if week has been lived
            if current_week < weeks_lived:
                draw.rectangle(
                    [x + 1, y + 1, x + CELL_SIZE - 2, y + CELL_SIZE - 2],
                    fill=COLORS["lived"],
                )
            current_week += 1

    # Add legend
    legend_y = height - PADDING + 10
    draw.rectangle(
        [PADDING, legend_y, PADDING + 20, legend_y + 20], fill=COLORS["lived"]
    )
    draw.text((PADDING + 30, legend_y), "Weeks Lived", fill=COLORS["text"], font=font)

    # Save to BytesIO
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr
