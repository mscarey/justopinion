import datetime
import os

from dotenv import load_dotenv
import pytest

from justopinion.decisions import Decision, Opinion
from justopinion.download import CAPClient


load_dotenv()


class TestDownloads:
    @pytest.mark.vcr
    def test_download_file(self):
        client = CAPClient(api_token=os.getenv("CAP_API_KEY"))
        decision = client.read_cite("1 Breese 34", full_case=True)
        assert isinstance(decision, Decision)
        assert isinstance(decision.opinions[0], Opinion)
        assert isinstance(decision.opinions[0].author, str)
        assert isinstance(decision.opinions[0].date, datetime.datetime)
