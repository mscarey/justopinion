import pytest

from justopinion.download import normalize_case_cite


class TestCitations:
    def test_normalize_case_cite(self):
        assert normalize_case_cite("3 US 100") == "3 U.S. 100"
