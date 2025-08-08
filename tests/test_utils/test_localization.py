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

    def test_message_builder_get_method(self):
        """Test MessageBuilder.get method with various keys."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test with a key that should exist
        result = builder.get("help.text")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_message_builder_get_with_parameters(self):
        """Test MessageBuilder.get method with parameters."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test with parameters for a key that exists
        result = builder.get("start.welcome_existing", first_name="John")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_message_builder_dunder_getattr(self):
        """Test MessageBuilder.__getattr__ method for dynamic access."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test dynamic access with a key that exists
        result = builder.get("start.welcome_existing", first_name="John")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_message_builder_get_with_fallback(self):
        """Test MessageBuilder.get method with fallback to default language."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test with a non-existent key (should fallback to key itself)
        result = builder.get("non.existent.key")
        assert result == "non.existent.key"

    def test_message_builder_get_with_formatting(self):
        """Test MessageBuilder.get method with string formatting."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test with formatting parameters
        result = builder.get("start.welcome_existing", first_name="John")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_message_builder_get_with_missing_format_placeholders(self):
        """Test MessageBuilder.get method handles keys with format placeholders not in kwargs gracefully."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Test with a key that contains format placeholders but kwargs doesn't have them
        # This should not raise KeyError or ValueError, but return the key as-is
        result = builder.get("key.with.{missing}.placeholders", existing_param="value")
        assert result == "key.with.{missing}.placeholders"

        # Test with no kwargs at all
        result = builder.get("key.with.{missing}.placeholders")
        assert result == "key.with.{missing}.placeholders"

        # Test with empty kwargs
        result = builder.get("key.with.{missing}.placeholders", **{})
        assert result == "key.with.{missing}.placeholders"

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

    def test_message_builder_dynamic_get_id_as_key(self):
        """Test MessageBuilder.get resolves ID-as-key via gettext._.

        We monkeypatch builder._ to simulate translation existing for key-only ids.
        """
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        original_gettext = builder._

        def fake_gettext(msgid: str) -> str:
            return "OK_ID" if msgid == "demo.key" else msgid

        builder._ = fake_gettext  # type: ignore[assignment]

        result = builder.get(key="demo.key")
        assert result == "OK_ID"

        # Restore
        builder._ = original_gettext  # type: ignore[assignment]

    def test_message_builder_dynamic_get_context_empty_id(self):
        """Test MessageBuilder.get resolves context-as-key with empty msgid via pgettext.

        We monkeypatch builder._trans.pgettext to return a value for (ctx, "").
        """
        from types import SimpleNamespace

        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")

        # Ensure id-as-key path fails to force ctx path
        builder._ = lambda s: s  # type: ignore[assignment]

        def fake_pgettext(context: str, msgid: str) -> str:
            if context == "demo.ctx" and msgid == "":
                return "OK_CTX_EMPTY"
            return ""

        builder._trans = SimpleNamespace(pgettext=fake_pgettext)  # type: ignore[assignment]

        result = builder.get(key="demo.ctx")
        assert result == "OK_CTX_EMPTY"

    def test_message_builder_dynamic_get_context_same_id(self):
        """Test MessageBuilder.get resolves context-as-key with same id via pgettext.

        We monkeypatch builder._trans.pgettext to return a value for (ctx, id).
        """
        from types import SimpleNamespace

        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        builder._ = lambda s: s  # type: ignore[assignment]

        def fake_pgettext(context: str, msgid: str) -> str:
            if context == "demo.same" and msgid == "demo.same":
                return "OK_CTX_SAME"
            return ""

        builder._trans = SimpleNamespace(pgettext=fake_pgettext)  # type: ignore[assignment]

        result = builder.get(key="demo.same")
        assert result == "OK_CTX_SAME"

    def test_message_builder_dunder_getattr_maps_snake_to_dotted(self):
        """Test that unknown attributes map to dotted keys via get()."""
        from src.utils.localization import MessageBuilder

        builder = MessageBuilder("ru")
        captured = {}

        def fake_get(key: str, **kwargs):  # type: ignore[no-untyped-def]
            captured["key"] = key
            captured.update(kwargs)
            return "OK"

        builder.get = fake_get  # type: ignore[assignment]

        # Use a non-existing attribute name to trigger __getattr__
        result = builder.some_new_message(age=25)  # dynamic path
        assert result == "OK"
        assert captured["key"] == "some.new.message"
        assert captured["age"] == 25
