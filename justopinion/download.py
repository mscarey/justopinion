"""Download client for data that can be converted to :class:`~justopinion.decisions.Decision` and :class:`~justopinion.decisions.Opinion` objects."""

from __future__ import annotations

from typing import Dict, List, Optional, Union

import requests

from justopinion.citations import CaseCitation, normalize_case_cite
from justopinion.decisions import (
    CAPCitation,
    CitationResponse,
    OpinionCL,
    Decision,
    DecisionCL,
    OpinionCluster,
)


class CourtListenerClient:
    """Downloads judicial decisions from CourtListener API."""

    def __init__(self, api_token: str):
        self.endpoint = "https://www.courtlistener.com/api/rest/v4/"
        if api_token and api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token

    def get_api_headers(self, full_case: bool = False) -> Dict[str, str]:
        """Get API headers based on whether the full case text is requested."""
        api_dict = {}
        if full_case:
            api_dict["Authorization"] = f"Token {self.api_token}"
        return api_dict

    def fetch(
        self, query: Union[int, str, CaseCitation], full_case: bool = False
    ) -> requests.models.Response:
        """Query by CourtListener id or citation, and download Docket from CourtListener API."""
        if isinstance(query, int) or (isinstance(query, str) and query.isdigit()):
            return self.fetch_id(int(query), full_case=full_case)
        return self.fetch_cite(query)

    def fetch_cite(self, cite: Union[str, CaseCitation]) -> requests.models.Response:
        """
        Get the API list response for a queried citation from the CourtListener API.

        This will require a query to the `citation-lookup endpoint <https://www.courtlistener.com/api/rest/v4/citation-lookup/>`,
        so the CourtListenerClient will need to have the `api_token` attribute.

        :param cite:
            a citation linked to an opinion in the
            `CourtListener database <https://www.courtlistener.com/help/api/rest/>`_.
            Usually these will be in the traditional format
            ``[Volume Number] [Reporter Name Abbreviation] [Page Number]``, e.g.
            `750 F.3d 1339`
            for Oracle America, Inc. v. Google Inc.
        :param full_case:
            whether to request the full text of the opinion from the
            `API's Opinions endpoint <https://www.courtlistener.com/api/rest/v4/opinions/>`_.
        :returns:
            the "results" list for this queried citation.
        """

        normalized_cite = normalize_case_cite(cite)
        volume, reporter, page = normalized_cite.split(" ")

        # CourtListener requires an API key for a cite lookup
        headers = self.get_api_headers(full_case=True)
        lookup_endpoint = self.endpoint + "citation-lookup/"
        params = {"reporter": reporter, "volume": volume, "page": page}
        response = requests.get(lookup_endpoint, data=params, headers=headers)
        if response.status_code == 401:
            detail = response.json()["detail"]
            raise CourtListenerAPIError(f"{detail}")
        return response

    def fetch_id(self, id: int, full_case: bool = False) -> requests.models.Response:
        """
        Download a decision from CourtListener API.

        :param id:
            an identifier for a docket in the
            `CourtListener database <https://www.courtlistener.com/api/rest/v4/>`_,
            e.g. 260804 for
            `Oracle America, Inc. v. Google Inc. <https://www.courtlistener.com/api/rest/v4/dockets/260804/>`_.
        :param full_case:
            whether to request the full text of the opinion (unused in CourtListener API).
        :returns:
            the first case in the "results" list for this queried citation.
        """
        url = self.endpoint + f"dockets/{id}/"
        headers = self.get_api_headers(full_case=True)
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise CourtListenerAPIError(f"API returned no cases with id {id}")
        return response

    def read_id(self, id: int, full_case: bool = False) -> DecisionCL:
        """
        Download a decision from Caselaw Access Project API.

        :param cap_id:
            an identifier for a docket in the
            `CourtListener <https://www.courtlistener.com/>`_ database,
            e.g. 260804 for
            `Oracle America, Inc. v. Google Inc. <https://www.courtlistener.com/api/rest/v4/dockets/260804/>`_.
        :param full_case:
            whether to request the full text of the opinion from the
            `CourtListener API <https://www.courtlistener.com/api/rest/v4/>`_.
            If this is ``True``, the CourtListenerClient must have the `api_token` attribute.
        :returns:
            a Decision created from the first case in the "results" list for
            this queried citation.
        """
        result = self.fetch_id(id=id, full_case=full_case)

        decision = DecisionCL(**result.json())
        if decision.clusters:
            headers = self.get_api_headers(full_case=full_case)
            response = requests.get(decision.clusters[0], headers=headers)
            decision.opinion_clusters = [OpinionCluster(**response.json())]
        return decision

    def read_decision_from_response(
        self, response: requests.models.Response
    ) -> DecisionCL:
        """
        Deserialize a list of cases from the "results" list of a response from the CourtListener API.

        :param response:
            a response from the CourtListener API

        :returns:
            all decisions in the "results" list for the response
        """
        first_result = response.json()[0]
        decision = DecisionCL(**first_result)
        if decision.clusters:
            headers = self.get_api_headers(full_case=True)
            response = requests.get(decision.clusters[0], headers=headers)
            decision.opinion_clusters = [OpinionCluster(**response.json())]
        return decision

    def read_citation_response(
        self, response: requests.models.Response
    ) -> CitationResponse:
        """
        Deserialize a single case from the "results" list of a response from the CourtListener API.

        :param response:
            a response from the CourtListener API

        :returns:
            the first decision in the "results" list for the response
        """
        citation_response = response.json()[0]
        return CitationResponse(**citation_response)

    def read_cite(self, cite: Union[str, CaseCitation]) -> CitationResponse:
        """
        Download a decision from Caselaw Access Project API.

        :param cap_id:
            an identifier for a docket in the
            `CourtListener <https://www.courtlistener.com/>`_ database,
            e.g. 260804 for
            `Oracle America, Inc. v. Google Inc. <https://www.courtlistener.com/api/rest/v4/dockets/260804/>`_.
        :param full_case:
            whether to request the full text of the opinion from the
            `CourtListener API <https://www.courtlistener.com/api/rest/v4/>`_.
            If this is ``True``, the CourtListenerClient must have the `api_token` attribute.
        :returns:
            a Decision created from the first case in the "results" list for
            this queried citation.
        """
        response = self.fetch_cite(cite=cite)
        return self.read_citation_response(response=response)

    def read_cluster_opinions(self, cluster: OpinionCluster) -> List[OpinionCL]:
        """Download and deserialize all opinions in a cluster."""
        headers = self.get_api_headers(full_case=True)
        return [
            OpinionCL(**response.json())
            for response in [
                requests.get(str(url), headers=headers) for url in cluster.sub_opinions
            ]
        ]


