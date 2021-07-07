from justopinion.download import normalize_case_cite


def test_add():
    assert 1 + 1 == 2


def test_normalize_case_cite():
    assert normalize_case_cite("3 US 100") == "3 U.S. 100"
