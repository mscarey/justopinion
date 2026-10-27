"""Download client for legal opinions."""

from justopinion.decisions import Decision, Opinion
from justopinion.download import CAPClient

__all__ = ["CAPClient", "Decision", "Opinion"]
__version__ = "0.5.0"
