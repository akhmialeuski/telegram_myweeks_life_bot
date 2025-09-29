"""Tests for grid visualization functionality."""

from io import BytesIO
from unittest.mock import Mock, mock_open, patch

import pytest

from src.database.models.user import User
from src.database.models.user_settings import UserSettings
from src.database.models.user_subscription import UserSubscription
from src.visualization.grid import (
    _load_font,
    _parse_legend_labels,
    _select_font_path,
    calculate_grid_dimensions,
    generate_visualization,
)


class TestCalculateGridDimensions:
    """Test class for calculate_grid_dimensions function.

    This class contains all tests for the grid dimensions calculation,
    including various configuration scenarios.
    """

    @patch("src.visualization.grid.WEEKS_PER_YEAR", 52)
    @patch("src.visualization.grid.CELL_SIZE", 10)
    @patch("src.visualization.grid.MAX_YEARS", 80)
    @patch("src.visualization.grid.PADDING", 20)
    def test_calculate_grid_dimensions_default(self):
        """Test calculate_grid_dimensions with default configuration.

        This test verifies that grid dimensions are calculated correctly
        using default configuration values.
        """
        width, height = calculate_grid_dimensions()

        # Verify width calculation: (52 weeks * 10 pixels) + (2 * 20 padding) = 560
        assert width == 560

        # Verify height calculation: (80 years * 10 pixels) + (2 * 20 padding) = 840
        assert height == 840

    @patch("src.visualization.grid.WEEKS_PER_YEAR", 52)
    @patch("src.visualization.grid.CELL_SIZE", 15)
    @patch("src.visualization.grid.MAX_YEARS", 100)
    @patch("src.visualization.grid.PADDING", 30)
    def test_calculate_grid_dimensions_custom(self):
        """Test calculate_grid_dimensions with custom configuration.

        This test verifies that grid dimensions are calculated correctly
        with custom configuration values.
        """
        width, height = calculate_grid_dimensions()

        # Verify width calculation: (52 weeks * 15 pixels) + (2 * 30 padding) = 840
        assert width == 840

        # Verify height calculation: (100 years * 15 pixels) + (2 * 30 padding) = 1560
        assert height == 1560

    @patch("src.visualization.grid.WEEKS_PER_YEAR", 1)
    @patch("src.visualization.grid.CELL_SIZE", 1)
    @patch("src.visualization.grid.MAX_YEARS", 1)
    @patch("src.visualization.grid.PADDING", 0)
    def test_calculate_grid_dimensions_minimal(self):
        """Test calculate_grid_dimensions with minimal configuration.

        This test verifies that grid dimensions work correctly
        with minimal configuration values.
        """
        width, height = calculate_grid_dimensions()

        # Verify minimal dimensions
        assert width == 1  # (1 week * 1 pixel) + (2 * 0 padding) = 1
        assert height == 1  # (1 year * 1 pixel) + (2 * 0 padding) = 1


