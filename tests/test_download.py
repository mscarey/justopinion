import datetime
import os

from dotenv import load_dotenv
import pytest

from justopinion.decisions import Decision, Opinion
from justopinion.download import CAPClient


load_dotenv()


class TestDownloads:
    client = CAPClient(api_token=os.getenv("CAP_API_KEY"))

    @pytest.mark.vcr
    def test_download_case_by_id(self):
        case = self.client.fetch(4066790)
        assert case["name_abbreviation"] == "Oracle America, Inc. v. Google Inc."
        assert case["id"] == 4066790

    @pytest.mark.default_cassette("TestDownloads.test_download_case_by_id.yaml")
    @pytest.mark.vcr
    def test_download_case_by_string_id(self):
        case = self.client.fetch("4066790")
        assert case["name_abbreviation"] == "Oracle America, Inc. v. Google Inc."

    @pytest.mark.vcr
    def test_read_decision(self):
        decision = self.client.read_cite("1 Breese 34", full_case=True)
        assert isinstance(decision, Decision)
        assert isinstance(decision.opinions[0], Opinion)
        assert decision.opinions[0].author is None
        assert decision.opinions[0].position == "majority"

    @pytest.mark.default_cassette("TestDownloads.test_read_decision.yaml")
    @pytest.mark.vcr
    def test_fetch_decision(self):
        response = self.client.fetch_cite("1 Breese 34", full_case=True)
        assert response.status_code == 200
        result = response.json().get("results")[0]
        assert result["id"] == 435800
        assert result["casebody"]["data"]["head_matter"].startswith("John")
