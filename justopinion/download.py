"""Downloading data that can be converted to Opinion and Decision objects."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import eyecite
from eyecite.models import CaseCitation
import requests

from justopinion.decisions import CAPCitation, Decision


class CaseAccessProjectAPIError(Exception):
    """Error for invalid API query."""

    pass


def normalize_case_cite(cite: Union[str, CaseCitation, CAPCitation]) -> str:
    """Get just the text that identifies a citation."""
    if isinstance(cite, CAPCitation):
        return cite.cite
    if isinstance(cite, str):
        possible_cites = list(eyecite.get_citations(cite))
        bad_cites = []
        for possible in possible_cites:
            if isinstance(possible, CaseCitation):
                return possible.corrected_citation()
            bad_cites.append(possible)
        error_msg = f"Could not locate a CaseCitation in the text {cite}."
        for bad_cite in bad_cites:
            error_msg += f" {str(bad_cite)} was type {bad_cite.__class__.__name__}, not CaseCitation."
        raise ValueError(error_msg)
    return cite.corrected_citation()


class CAPClient:
    """Downloads Decisions from Case Access Project API."""

    def __init__(self, api_token: Optional[str] = ""):

        """Create download client with an API token and an API address."""
        self.endpoint = f"https://api.case.law/v1/cases/"
        if api_token and api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token or ""

    def get_api_headers(self, full_case: bool = False) -> Dict[str, str]:
        """Get API headers based on whether the full case text is requested."""
        api_dict = {}
        if full_case:
            if not self.api_token:
                raise CaseAccessProjectAPIError(
                    "To fetch full opinion text using the full_case parameter, "
                    "set the CAPClient's 'api_key' attribute to "
                    "your API key for the Case Access Project. See https://api.case.law/"
                )
            api_dict["Authorization"] = f"Token {self.api_token}"
        return api_dict

    def fetch_cite(
        self, cite: Union[str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> requests.models.Response:
        """
        Get the API list response for a queried citation from the CAP API.
        :param cite:
            a citation linked to an opinion in the
            `Caselaw Access Project database <https://case.law/api/>`_.
            Usually these will be in the traditional format
            ``[Volume Number] [Reporter Name Abbreviation] [Page Number]``, e.g.
            `750 F.3d 1339 <https://case.law/search/#/cases?page=1&cite=%22750%20F.3d%201339%22>`_
            for Oracle America, Inc. v. Google Inc.
        :param full_case:
            whether to request the full text of the opinion from the
            `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.
            If this is ``True``, the CAPClient must have the `api_token` attribute.
        :returns:
            the "results" list for this queried citation.
        """

        normalized_cite = normalize_case_cite(cite)

        params = {"cite": normalized_cite}

        headers = self.get_api_headers(full_case=full_case)

        if full_case:
            params["full_case"] = "true"
        return requests.get(self.endpoint, params=params, headers=headers)

    def read_decision_list_by_cite(
        self, cite: Union[str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> List[Decision]:
        """
        Download and deserialize the "results" list for a queried citation from the CAP API.
        :param cite:
            a citation linked to an opinion in the
            `Caselaw Access Project database <https://case.law/api/>`_.
            Usually these will be in the traditional format
            ``[Volume Number] [Reporter Name Abbreviation] [Page Number]``, e.g.
            `750 F.3d 1339 <https://case.law/search/#/cases?page=1&cite=%22750%20F.3d%201339%22>`_
            for Oracle America, Inc. v. Google Inc.
        :param full_case:
            whether to request the full text of the opinion from the
            `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.
            If this is ``True``, the CAPClient must have the `api_token` attribute.
        :returns:
            the first case in the "results" list for this queried citation.
        """
        response = self.fetch_cite(cite=cite, full_case=full_case)
        results = response.json()["results"]
        return [Decision(**result) for result in results]

    def read_cite(
        self, cite: Union[str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> Decision:
        """
        Download and deserialize a Decision from Caselaw Access Project API.
        :param cite:
            a citation linked to an opinion in the
            `Caselaw Access Project database <https://case.law/api/>`_.
            Usually these will be in the traditional format
            ``[Volume Number] [Reporter Name Abbreviation] [Page Number]``, e.g.
            `750 F.3d 1339 <https://case.law/search/#/cases?page=1&cite=%22750%20F.3d%201339%22>`_
            for Oracle America, Inc. v. Google Inc.
        :param full_case:
            whether to request the full text of the opinion from the
            `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.
            If this is ``True``, the CAPClient must have the `api_token` attribute.
        :returns:
            the first case in the "results" list for this queried citation.
        """
        response = self.fetch_cite(cite=cite, full_case=full_case)
        result = response.json()["results"][0]
        return Decision(**result)

    def fetch_id(self, cap_id: int, full_case: bool = False) -> RawDecision:
        """
        Download a decision from Caselaw Access Project API.
        :param cap_id:
            an identifier for an opinion in the
            `Caselaw Access Project database <https://case.law/api/>`_,
            e.g. 4066790 for
            `Oracle America, Inc. v. Google Inc. <https://api.case.law/v1/cases/4066790/>`_.
        :param full_case:
            whether to request the full text of the opinion from the
            `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.
            If this is ``True``, the CAPClient must have the `api_token` attribute.
        :returns:
            the first case in the "results" list for this queried citation.
        """
        url = self.endpoint + f"{cap_id}/"
        headers = self.get_api_headers(full_case=full_case)
        params = {}
        if full_case:
            params["full_case"] = "true"
        response = requests.get(url, params=params, headers=headers).json()
        if cap_id and response.get("detail") == "Not found.":
            raise CaseAccessProjectAPIError(f"API returned no cases with id {cap_id}")
        return response

    def read_id(self, cap_id: int, full_case: bool = False) -> Decision:
        """
        Download a decision from Caselaw Access Project API.
        :param cap_id:
            an identifier for an opinion in the
            `Caselaw Access Project database <https://case.law/api/>`_,
            e.g. 4066790 for
            `Oracle America, Inc. v. Google Inc. <https://api.case.law/v1/cases/4066790/>`_.
        :param full_case:
            whether to request the full text of the opinion from the
            `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.
            If this is ``True``, the CAPClient must have the `api_token` attribute.
        :returns:
            a Decision created from the first case in the "results" list for
            this queried citation.
        """
        response = self.fetch_id(cap_id=cap_id, full_case=full_case)
        schema = DecisionSchema()
        return schema.load(response)

    def fetch(
        self, query: Union[int, str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> RawDecision:
        """Query by CAP id or citation, and download Decision from CAP API."""
        if isinstance(query, int) or (isinstance(query, str) and query.isdigit()):
            return self.fetch_id(int(query), full_case=full_case)
        return self.fetch_cite(query)

    def read(
        self, query: Union[int, str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> Decision:
        """Query by CAP id or citation, download, and load Decision from CAP API."""
        if isinstance(query, int) or (isinstance(query, str) and query.isdigit()):
            return self.read_id(int(query), full_case=full_case)
        return self.read_cite(query)
