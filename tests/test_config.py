from src import config


def test_all_dicts_25():
    for name in ("SUPPLEMENTS", "EN", "NORM", "VERDICT", "WB_QUERY"):
        assert len(getattr(config, name)) == 25, name


def test_keys_consistent():
    keys = set(config.SUPPLEMENTS)
    for name in ("EN", "NORM", "VERDICT", "WB_QUERY"):
        assert set(getattr(config, name)) == keys, name


def test_verdict_values():
    assert set(config.VERDICT.values()) <= {-1, 0, 1}