import os

from dotenv import load_dotenv
import eyecite
import pytest

from justopinion.decisions import CAPCitation, Decision, Opinion
from justopinion.download import (
    CAPClient,
    CaseAccessProjectAPIError,
    normalize_case_cite,
)


load_dotenv()


class TestDownloads:
    client = CAPClient(api_token=os.getenv("CAP_API_KEY"))

    @pytest.mark.vcr
    def test_download_case_by_id(self):
        case = self.client.fetch(4066790).json()
        assert case["name_abbreviation"] == "Oracle America, Inc. v. Google Inc."
        assert case["id"] == 4066790

    @pytest.mark.default_cassette("TestDownloads.test_download_case_by_id.yaml")
    @pytest.mark.vcr
    def test_read_case_by_id(self):
        case = self.client.read_id(4066790)
        assert case.name_abbreviation == "Oracle America, Inc. v. Google Inc."
        assert case.id == 4066790
        name = "Oracle America, Inc. v. Google Inc., 750 F.3d 1339 (2014-05-09)"
        assert str(case) == name

    @pytest.mark.default_cassette("TestDownloads.test_download_case_by_id.yaml")
    @pytest.mark.vcr
    def test_download_case_by_string_id(self):
        case = self.client.fetch("4066790")
        assert case.json()["name_abbreviation"] == "Oracle America, Inc. v. Google Inc."

    @pytest.mark.vcr
    def test_full_case_by_cite(self):
        response = self.client.fetch("49 F.3d 807", full_case=True)
        lotus = response.json()["results"][0]
        assert lotus["decision_date"] == "1995-03-09"
        assert lotus["casebody"]["data"]["opinions"][0]["author"].startswith("STAHL")

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

    @pytest.mark.default_cassette("TestDownloads.test_full_case_by_cite.yaml")
    @pytest.mark.vcr
    def test_download_and_make_opinion(self):
        cases = self.client.read_decision_list_by_cite(
            cite="49 F.3d 807", full_case=True
        )
        lotus = cases[0]
        lotus_opinion = lotus.majority
        assert lotus_opinion.__class__.__name__ == "Opinion"

    @pytest.mark.default_cassette("TestDownloads.test_full_case_by_cite.yaml")
    @pytest.mark.vcr
    def test_full_case_as_json(self):
        lotus = self.client.read("49 F.3d 807", full_case=True)
        assert "Lotus" in lotus.name_abbreviation

    def test_error_download_without_case_reference(self):
        with pytest.raises(TypeError):
            self.client.fetch_cite()

    @pytest.mark.vcr
    def test_error_bad_cap_id(self):
        with pytest.raises(CaseAccessProjectAPIError):
            self.client.fetch_id(cap_id=99999999)

    def test_error_bad_cite(self):
        with pytest.raises(ValueError):
            self.client.fetch_cite(cite="999 Cal 9th. 9999")

    @pytest.mark.vcr
    def test_error_full_case_download_without_api_key(self):
        bad_client = CAPClient()
        with pytest.raises(CaseAccessProjectAPIError):
            bad_client.fetch_cite(cite="49 F.3d 807", full_case=True)

    @pytest.mark.vcr
    def test_read_case_from_citation(self):
        citation = CAPCitation(
            cite="460 F. 3d 337",
            reporter="F.3d",
            category="reporters:federal",
            case_ids=[3674823],
            type=None,
        )
        case = self.client.read_cite(citation)
        assert case.id == 3674823

    @pytest.mark.vcr("TestDownloads.test_read_case_from_citation.yaml")
    def test_read_cited_case_from_id_using_client(self):
        case = self.client.read(query=3675682, full_case=False)
        assert case.name_abbreviation == "Kimbrough v. United States"
        cited_case = self.client.read_cite(cite=case.cites_to[0])
        assert cited_case.name_abbreviation == "United States v. Castillo"

    @pytest.mark.vcr
    def test_read_case_list_from_eyecite_case_citation(self):
        case_citation = eyecite.get_citations("9 F. Cas. 50")[0]
        cases_again = self.client.read_decision_list_by_cite(cite=case_citation)
        assert cases_again[0].name_abbreviation == "Fikes v. Bentley"

    @pytest.mark.vcr
    def test_fail_to_read_id_cite(self):
        with pytest.raises(ValueError, match="was type IdCitation, not CaseCitation"):
            self.client.read_decision_list_by_cite(cite="id. at 37")


class TestDecisions:
    client = CAPClient(api_token=os.getenv("CAP_API_KEY"))

    def test_normalize_case_cite(self):
        assert normalize_case_cite("3 US 100") == "3 U.S. 100"

    @pytest.mark.default_cassette("TestDownloads.test_download_case_by_id.yaml")
    @pytest.mark.vcr
    def test_no_majority_without_full_case(self):
        case = self.client.read_id(4066790)
        assert case.name_abbreviation == "Oracle America, Inc. v. Google Inc."
        assert case.majority is None
