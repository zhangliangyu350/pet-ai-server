from app.core.config import get_settings


def test_default_settings_have_app_name():
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.app_name == "Pet AI Server"
    assert settings.app_env == "development"

