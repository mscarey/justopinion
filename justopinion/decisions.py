"""Data models for published judicial decisions."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Optional, Sequence, Union

from anchorpoint import TextPositionSelector, TextQuoteSelector, TextPositionSet
from anchorpoint.textselectors import TextPositionSetFactory, TextSequence
from pydantic import BaseModel, Field, HttpUrl, field_validator

from justopinion.citations import CAPCitation, ReporterCitation


class ReporterVolume(BaseModel):
    """
    A group of decisions corresponding to a bound print volume.

    :param id:
        The unique identifier for this volume.
    :param url:
        The URL of this volume in the Case Access Project API.
    :param full_name:
        The name of this volume.
    """

    id: int
    url: HttpUrl
    full_name: str


class Court(BaseModel):
    """
    A court that issues legal decisions.

    :param id:
        The unique identifier for this court.
    :param name:
        The name of this court.
    :param url:
        The URL of this court in the Case Access Project API.
    :param slug:
        The URL-safe name of this court.
    :param name_abbreviation:
        The abbreviation of this court's name.
    """

    id: int
    name: str
    url: HttpUrl
    slug: str
    name_abbreviation: str = ""


class Jurisdiction(BaseModel):
    """
    A government or other entity that is responsible for a legal system.

    :param id:
        The unique identifier for this jurisdiction.
    :param name:
        The name of this jurisdiction.
    :param url:
        The URL of this jurisdiction in the Case Access Project API.
    :param slug:
        The URL-safe name of this jurisdiction.
    :param whitelisted:
        Whether the jurisdiction's cases are accessible without restriction
        in the Case Access Project API.
    :param name_abbreviation:
        The abbreviation of this jurisdiction.
    """

    id: int
    name: str
    url: HttpUrl
    slug: str
    whitelisted: bool
    name_abbreviation: str = ""


class Opinion(BaseModel):
    """
    A document that resolves legal issues in a case and posits legal holdings.

    Usually an opinion must have ``type="majority"``
    to create holdings binding on any courts.

    :param type:
        the opinion's attitude toward the court's disposition of the case.
        e.g. ``majority``, ``dissenting``, ``concurring``, ``concurring in the result``
    :param author:
        name of the judge who authored the opinion, if identified
    :param text:
    """

    type: str = "majority"
    author: str = ""
    text: str = Field(default="")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(type="{self.type}", author="{self.author}")'

    def __str__(self):
        result = f"{self.type} opinion" if self.type else "opinion"
        if self.author:
            result += f" by {self.author}"
        return result

    @field_validator("author", mode="before")
    def remove_author_name_punctuation(cls, v: str | None) -> str:
        """Normalize Opinion author names by removing punctuation."""
        result = v or ""
        result = result.replace("Judge.", "Judge").replace("Justice.", "Justice")
        return result.strip(", -:;")

    def locate_text(
        self,
        selection: Union[
            bool,
            str,
            TextPositionSelector,
            TextQuoteSelector,
            Sequence[Union[str, TextQuoteSelector, TextPositionSelector]],
        ],
    ) -> TextPositionSet:
        """Get set of position selectors for text in Opinion."""
        factory = TextPositionSetFactory(self.text)
        return factory.from_selection(selection)

    def select_text(self, selector: TextQuoteSelector) -> TextSequence:
        r"""
        Get text using a :class:`.TextQuoteSelector`.

        :param selector:
            a selector referencing a text passage in the :class:`Opinion`.

        :returns:
            the text referenced by the selector, or ``None`` if the text
            can't be found.
        """
        text_locations = self.locate_text(selector)
        return text_locations.as_text_sequence(self.text)


class OpinionCL(Opinion):
    """A judicial opinion from the CourtListener API."""

    resource_uri: HttpUrl
    id: int
    absolute_url: str
    cluster_id: int
    author_id: int | None
    author: str = Field(alias="author_str", default="")
    per_curiam: bool = False
    joined_by: list[str] = []
    joined_by_str: str = ""
    date_created: datetime.datetime
    date_modified: datetime.datetime
    judges: str = ""
    sha1: str = ""
    page_count: int | None = None
    download_url: HttpUrl | None = None
    local_path: str | None = None
    text: str = Field(alias="plain_text", default="")
    html: str = ""
    html_lawbox: str = ""
    html_columbia: str = ""
    html_anon_2020: str = ""
    xml_harvard: str = ""
    html_with_citations: str = ""
    extracted_by_ocr: bool = False
    opinions_cited: list[HttpUrl] = []


class PrecedentialStatus(Enum):
    PUBLISHED = "Published"
    UNPUBLISHED = "Unpublished"


class OpinionCluster(BaseModel):
    """
    A group of opinions that are related to each other, from the CourtListener API.

    https://www.courtlistener.com/api/rest/v4/clusters/
    """

    resource_uri: HttpUrl
    id: int
    absolute_url: str
    docket_id: int
    docket: HttpUrl
    citations: List[ReporterCitation]
    sub_opinions: List[HttpUrl]
    date_created: datetime.datetime
    date_modified: datetime.datetime
    judges: str
    date_filed: datetime.date
    date_filed_is_approximate: bool
    slug: str
    case_name_short: str = ""
    case_name: str
    case_name_full: str = ""
    attorneys: str = ""
    precedential_status: PrecedentialStatus = PrecedentialStatus.PUBLISHED
    blocked: bool = False
    headmatter: str = ""


class CaseData(BaseModel):
    """The content of a Decision, including Opinions."""

    head_matter: Optional[str] = None
    corrections: Optional[str] = None
    parties: List[str] = []
    attorneys: List[str] = []
    opinions: List[Opinion] = []
    judges: List[str] = []


class PageRank(BaseModel):
    """The rank of the Decision in the collection of documents."""

    percentile: float
    raw: float


class CaseBody(BaseModel):
    """Data about an Opinion in the form used by the Caselaw Access Project API."""

    data: CaseData
    status: str = ""


class DecisionAnalysis(BaseModel):
    """Data generated by Case Access Project about a Decision."""

    word_count: int
    sha256: str
    orc_confidence: Optional[float] = None
    char_count: int
    pagerank: Optional[PageRank] = None
    cardinality: int
    simhash: str


class DecisionError(Exception):
    """Error for failed attempts to assign Opinions to Decisions."""

    pass


class CitationResponse(BaseModel):
    """
    A response from the CourtListener API for a citation query.

    :param results:
        The list of citations found in the query.
    :param next:
        The URL of the next page of results, if any.
    """

    citation: str
    normalized_citations: list[str]
    start_index: int
    end_index: int
    status: int
    error_message: str
    clusters: list[OpinionCluster] = []


class DecisionCL(BaseModel):
    opinion_clusters: List[OpinionCluster] = []
    resource_uri: HttpUrl
    id: int
    court: HttpUrl
    court_id: str
    clusters: List[str]
    absolute_url: str
    date_created: datetime.datetime
    date_modified: datetime.datetime
    source: int | None = None
    appeal_from_str: str = ""
    assigned_to_str: str = ""
    referred_to_str: str = ""
    panel_str: str = ""
    case_name: str = ""
    case_name_full: str = ""
    slug: str
    docket_number: str
    blocked: bool = False

    def __str__(self):
        cluster = self.opinion_clusters[0] if self.opinion_clusters else None
        decision_date = f" ({cluster.date_filed.isoformat()})" if cluster else ""
        citation = cluster.citations[0] if cluster else ""
        return f"{self.case_name}, {str(citation)}{decision_date}"


class Decision(BaseModel):
    r"""
    A court decision to resolve a step in litigation.

    Uses the model of a judicial decision from
    the `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.

    One of these records may contain multiple :class:`.Opinion`\s.
    Typically one record will contain all
    the :class:`~justopinion.decisions.Opinion`\s
    from one appeal, but not necessarily from the whole lawsuit. One
    lawsuit may contain multiple appeals or other petitions, and
    if more then one of those generates published Opinions,
    the CAP API will divide those Opinions into a separate
    record for each appeal.
    The outcome of a decision may be determined by one majority
    :class:`~justopinion.decisions.Opinion` or by the combined
    effect of multiple Opinions.
    The lead opinion is commonly, but not always, the only
    Opinion that creates binding legal authority.
    Usually every rule posited by the lead Opinion is
    binding, but some may not be, often because parts of the
    Opinion fail to command a majority of the panel
    of judges.

    :param decision_date:
        date when the opinion was first published by the court
        (not the publication date of the reporter volume)
    :param name:
        full name of the opinion, e.g. "ORACLE AMERICA, INC.,
        Plaintiff-Appellant, v. GOOGLE INC., Defendant-Cross-Appellant"
    :param name_abbreviation:
        shorter name of the opinion, e.g. "Oracle America, Inc. v. Google Inc."
    :param docket_num:
    :param citations:
        ways to cite this Decision
    :param parties:
    :param attorneys:
    :param first_page:
        the page where the opinion begins in its official reporter
    :param last_page:
        the page where the opinion ends in its official reporter
    :param court:
        name of the court that published the opinion
    :param casebody:
        the Decision content including Opinions
    :param juridiction:
        the jurisdiction of the case
    :param cites_to:
        :class:`~justopinion.citations.CAPCitation`\s to other Decisions
    :param id:
        unique ID from CAP API
    :param last_updated:
        date when the record was last updated in CAP API
    :param frontend_url:
        URL to the decision in CAP's frontend
    :param analysis:
        data generated by Case Access Project about this Decision
    """

    decision_date: datetime.date
    name: Optional[str] = None
    name_abbreviation: Optional[str] = None
    docket_num: Optional[str] = None
    citations: Optional[Sequence[CAPCitation]] = None
    parties: List[str] = []
    attorneys: List[str] = []
    first_page: Optional[int] = None
    last_page: Optional[int] = None
    court: Optional[Court] = None
    casebody: Optional[CaseBody] = None
    jurisdiction: Optional[Jurisdiction] = None
    cites_to: Optional[Sequence[CAPCitation]] = None
    id: Optional[int] = None
    last_updated: Optional[datetime.datetime] = None
    frontend_url: Optional[HttpUrl] = None
    analysis: Optional[DecisionAnalysis] = None

    def __str__(self):
        citation = self.citations[0].cite if self.citations else ""
        name = self.name_abbreviation or self.name
        return f"{name}, {citation} ({self.decision_date})"

    @field_validator("decision_date", mode="before")
    def decision_date_must_include_day(
        cls, v: datetime.date | str
    ) -> datetime.date | str:
        """Add a day of "01" if a string format is missing it."""
        if isinstance(v, str) and len(v) == 7:
            return v + "-01"
        return v

    @property
    def opinions(self) -> List[Opinion]:
        """Get all Opinions published with this Decision."""
        return self.casebody.data.opinions if self.casebody else []

    @property
    def majority(self) -> Optional[Opinion]:
        """Get a majority opinion, if any."""
        for opinion in self.opinions:
            if opinion.type == "majority":
                return opinion
        return None

    def find_matching_opinion(
        self,
        opinion_type: str = "",
        opinion_author: str = "",
    ) -> Optional[Opinion]:
        """Get Opinion matching the given attributes."""
        if not opinion_type and not opinion_author:
            if len(self.opinions) >= 1:
                return self.opinions[0]
            return None
        for opinion in self.opinions:
            if ((opinion_type == opinion.type) or not opinion_type) and (
                (opinion_author == opinion.author) or not opinion_author
            ):
                return opinion
        return None

    def add_opinion(self, opinion: Opinion) -> None:
        """Add an Opinion to self's CaseBody if the Opinion doesn't already exist."""
        existing = self.find_matching_opinion(
            opinion_type=opinion.type, opinion_author=opinion.author
        )
        if existing:
            raise DecisionError(
                f"Decision {self} already has an Opinion with type {existing.type} and author {existing.author}."
            )
        self.casebody = self.casebody or CaseBody(data=CaseData())
        self.casebody.data.opinions.append(opinion)