class TestGenerateVisualization:
    """Test class for generate_visualization function.

    This class contains all tests for the visualization generation,
    including various input types and error scenarios.
    """

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create mock user profile
        self.mock_user_settings = Mock(spec=UserSettings)
        self.mock_user_settings.language = "en"

        self.mock_user_subscription = Mock(spec=UserSubscription)

        self.mock_user_profile = Mock(spec=User)
        self.mock_user_profile.telegram_id = 12345
        self.mock_user_profile.settings = self.mock_user_settings
        self.mock_user_profile.subscription = self.mock_user_subscription

    @patch("src.visualization.grid.user_service")
    @patch("src.visualization.grid.LifeCalculatorEngine")
    @patch("src.visualization.grid.Image")
    @patch("src.visualization.grid.ImageDraw")
    @patch("src.visualization.grid._load_font")
    @patch("src.i18n.use_locale")
    @patch("src.visualization.grid._parse_legend_labels")
    def test_generate_visualization_with_db_user(
        self,
        mock_parse_legend,
        mock_use_locale,
        mock_load_font,
        mock_image_draw,
        mock_image,
        mock_calculator,
        mock_user_service,
    ):
        """Test generate_visualization with database User object.

        This test verifies that visualization is generated correctly
        when provided with a database User object.
        """
        # Setup mocks
        mock_user_service.get_user_profile.return_value = self.mock_user_profile

        mock_engine = Mock()
        mock_engine.calculate_weeks_lived.return_value = 1000
        mock_calculator.return_value = mock_engine

        mock_image_instance = Mock()
        mock_image.new.return_value = mock_image_instance

        mock_draw = Mock()
        mock_draw.textbbox.return_value = (
            0,
            0,
            100,
            20,
        )  # Mock bbox for text measurement
        mock_image_draw.Draw.return_value = mock_draw

        mock_font = Mock()
        mock_load_font.return_value = mock_font

        mock_pgettext = Mock()
        mock_pgettext.return_value = "🟩 Lived weeks | ⬜ Future weeks"
        mock_use_locale.return_value = (Mock(), Mock(), mock_pgettext)

        mock_parse_legend.return_value = ("Lived weeks", "Future weeks")

        # Test with database User object
        result = generate_visualization(self.mock_user_profile)

        # Verify result is BytesIO
        assert isinstance(result, BytesIO)

        # Verify user service was called with correct telegram_id
        mock_user_service.get_user_profile.assert_called_once_with(telegram_id=12345)

        # Verify calculator was created and called
        mock_calculator.assert_called_once_with(user=self.mock_user_profile)
        mock_engine.calculate_weeks_lived.assert_called_once()

        # Verify image creation
        mock_image.new.assert_called_once()
        mock_image_draw.Draw.assert_called_once_with(mock_image_instance)

    @patch("src.visualization.grid.user_service")
    @patch("src.visualization.grid.LifeCalculatorEngine")
    @patch("src.visualization.grid.Image")
    @patch("src.visualization.grid.ImageDraw")
    @patch("src.visualization.grid._load_font")
    @patch("src.i18n.use_locale")
    @patch("src.visualization.grid._parse_legend_labels")
    def test_generate_visualization_with_telegram_user(
        self,
        mock_parse_legend,
        mock_use_locale,
        mock_load_font,
        mock_image_draw,
        mock_image,
        mock_calculator,
        mock_user_service,
    ):
        """Test generate_visualization with Telegram User object.

        This test verifies that visualization is generated correctly
        when provided with a Telegram User object.
        """
        # Setup mocks
        mock_user_service.get_user_profile.return_value = self.mock_user_profile

        mock_engine = Mock()
        mock_engine.calculate_weeks_lived.return_value = 500
        mock_calculator.return_value = mock_engine

        mock_image_instance = Mock()
        mock_image.new.return_value = mock_image_instance

        mock_draw = Mock()
        mock_draw.textbbox.return_value = (
            0,
            0,
            100,
            20,
        )  # Mock bbox for text measurement
        mock_image_draw.Draw.return_value = mock_draw

        mock_font = Mock()
        mock_load_font.return_value = mock_font

        mock_pgettext = Mock()
        mock_pgettext.return_value = "🟩 Lived weeks | ⬜ Future weeks"
        mock_use_locale.return_value = (Mock(), Mock(), mock_pgettext)

        mock_parse_legend.return_value = ("Lived weeks", "Future weeks")

        # Create mock Telegram User object
        mock_telegram_user = Mock()
        mock_telegram_user.id = 67890
        # Ensure getattr works properly for telegram_id
        mock_telegram_user.telegram_id = 67890

        # Test with Telegram User object
        result = generate_visualization(mock_telegram_user)

        # Verify result is BytesIO
        assert isinstance(result, BytesIO)

        # Verify user service was called with correct telegram_id
        mock_user_service.get_user_profile.assert_called_once_with(telegram_id=67890)

    @patch("src.visualization.grid.user_service")
    @patch("src.visualization.grid.LifeCalculatorEngine")
    @patch("src.visualization.grid.Image")
    @patch("src.visualization.grid.ImageDraw")
    @patch("src.visualization.grid._load_font")
    @patch("src.i18n.use_locale")
    @patch("src.visualization.grid._parse_legend_labels")
    def test_generate_visualization_with_int_user_id(
        self,
        mock_parse_legend,
        mock_use_locale,
        mock_load_font,
        mock_image_draw,
        mock_image,
        mock_calculator,
        mock_user_service,
    ):
        """Test generate_visualization with integer user ID.

        This test verifies that visualization is generated correctly
        when provided with an integer user ID.
        """
        # Setup mocks
        mock_user_service.get_user_profile.return_value = self.mock_user_profile

        mock_engine = Mock()
        mock_engine.calculate_weeks_lived.return_value = 2000
        mock_calculator.return_value = mock_engine

        mock_image_instance = Mock()
        mock_image.new.return_value = mock_image_instance

        mock_draw = Mock()
        mock_draw.textbbox.return_value = (
            0,
            0,
            100,
            20,
        )  # Mock bbox for text measurement
        mock_image_draw.Draw.return_value = mock_draw

        mock_font = Mock()
        mock_load_font.return_value = mock_font

        mock_pgettext = Mock()
        mock_pgettext.return_value = "🟩 Lived weeks | ⬜ Future weeks"
        mock_use_locale.return_value = (Mock(), Mock(), mock_pgettext)

        mock_parse_legend.return_value = ("Lived weeks", "Future weeks")

        # Test with integer user ID
        result = generate_visualization(11111)

        # Verify result is BytesIO
        assert isinstance(result, BytesIO)

        # Verify user service was called with correct telegram_id
        mock_user_service.get_user_profile.assert_called_once_with(telegram_id=11111)

    def test_generate_visualization_with_unsupported_type(self):
        """Test generate_visualization with unsupported input type.

        This test verifies that TypeError is raised when provided
        with an unsupported input type.
        """
        # Test with unsupported type
        with pytest.raises(TypeError) as exc_info:
            generate_visualization("invalid_input")

        # Verify error message
        assert (
            "generate_visualization expects DB User (telegram_id), Telegram User (id), or int user id"
            in str(exc_info.value)
        )

    def test_generate_visualization_with_unsupported_object(self):
        """Test generate_visualization with object without required attributes.

        This test verifies that TypeError is raised when provided
        with an object that doesn't have required attributes.
        """
        # Create mock object without required attributes
        mock_object = Mock()
        del mock_object.telegram_id
        del mock_object.id

        # Test with unsupported object
        with pytest.raises(TypeError) as exc_info:
            generate_visualization(mock_object)

        # Verify error message
        assert (
            "generate_visualization expects DB User (telegram_id), Telegram User (id), or int user id"
            in str(exc_info.value)
        )

    @patch("src.visualization.grid.user_service")
    def test_generate_visualization_user_not_found(self, mock_user_service):
        """Test generate_visualization when user profile is not found.

        This test verifies that ValueError is raised when user profile
        cannot be found in the database.
        """
        # Setup mock to return None (user not found)
        mock_user_service.get_user_profile.return_value = None

        # Test with user not found
        with pytest.raises(ValueError) as exc_info:
            generate_visualization(99999)

        # Verify error message
        assert "User profile not found for telegram_id: 99999" in str(exc_info.value)

    @patch("src.visualization.grid.user_service")
    @patch("src.visualization.grid.LifeCalculatorEngine")
    @patch("src.visualization.grid.Image")
    @patch("src.visualization.grid.ImageDraw")
    @patch("src.visualization.grid._load_font")
    @patch("src.i18n.use_locale")
    @patch("src.visualization.grid._parse_legend_labels")
    def test_generate_visualization_with_no_language_setting(
        self,
        mock_parse_legend,
        mock_use_locale,
        mock_load_font,
        mock_image_draw,
        mock_image,
        mock_calculator,
        mock_user_service,
    ):
        """Test generate_visualization when user has no language setting.

        This test verifies that visualization works correctly when user
        has no language setting (uses default language).
        """
        # Setup user profile without language setting
        mock_user_settings_no_lang = Mock(spec=UserSettings)
        mock_user_settings_no_lang.language = None

        mock_user_profile_no_lang = Mock(spec=User)
        mock_user_profile_no_lang.telegram_id = 12345
        mock_user_profile_no_lang.settings = mock_user_settings_no_lang

        # Setup mocks
        mock_user_service.get_user_profile.return_value = mock_user_profile_no_lang

        mock_engine = Mock()
        mock_engine.calculate_weeks_lived.return_value = 100
        mock_calculator.return_value = mock_engine

        mock_image_instance = Mock()
        mock_image.new.return_value = mock_image_instance

        mock_draw = Mock()
        mock_draw.textbbox.return_value = (
            0,
            0,
            100,
            20,
        )  # Mock bbox for text measurement
        mock_image_draw.Draw.return_value = mock_draw

        mock_font = Mock()
        mock_load_font.return_value = mock_font

        mock_pgettext = Mock()
        mock_pgettext.return_value = "🟩 Lived weeks | ⬜ Future weeks"
        mock_use_locale.return_value = (Mock(), Mock(), mock_pgettext)

        mock_parse_legend.return_value = ("Lived weeks", "Future weeks")

        # Test with user without language setting
        result = generate_visualization(mock_user_profile_no_lang)

        # Verify result is BytesIO
        assert isinstance(result, BytesIO)

        # Verify default language was used
        mock_use_locale.assert_called_once_with("ru")  # DEFAULT_LANGUAGE


