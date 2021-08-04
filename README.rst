Justopinion
===========

A Python library for downloading and researching legal opinions
using the `Case Access Project API`_.

.. image:: https://img.shields.io/badge/open-ethical-%234baaaa
    :target: https://ethicalsource.dev/licenses/
    :alt: An Ethical Open Source Project

.. image:: https://coveralls.io/repos/github/mscarey/justopinion/badge.svg?branch=master
    :target: https://coveralls.io/github/mscarey/justopinion?branch=master
    :alt: Test Coverage Percentage

.. image:: https://github.com/mscarey/justopinion/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/mscarey/justopinion/actions
    :alt: GitHub Actions Workflow

.. image:: https://readthedocs.org/projects/justopinion/badge/?version=latest
    :target: https://nettlesome.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Examples
--------

In this example, Justopinion is used to download the decision with the citation `1 Breese 34`.

    >>> from justopinion import CAPClient
    >>> client = CAPClient(api_token="your-secret-api-token")
    >>> thornton = client.read_cite("1 Breese 34", full_case=True)
    >>> thornton.casebody.data.parties[0]
    'John Thornton and others, Appellants, v. George Smiley and John Bradshaw, Appellees.'

You can also use Justopinion to locate text in an opinion:

    >>> thornton.opinions[0].locate_text("The court knows of no power in the administrator")
    TextPositionSet{TextPositionSelector[22, 70)}

Or to get the text from a specified location in the opinion:

    >>> selection = thornton.opinions[0].select_text([(258, 294), (312, 359)])
    >>> str(selection)
    '…The note was made to West alone, and…the suit should have been commenced in his name…'

And you can use Justopinion to follow citations in an opinion and download the cited cases:

    >>> str(thornton.cites_to[0])
    'Citation to 15 Ill., 284'
    >>> cited = client.read_cite(thornton.cites_to[0], full_case=True)
    >>> str(cited)
    'Marsh v. People, 15 Ill. 284 (1853-12-01)'

.. _Case Access Project API: https://api.case.law/v1/