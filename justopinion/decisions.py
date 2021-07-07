from __future__ import annotations

from dataclasses import dataclass, field
import datetime
import operator
from typing import Iterable, Iterator, List
from typing import Optional, Sequence, Union


from anchorpoint.textselectors import TextQuoteSelector
from pydantic import BaseModel, validator


class CAPCitation(BaseModel):
    cite: str
    reporter: Optional[str] = None
    category: Optional[str] = None
    case_ids: List[int] = field(default_factory=list)


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
    author: Optional[str] = None
    text: Optional[str] = field(default=None, repr=False)

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


class Decision(BaseModel):
    r"""
    A court decision to resolve a step in litigation.
    Uses the model of a judicial decision from
    the `Caselaw Access Project API <https://api.case.law/v1/cases/>`_.
    One of these records may contain multiple :class:`.Opinion`\s.
    Typically one record will contain all
    the :class:`~authorityspoke.opinions.Opinion`\s
    from one appeal, but not necessarily from the whole lawsuit. One
    lawsuit may contain multiple appeals or other petitions, and
    if more then one of those generates published Opinions,
    the CAP API will divide those Opinions into a separate
    record for each appeal.
    The outcome of a decision may be determined by one majority
    :class:`~authorityspoke.opinions.Opinion` or by the combined
    effect of multiple Opinions.
    The lead opinion is commonly, but not always, the only
    Opinion that creates binding legal authority.
    Usually every :class:`~authorityspoke.rules.Rule` posited by the lead Opinion is
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
    :param _id:
        unique ID from CAP API
    """

    def __init__(
        self,
        date: datetime.date,
        name: Optional[str] = None,
        name_abbreviation: Optional[str] = None,
        citations: Optional[Sequence[CAPCitation]] = None,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        court: Optional[str] = None,
        opinions: Optional[Union[Opinion, Sequence[Opinion]]] = None,
        jurisdiction: Optional[str] = None,
        cites_to: Optional[Sequence[CAPCitation]] = None,
        id: Optional[int] = None,
    ) -> None:
        self.date = date
        self.name = name
        self.name_abbreviation = name_abbreviation
        self.citations = citations
        self.first_page = first_page
        self.last_page = last_page
        self.court = court
        if isinstance(opinions, Opinion):
            self.opinions = [opinions]
        elif not opinions:
            self.opinions = []
        else:
            self.opinions = list(opinions)
        self.jurisdiction = jurisdiction
        self.cites_to = cites_to
        self._id = id

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