class TestSelectFontPath:
    """Test class for _select_font_path function.

    This class contains all tests for the font path selection,
    including various file system scenarios.
    """

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_select_font_path_no_fonts_found(self, mock_open):
        """Test _select_font_path when no fonts are found.

        This test verifies that None is returned when no font files
        are found in the expected locations.
        """
        result = _select_font_path()
        assert result is None

    @patch("builtins.open", mock_open(read_data=b"font_data"))
    def test_select_font_path_first_font_found(self):
        """Test _select_font_path when first font is found.

        This test verifies that the first available font path is returned
        when found in the candidate paths.
        """
        result = _select_font_path()
        assert result == "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    @patch(
        "builtins.open",
        side_effect=[FileNotFoundError, mock_open(read_data=b"font_data").return_value],
    )
    def test_select_font_path_second_font_found(self, mock_open):
        """Test _select_font_path when second font is found.

        This test verifies that the second available font path is returned
        when the first one is not found.
        """
        result = _select_font_path()
        assert (
            result == "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        )

    @patch(
        "builtins.open",
        side_effect=[
            FileNotFoundError,
            FileNotFoundError,
            FileNotFoundError,
            mock_open(read_data=b"font_data").return_value,
        ],
    )
    def test_select_font_path_last_font_found(self, mock_open):
        """Test _select_font_path when last font is found.

        This test verifies that the last available font path is returned
        when only the last one is found.
        """
        result = _select_font_path()
        assert result == "/usr/local/share/fonts/DejaVuSans.ttf"

    @patch("builtins.open", side_effect=PermissionError)
    def test_select_font_path_permission_error(self, mock_open):
        """Test _select_font_path with permission error.

        This test verifies that None is returned when permission error
        occurs while trying to access font files.
        """
        result = _select_font_path()
        assert result is None


class TestLoadFont:
    """Test class for _load_font function.

    This class contains all tests for the font loading functionality,
    including various font loading scenarios.
    """

    @patch("src.visualization.grid._select_font_path")
    @patch("src.visualization.grid.ImageFont.truetype")
    def test_load_font_with_custom_font(self, mock_truetype, mock_select_path):
        """Test _load_font with custom font path.

        This test verifies that custom font is loaded when available.
        """
        # Setup mock
        mock_select_path.return_value = "/custom/font.ttf"
        mock_font = Mock()
        mock_truetype.return_value = mock_font

        # Test font loading
        result = _load_font(12)

        # Verify custom font was loaded
        mock_truetype.assert_called_once_with("/custom/font.ttf", 12)
        assert result == mock_font

    @patch("src.visualization.grid._select_font_path")
    @patch("src.visualization.grid.ImageFont.truetype")
    def test_load_font_with_custom_font_error_fallback_to_arial(
        self, mock_truetype, mock_select_path
    ):
        """Test _load_font fallback to Arial when custom font fails.

        This test verifies that Arial font is loaded as fallback when
        custom font loading fails.
        """
        # Setup mock
        mock_select_path.return_value = "/custom/font.ttf"
        mock_font = Mock()

        # First call fails, second call succeeds
        mock_truetype.side_effect = [OSError("Font error"), mock_font]

        # Test font loading
        result = _load_font(14)

        # Verify both calls were made
        assert mock_truetype.call_count == 2
        mock_truetype.assert_any_call("/custom/font.ttf", 14)
        mock_truetype.assert_any_call("arial.ttf", 14)
        assert result == mock_font

    @patch("src.visualization.grid._select_font_path")
    @patch("src.visualization.grid.ImageFont.truetype")
    @patch("src.visualization.grid.ImageFont.load_default")
    def test_load_font_all_fonts_fail_fallback_to_default(
        self, mock_load_default, mock_truetype, mock_select_path
    ):
        """Test _load_font fallback to default font when all fonts fail.

        This test verifies that default font is loaded when all other
        font loading attempts fail.
        """
        # Setup mock
        mock_select_path.return_value = "/custom/font.ttf"
        mock_font = Mock()
        mock_load_default.return_value = mock_font

        # All font loading attempts fail
        mock_truetype.side_effect = OSError("Font error")

        # Test font loading
        result = _load_font(16)

        # Verify fallback to default font
        mock_load_default.assert_called_once()
        assert result == mock_font

    @patch("src.visualization.grid._select_font_path")
    @patch("src.visualization.grid.ImageFont.truetype")
    @patch("src.visualization.grid.ImageFont.load_default")
    def test_load_font_no_custom_font_fallback_to_arial(
        self, mock_load_default, mock_truetype, mock_select_path
    ):
        """Test _load_font fallback to Arial when no custom font is found.

        This test verifies that Arial font is loaded when no custom
        font path is available.
        """
        # Setup mock
        mock_select_path.return_value = None
        mock_font = Mock()
        mock_truetype.return_value = mock_font

        # Test font loading
        result = _load_font(18)

        # Verify Arial font was loaded
        mock_truetype.assert_called_once_with("arial.ttf", 18)
        assert result == mock_font


class TestParseLegendLabels:
    """Test class for _parse_legend_labels function.

    This class contains all tests for the legend parsing functionality,
    including various legend formats and edge cases.
    """

    def test_parse_legend_labels_with_pipe_separator(self):
        """Test _parse_legend_labels with pipe separator.

        This test verifies that legend labels are parsed correctly
        when separated by pipe character.
        """
        legend_text = "🟩 Lived weeks | ⬜ Future weeks"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_with_emoji(self):
        """Test _parse_legend_labels with emoji markers.

        This test verifies that emoji markers are stripped correctly
        from legend labels.
        """
        legend_text = "🟢 Lived weeks | 🔲 Future weeks"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_with_symbols(self):
        """Test _parse_legend_labels with various symbols.

        This test verifies that various symbols are stripped correctly
        from legend labels.
        """
        legend_text = "■ Lived weeks | □ Future weeks"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_without_pipe_separator(self):
        """Test _parse_legend_labels without pipe separator.

        This test verifies that legend labels are parsed correctly
        when no pipe separator is present.
        """
        legend_text = "🟩 Lived weeks"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_empty_parts(self):
        """Test _parse_legend_labels with empty parts.

        This test verifies that empty parts are handled correctly
        with default labels.
        """
        legend_text = "🟩 | ⬜"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_whitespace_handling(self):
        """Test _parse_legend_labels with whitespace handling.

        This test verifies that whitespace is handled correctly
        in legend parsing.
        """
        legend_text = "  🟩   Lived weeks   |   ⬜   Future weeks   "
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_complex_symbols(self):
        """Test _parse_legend_labels with complex symbols.

        This test verifies that complex symbols are stripped correctly
        from legend labels.
        """
        legend_text = "🔴🟩⭐ Lived weeks | 🔵⬜✨ Future weeks"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_multiple_pipes(self):
        """Test _parse_legend_labels with multiple pipe separators.

        This test verifies that only the first pipe separator is used
        for splitting legend labels.
        """
        legend_text = "🟩 Lived weeks | ⬜ Future weeks | Extra part"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_empty_string(self):
        """Test _parse_legend_labels with empty string.

        This test verifies that empty string is handled correctly
        with default labels.
        """
        legend_text = ""
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"

    def test_parse_legend_labels_only_symbols(self):
        """Test _parse_legend_labels with only symbols.

        This test verifies that labels with only symbols are handled
        correctly with default labels.
        """
        legend_text = "🟩🟢■ | ⬜🔲□"
        lived_label, future_label = _parse_legend_labels(legend_text)

        assert lived_label == "Lived weeks"
        assert future_label == "Future weeks"
