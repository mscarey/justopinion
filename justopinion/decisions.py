from __future__ import annotations

import datetime
import re
from typing import Iterable, Iterator, List
from typing import Optional, Sequence, Union


from anchorpoint.textselectors import TextQuoteSelector
from pydantic import BaseModel, validator, HttpUrl


class ReporterVolume(BaseModel):
    url: HttpUrl
    full_name: str
    id: int


class Court(BaseModel):
    id: int
    name: str
    url: HttpUrl
    slug: str
    name_abbreviation: str


class Jurisdiction(BaseModel):
    id: int
    name: str
    url: HttpUrl
    slug: str
    name_abbreviation: str
    whitelisted: bool


class CAPCitation(BaseModel):
    cite: str
    reporter: Optional[str] = None
    category: Optional[str] = None
    case_ids: List[int] = []
    type: Optional[str] = None


class Opinion(BaseModel):
    """
    A document that resolves legal issues in a case and posits legal holdings.
    Usually an opinion must have ``position="majority"``
    to create holdings binding on any courts.
    :param position:
        the opinion's attitude toward the court's disposition of the case.
        e.g. ``majority``, ``dissenting``, ``concurring``, ``concurring in the result``
    :param author:
        name of the judge who authored the opinion, if identified
    :param text:
    """

    position: str = "majority"
    author: Optional[str] = ""
    text: Optional[str] = ""

    def select_text(self, selector: TextQuoteSelector) -> Optional[str]:
        r"""
        Get text using a :class:`.TextQuoteSelector`.
        :param selector:
            a selector referencing a text passage in this :class:`Opinion`.
        :returns:
            the text referenced by the selector, or ``None`` if the text
            can't be found.
        """
        if re.search(selector.passage_regex(), self.text, re.IGNORECASE):
            return selector.exact
        raise ValueError(
            f'Passage "{selector.exact}" from TextQuoteSelector '
            + f'not found in Opinion "{self}".'
        )

    def __str__(self):
        return f"{self.position} Opinion by {self.author}"


class Court(BaseModel):
    id: int
    name: str
    url: HttpUrl
    slug: str
    name_abbreviation: str


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

    :param name:
        full name of the opinion, e.g. "ORACLE AMERICA, INC.,
        Plaintiff-Appellant, v. GOOGLE INC., Defendant-Cross-Appellant"
    :param name_abbreviation:
        shorter name of the opinion, e.g. "Oracle America, Inc. v. Google Inc."
    :param citations:
        citations to the opinion, usually in the format
        ``[Volume Number] [Reporter Name Abbreviation] [Page Number]``
    :param first_page:
        the page where the opinion begins in its official reporter
    :param last_page:
        the page where the opinion ends in its official reporter
    :param decision_date:
        date when the opinion was first published by the court
        (not the publication date of the reporter volume)
    :param court:
        name of the court that published the opinion
    :param id:
        unique ID from CAP API
    :param url:
        URL to the CAP API record

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
    opinions: Optional[Union[Opinion, Sequence[Opinion]]] = None
    jurisdiction: Optional[Jurisdiction] = None
    cites_to: Optional[Sequence[CAPCitation]] = None
    id: Optional[int] = None
    url: Optional[HttpUrl] = None
    last_updated: Optional[datetime.datetime] = None

    def __str__(self):
        citation = self.citations[0].cite if self.citations else ""
        name = self.name_abbreviation or self.name
        return f"{name}, {citation} ({self.date})"

    @property
    def majority(self) -> Optional[Opinion]:
        for opinion in self.opinions:
            if opinion.position == "majority":
                return opinion
        return None
