"""Grid visualization for life weeks tracking."""

from io import BytesIO
from typing import Any, Tuple

from PIL import Image, ImageDraw, ImageFont

from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import user_service
from ..utils.config import (
    CELL_SIZE,
    COLORS,
    DEFAULT_LANGUAGE,
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


async def generate_visualization(user_info: Any) -> BytesIO:
    """Generate a visual representation of weeks lived.

    Creates a grid where:
    - Each cell represents one week
    - Each row represents one year (52 weeks)
    - Green cells represent weeks lived
    - Empty cells represent weeks not yet lived
    - Years are labeled on the vertical axis
    - Weeks are labeled on the horizontal axis (every 4th week)
    - A legend is included at the bottom

    This function accepts either a database ``User`` (with ``telegram_id``),
    a Telegram ``User`` (with ``id``), or a raw ``int`` user ID.

    :param user_info: DB ``User`` | Telegram ``User`` | ``int`` user id
    :type user_info: Any
    :returns: BytesIO object containing the generated image.
    :rtype: BytesIO
    :raises TypeError: If ``user_info`` is not a supported type
    :raises ValueError: If user profile cannot be found in the database
    """
    # Resolve user id from various supported inputs
    if hasattr(user_info, "telegram_id"):
        user_id: int = int(getattr(user_info, "telegram_id"))
    elif hasattr(user_info, "id"):
        user_id = int(getattr(user_info, "id"))
    elif isinstance(user_info, int):
        user_id = user_info
    else:
        raise TypeError(
            "generate_visualization expects DB User (telegram_id), Telegram User (id), or int user id"
        )

    # Resolve complete user profile and language
    user_profile = await user_service.get_user_profile(telegram_id=user_id)
    if not user_profile:
        raise ValueError(f"User profile not found for telegram_id: {user_id}")
    user_lang: str = (
        user_profile.settings.language
        if user_profile
        and getattr(user_profile, "settings", None)
        and getattr(user_profile.settings, "language", None)
        else DEFAULT_LANGUAGE
    )

    # Create calculator instance
    calculator = LifeCalculatorEngine(user=user_profile)
    weeks_lived: int = calculator.calculate_weeks_lived()

    width, height = calculate_grid_dimensions()
    image = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(image)

    # Draw grid and cells
    current_week = 0

    # Prepare fonts
    font = _load_font(size=FONT_SIZE)
    small_font = _load_font(size=max(10, int(FONT_SIZE * 0.85)))

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

    # Add legend with colored markers (avoid emojis to ensure wide font support)
    legend_y = height - 30

    # Use gettext for localization
    from ..i18n import use_locale

    _, _, pgettext = use_locale(user_lang)
    legend_text: str = pgettext("visualize.legend", "🟩 Lived weeks | ⬜ Future weeks")

    lived_label, future_label = _parse_legend_labels(raw_legend=legend_text)

    box_size = max(12, int(FONT_SIZE * 0.9))
    gap = 8

    # First legend item: lived
    lx = PADDING
    draw.rectangle(
        [lx, legend_y, lx + box_size, legend_y + box_size],
        fill=COLORS["lived"],
        outline=COLORS["grid"],
    )
    text_x = lx + box_size + gap
    draw.text((text_x, legend_y), lived_label, fill=COLORS["text"], font=small_font)

    # Measure width of first item to place the second item
    bbox = draw.textbbox((0, 0), lived_label, font=small_font)
    first_width = (box_size + gap) + (bbox[2] - bbox[0]) + 24

    # Second legend item: future
    sx = PADDING + first_width
    draw.rectangle(
        [sx, legend_y, sx + box_size, legend_y + box_size],
        fill=COLORS["background"],
        outline=COLORS["grid"],
    )
    draw.text(
        (sx + box_size + gap, legend_y),
        future_label,
        fill=COLORS["text"],
        font=small_font,
    )

    # Convert to BytesIO
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    return img_byte_arr


def _select_font_path() -> str | None:
    """Select a font path that supports Cyrillic on most Linux systems.

    Tries a list of common fonts (DejaVu Sans, Liberation Sans, Noto Sans).

    :returns: Absolute path to a TTF font if found, otherwise ``None``
    :rtype: Optional[str]
    """
    candidate_paths: list[str] = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/local/share/fonts/DejaVuSans.ttf",
    ]
    for path in candidate_paths:
        try:
            with open(path, "rb"):
                return path
        except Exception:
            continue
    return None


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font with good Unicode coverage.

    Falls back to default font if no known TTF is available.

    :param size: Font size in pixels
    :type size: int
    :returns: Pillow font object
    :rtype: ImageFont.FreeTypeFont | ImageFont.ImageFont
    """
    font_path = _select_font_path()
    if font_path is not None:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _parse_legend_labels(raw_legend: str) -> Tuple[str, str]:
    """Parse localized legend string into two labels without emoji.

    The expected format is similar to: "🟩 Lived weeks | ⬜ Future weeks".
    This function strips any leading non-word symbols (e.g., emoji) from each part.

    :param raw_legend: Localized legend text possibly containing emoji markers
    :type raw_legend: str
    :returns: Tuple of (lived_label, future_label)
    :rtype: Tuple[str, str]
    """
    import re

    parts = [p.strip() for p in raw_legend.split("|")]
    if len(parts) == 1:
        parts.append("")

    def strip_symbols(s: str) -> str:
        return re.sub(r"^\W+\s*", "", s)

    lived_label = strip_symbols(parts[0]) or "Lived weeks"
    future_label = strip_symbols(parts[1]) or "Future weeks"
    return lived_label, future_label
