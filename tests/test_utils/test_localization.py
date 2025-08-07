"""Tests for localization functionality."""


class TestLocalization:
    """Test localization functions."""

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        # Import here to avoid circular imports
        from src.utils.localization import get_supported_languages

        languages = get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "ru" in languages
        assert "en" in languages

    def test_is_language_supported_valid(self):
        """Test checking if valid language is supported."""
        from src.utils.localization import is_language_supported

        assert is_language_supported("ru") is True
        assert is_language_supported("en") is True

    def test_is_language_supported_invalid(self):
        """Test checking if invalid language is supported."""
        from src.utils.localization import is_language_supported

        assert is_language_supported("fr") is False
        assert is_language_supported("de") is False

    def test_is_language_supported_edge_cases(self):
        """Test language support with edge cases."""
        from src.utils.localization import is_language_supported

        assert is_language_supported("") is False
        assert is_language_supported(None) is False

    def test_get_localized_language_name_valid_combinations(self):
        """Test getting localized language names for valid combinations."""
        from src.utils.localization import get_localized_language_name

        # Test Russian language names
        assert get_localized_language_name("ru", "ru") == "Русский"
        assert get_localized_language_name("en", "ru") == "Английский"
        assert get_localized_language_name("ua", "ru") == "Украинский"
        assert get_localized_language_name("by", "ru") == "Белорусский"

        # Test English language names
        assert get_localized_language_name("ru", "en") == "Russian"
        assert get_localized_language_name("en", "en") == "English"
        assert get_localized_language_name("ua", "en") == "Ukrainian"
        assert get_localized_language_name("by", "en") == "Belarusian"

        # Test Ukrainian language names
        assert get_localized_language_name("ru", "ua") == "Російська"
        assert get_localized_language_name("en", "ua") == "Англійська"
        assert get_localized_language_name("ua", "ua") == "Українська"
        assert get_localized_language_name("by", "ua") == "Білоруська"

        # Test Belarusian language names
        assert get_localized_language_name("ru", "by") == "Рускай"
        assert get_localized_language_name("en", "by") == "Англійская"
        assert get_localized_language_name("ua", "by") == "Украінская"
        assert get_localized_language_name("by", "by") == "Беларуская"

    def test_get_localized_language_name_unsupported_target_language(self):
        """Test getting localized language name with unsupported target language."""
        from src.utils.localization import get_localized_language_name

        # Should return the language code if target language is not supported
        assert get_localized_language_name("ru", "fr") == "ru"
        assert get_localized_language_name("en", "de") == "en"

    def test_get_localized_language_name_unsupported_language(self):
        """Test getting localized language name with unsupported language."""
        from src.utils.localization import get_localized_language_name

        # Should return the language code if language is not supported
        assert get_localized_language_name("fr", "ru") == "fr"
        assert get_localized_language_name("de", "en") == "de"

    def test_get_localized_language_name_edge_cases(self):
        """Test getting localized language name with edge cases."""
        from src.utils.localization import get_localized_language_name

        # Test with empty strings
        assert get_localized_language_name("", "ru") == ""
        assert get_localized_language_name("ru", "") == "ru"

        # Test with None values
        assert get_localized_language_name(None, "ru") is None
        assert get_localized_language_name("ru", None) == "ru"

    def test_message_builder_initialization(self):
        """Test MessageBuilder initialization."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        assert builder.lang == "ru"
        assert hasattr(builder, "_")

    def test_message_builder_help_message(self):
        """Test MessageBuilder help message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        help_message = builder.help()
        assert isinstance(help_message, str)
        assert len(help_message) > 0
        assert "LifeWeeksBot" in help_message or "бот" in help_message

    def test_message_builder_error_message(self):
        """Test MessageBuilder error message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        error_message = builder.error()
        assert isinstance(error_message, str)
        assert len(error_message) > 0

    def test_message_builder_unknown_command_message(self):
        """Test MessageBuilder unknown command message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        unknown_message = builder.unknown_command()
        assert isinstance(unknown_message, str)
        assert len(unknown_message) > 0

    def test_message_builder_not_registered_message(self):
        """Test MessageBuilder not registered message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        not_registered_message = builder.not_registered()
        assert isinstance(not_registered_message, str)
        assert len(not_registered_message) > 0

    def test_message_builder_not_set_message(self):
        """Test MessageBuilder not set message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        not_set_message = builder.not_set()
        assert isinstance(not_set_message, str)
        assert len(not_set_message) > 0

    def test_message_builder_registration_error_message(self):
        """Test MessageBuilder registration error message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        registration_error_message = builder.registration_error()
        assert isinstance(registration_error_message, str)
        assert len(registration_error_message) > 0

    def test_message_builder_birth_date_errors(self):
        """Test MessageBuilder birth date error messages."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        future_error = builder.birth_date_future_error()
        assert isinstance(future_error, str)
        assert len(future_error) > 0

        old_error = builder.birth_date_old_error()
        assert isinstance(old_error, str)
        assert len(old_error) > 0

        format_error = builder.birth_date_format_error()
        assert isinstance(format_error, str)
        assert len(format_error) > 0

    def test_message_builder_not_registered_weeks_message(self):
        """Test MessageBuilder not registered weeks message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        not_registered_weeks_message = builder.not_registered_weeks()
        assert isinstance(not_registered_weeks_message, str)
        assert len(not_registered_weeks_message) > 0

    def test_message_builder_not_registered_visualize_message(self):
        """Test MessageBuilder not registered visualize message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        not_registered_visualize_message = builder.not_registered_visualize()
        assert isinstance(not_registered_visualize_message, str)
        assert len(not_registered_visualize_message) > 0

    def test_message_builder_visualization_error_message(self):
        """Test MessageBuilder visualization error message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        visualization_error_message = builder.visualization_error()
        assert isinstance(visualization_error_message, str)
        assert len(visualization_error_message) > 0

    def test_message_builder_weeks_error_message(self):
        """Test MessageBuilder weeks error message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        weeks_error_message = builder.weeks_error()
        assert isinstance(weeks_error_message, str)
        assert len(weeks_error_message) > 0

    def test_message_builder_subscription_messages(self):
        """Test MessageBuilder subscription message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test subscription current message
        subscription_current = builder.subscription_current(
            "basic", "Basic subscription"
        )
        assert isinstance(subscription_current, str)
        assert len(subscription_current) > 0

        # Test subscription invalid type message
        subscription_invalid = builder.subscription_invalid_type()
        assert isinstance(subscription_invalid, str)
        assert len(subscription_invalid) > 0

        # Test subscription profile error message
        subscription_profile_error = builder.subscription_profile_error()
        assert isinstance(subscription_profile_error, str)
        assert len(subscription_profile_error) > 0

        # Test subscription already active message
        subscription_already_active = builder.subscription_already_active("basic")
        assert isinstance(subscription_already_active, str)
        assert len(subscription_already_active) > 0

    def test_message_builder_subscription_change_messages(self):
        """Test MessageBuilder subscription change message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test subscription change success message
        subscription_change_success = builder.subscription_change_success(
            "basic", "Basic subscription"
        )
        assert isinstance(subscription_change_success, str)
        assert len(subscription_change_success) > 0

        # Test subscription change failed message
        subscription_change_failed = builder.subscription_change_failed()
        assert isinstance(subscription_change_failed, str)
        assert len(subscription_change_failed) > 0

        # Test subscription change error message
        subscription_change_error = builder.subscription_change_error()
        assert isinstance(subscription_change_error, str)
        assert len(subscription_change_error) > 0

    def test_message_builder_settings_messages(self):
        """Test MessageBuilder settings message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test change birth date message
        change_birth_date = builder.change_birth_date("01.01.1990")
        assert isinstance(change_birth_date, str)
        assert len(change_birth_date) > 0

        # Test change language message
        change_language = builder.change_language("ru")
        assert isinstance(change_language, str)
        assert len(change_language) > 0

        # Test change life expectancy message
        change_life_expectancy = builder.change_life_expectancy(80)
        assert isinstance(change_life_expectancy, str)
        assert len(change_life_expectancy) > 0

    def test_message_builder_update_messages(self):
        """Test MessageBuilder update message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test birth date updated message
        birth_date_updated = builder.birth_date_updated("01.01.1990", 30)
        assert isinstance(birth_date_updated, str)
        assert len(birth_date_updated) > 0

        # Test language updated message
        language_updated = builder.language_updated("en")
        assert isinstance(language_updated, str)
        assert len(language_updated) > 0

        # Test life expectancy updated message
        life_expectancy_updated = builder.life_expectancy_updated(80)
        assert isinstance(life_expectancy_updated, str)
        assert len(life_expectancy_updated) > 0

    def test_message_builder_invalid_life_expectancy_message(self):
        """Test MessageBuilder invalid life expectancy message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        invalid_life_expectancy_message = builder.invalid_life_expectancy()
        assert isinstance(invalid_life_expectancy_message, str)
        assert len(invalid_life_expectancy_message) > 0

    def test_message_builder_settings_error_message(self):
        """Test MessageBuilder settings error message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        settings_error_message = builder.settings_error()
        assert isinstance(settings_error_message, str)
        assert len(settings_error_message) > 0

    def test_message_builder_cancel_messages(self):
        """Test MessageBuilder cancel message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test cancel success message
        cancel_success = builder.cancel_success("John")
        assert isinstance(cancel_success, str)
        assert len(cancel_success) > 0

        # Test cancel error message
        cancel_error = builder.cancel_error("John")
        assert isinstance(cancel_error, str)
        assert len(cancel_error) > 0

    def test_message_builder_button_messages(self):
        """Test MessageBuilder button message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test button change birth date message
        button_change_birth_date = builder.button_change_birth_date()
        assert isinstance(button_change_birth_date, str)
        assert len(button_change_birth_date) > 0

        # Test button change language message
        button_change_language = builder.button_change_language()
        assert isinstance(button_change_language, str)
        assert len(button_change_language) > 0

        # Test button change life expectancy message
        button_change_life_expectancy = builder.button_change_life_expectancy()
        assert isinstance(button_change_life_expectancy, str)
        assert len(button_change_life_expectancy) > 0

    def test_message_builder_weeks_statistics(self):
        """Test MessageBuilder weeks statistics message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        weeks_statistics = builder.weeks_statistics(
            age=25,
            weeks_lived=1300,
            remaining_weeks=2860,
            life_percentage="16.2%",
            days_until_birthday=45,
        )
        assert isinstance(weeks_statistics, str)
        assert len(weeks_statistics) > 0
        assert "25" in weeks_statistics

    def test_message_builder_visualize_info(self):
        """Test MessageBuilder visualize info message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        visualize_info = builder.visualize_info(
            age=25, weeks_lived=1300, life_percentage="16.2%"
        )
        assert isinstance(visualize_info, str)
        assert len(visualize_info) > 0
        assert "25" in visualize_info

    def test_message_builder_start_welcome_messages(self):
        """Test MessageBuilder start welcome message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test start welcome existing message
        start_welcome_existing = builder.start_welcome_existing("John")
        assert isinstance(start_welcome_existing, str)
        assert len(start_welcome_existing) > 0

        # Test start welcome new message
        start_welcome_new = builder.start_welcome_new("John")
        assert isinstance(start_welcome_new, str)
        assert len(start_welcome_new) > 0

    def test_message_builder_registration_success(self):
        """Test MessageBuilder registration success message generation."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        registration_success = builder.registration_success(
            first_name="John",
            birth_date="01.01.1990",
            age=30,
            weeks_lived=1560,
            remaining_weeks=2600,
            life_percentage="37.5%",
        )
        assert isinstance(registration_success, str)
        assert len(registration_success) > 0
        assert "01.01.1990" in registration_success
        assert "30" in registration_success

    def test_localization_module_imports(self):
        """Test that all required functions can be imported."""
        from src.utils.localization import (
            DEFAULT_LANGUAGE,
            LANGUAGES,
            get_localized_language_name,
            get_supported_languages,
            is_language_supported,
        )

        assert callable(get_localized_language_name)
        assert callable(get_supported_languages)
        assert callable(is_language_supported)
        assert isinstance(LANGUAGES, list)
        assert isinstance(DEFAULT_LANGUAGE, str)
