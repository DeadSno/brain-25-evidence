from src import config


def test_all_dicts_41():
    for name in ("SUPPLEMENTS", "EN", "NORM", "WB_QUERY"):
        assert len(getattr(config, name)) == 41, name


def test_keys_consistent():
    keys = set(config.SUPPLEMENTS)
    for name in ("EN", "NORM", "WB_QUERY"):
        assert set(getattr(config, name)) == keys, name