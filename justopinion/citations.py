"""Citations used for cross-referencing caselaw."""

from typing import List, Optional, Union

from eyecite import get_citations
from eyecite.models import CaseCitation
from pydantic import BaseModel


class CAPCitation(BaseModel):
    """
    A case citation generated by the Case Access Project.

    Not to be confused with a CaseCitation created by the Eyecite library.

    :param cite:
        The text making up the citation.
    :param reporter:
        Identifier for the reporter cited to.
    :param category:
        The type of document cited, e.g. "reporters:federal"
    :param case_ids:
        A list of Case Access Project IDs for the cited case.
    :param type:
        The kind of citation, e.g. "official"
    """

    cite: str
    reporter: Optional[str] = None
    category: Optional[str] = None
    case_ids: List[int] = []
    type: Optional[str] = None

    def __str__(self) -> str:
        return f"Citation to {self.cite}"


class ReporterCitation(BaseModel):
    """
    The volume, reporter, and initial page number of a case in a reporter.

    Based on the CourtListener API's Cluster endpoint's citation object.
    """

    volume: int
    reporter: str
    page: str

    def __str__(self) -> str:
        return f"{self.volume} {self.reporter} {self.page}"


def normalize_case_cite(cite: Union[str, CaseCitation, CAPCitation]) -> str:
    """Get just the text that identifies a citation."""
    if isinstance(cite, CAPCitation):
        return cite.cite
    if isinstance(cite, str):
        possible_cites = list(get_citations(cite))
        bad_cites = []
        for possible in possible_cites:
            if isinstance(possible, CaseCitation):
                return possible.corrected_citation()
            bad_cites.append(possible)
        error_msg = f"Could not locate a CaseCitation in the text {cite}."
        for bad_cite in bad_cites:
            error_msg += (
                f" {bad_cite} was type {bad_cite.__class__.__name__}, not CaseCitation."
            )

        raise ValueError(error_msg)
    return cite.corrected_citation()
