from honeybadger.main import run


def test_run_prints_available():
    # Basic smoke test to confirm entrypoint exists
    assert callable(run)
