"""Grid visualization for life weeks tracking."""

from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from ..core.life_calculator import LifeCalculatorEngine
from ..database.models import User
from ..utils.config import (
    CELL_SIZE,
    COLORS,
    FONT_SIZE,
    MAX_YEARS,
    PADDING,
    WEEKS_PER_YEAR,
)
from ..utils.localization import get_message


def calculate_grid_dimensions() -> Tuple[int, int]:
    """Calculate the dimensions of the visualization grid.

    :returns: Tuple of (width, height) in pixels.
    :rtype: Tuple[int, int]
    """
    width = (WEEKS_PER_YEAR * CELL_SIZE) + (2 * PADDING)
    height = (MAX_YEARS * CELL_SIZE) + (2 * PADDING)
    return width, height


def generate_visualization(user: User, lang: str) -> BytesIO:
    """Generate a visual representation of weeks lived.

    Creates a grid where:
    - Each cell represents one week
    - Each row represents one year (52 weeks)
    - Green cells represent weeks lived
    - Empty cells represent weeks not yet lived
    - Years are labeled on the vertical axis
    - Weeks are labeled on the horizontal axis (every 4th week)
    - A legend is included at the bottom

    :param user: User profile object with birth date
    :type user: User
    :param lang: Language code
    :type lang: str
    :returns: BytesIO object containing the generated image.
    :rtype: BytesIO
    """
    # Create calculator instance
    calculator = LifeCalculatorEngine(user=user)
    weeks_lived = calculator.calculate_weeks_lived()

    width, height = calculate_grid_dimensions()
    image = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(image)

    # Draw grid and cells
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

            # Color cell based on whether week has been lived
            if current_week < weeks_lived:
                draw.rectangle(
                    [x, y, x + CELL_SIZE - 1, y + CELL_SIZE - 1],
                    fill=COLORS["lived"],
                    outline=COLORS["grid"],
                )
            else:
                draw.rectangle(
                    [x, y, x + CELL_SIZE - 1, y + CELL_SIZE - 1],
                    fill=COLORS["background"],
                    outline=COLORS["grid"],
                )

            current_week += 1

    # Add legend
    legend_y = height - 30
    legend_text = get_message("command_visualize", "legend", lang)
    draw.text((PADDING, legend_y), legend_text, fill=COLORS["text"], font=font)

    # Convert to BytesIO
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    return img_byte_arr