class CAPClient:
    """Downloads judicial decisions from Case Access Project API."""

    def __init__(self, api_token: Optional[str] = ""):
        """Create download client with an API token and an API address."""
        self.endpoint = "https://api.case.law/v1/cases/"
        if api_token and api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token or ""
        self.api_alert = (
            "To fetch full opinion text using the full_case parameter, "
            "set the CAPClient's 'api_key' attribute to "
            "your API key for the Case Access Project. See https://api.case.law/"
        )

    def fetch(
        self, query: Union[int, str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> requests.models.Response:
        """Query by CAP id or citation, and download Decision from CAP API."""
        if isinstance(query, int) or (isinstance(query, str) and query.isdigit()):
            return self.fetch_id(int(query), full_case=full_case)
        return self.fetch_cite(query, full_case=full_case)

    def read(
        self, query: Union[int, str, CaseCitation, CAPCitation], full_case: bool = False
    ) -> Decision:
        """Query by CAP id or citation, download, and load Decision from CAP API."""
        if isinstance(query, int) or (isinstance(query, str) and query.isdigit()):
            return self.read_id(int(query), full_case=full_case)
        return self.read_cite(query, full_case=full_case)

    def get_api_headers(self, full_case: bool = False) -> Dict[str, str]:
        """Get API headers based on whether the full case text is requested."""
        api_dict = {}
        if full_case:
            if not self.api_token:
                raise CaseAccessProjectAPIError(self.api_alert)
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
        response = requests.get(self.endpoint, params=params, headers=headers)
        if response.status_code == 401:
            detail = response.json()["detail"]
            raise CaseAccessProjectAPIError(f"{detail} {self.api_alert}")
        return response

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
        return self.read_decisions_from_response(response)

    def read_decisions_from_response(
        self, response: requests.models.Response
    ) -> List[Decision]:
        """
        Deserialize a list of cases from the "results" list of a response from the CAP API.

        :param response:
            a response from the CAP API

        :returns:
            all decisions in the "results" list for the response
        """
        results = response.json()["results"]
        return [Decision(**result) for result in results]

    def read_decision_from_response(
        self, response: requests.models.Response
    ) -> Decision:
        """
        Deserialize a single case from the "results" list of a response from the CAP API.

        :param response:
            a response from the CAP API

        :returns:
            the first decision in the "results" list for the response
        """
        decision = response.json()
        if "results" in decision:
            return Decision(**decision["results"][0])
        return Decision(**decision)

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
        return self.read_decision_from_response(response=response)

    def fetch_id(
        self, cap_id: int, full_case: bool = False
    ) -> requests.models.Response:
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
        response = requests.get(url, params=params, headers=headers)
        if cap_id and response.status_code == 404:
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
        result = self.fetch_id(cap_id=cap_id, full_case=full_case)

        return Decision(**result.json())


class CaseAccessProjectAPIError(Exception):
    """Error for failed attempts to use the Case Access Project API."""

    pass


class CourtListenerAPIError(Exception):
    """Error for failed attempts to use the CourtListener API."""

    pass
