from honeybadger import config


def test_config_values_exist():
    assert config.OLLAMA_URL
    assert config.MAX_VRAM_GB == 3.5
