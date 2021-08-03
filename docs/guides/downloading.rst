..  _downloading:

How to Download Judicial Decisions
=======================================

Justopinion works by downloading data about judicial opinions from
the `Caselaw Access Project API <https://case.law/docs/site_features/api>`__.

To take advantage of all the features of the API (and of justopinion), you'll
need to `register with the Caselaw Access Project and get an API
key <https://case.law/docs/site_features/registration>`__.  Then, you can use
justopinion to create a :class:`~justopinion.download.CAPClient` object
that will hold your API key and automate some of the steps of downloading.

Your API key should remain secret like a password. It's important not to include
your API key in the Python code you write, because you might accidentally post
it somewhere on the web where other people can see it, like on GitHub.

Your API Key
~~~~~~~~~~~~

A safer way to handle your API key is to use `python-dotenv <https://pypi.org/project/python-dotenv/>`__.
To use python-dotenv, add a file in the root directory of your project called `.env`.
Also add `.env` to your `.gitignore` file. The
`.env` file should contain a line that looks like `CAP_API_KEY=your-api-key-here`.
Then within your Python code, you can import a variable called `CAP_API_KEY`
that will hold your API key.

    >>> import os
    >>> from dotenv import load_dotenv
    >>> load_dotenv()
    True
    >>> CAP_API_KEY = os.getenv('CAP_API_KEY')

Next, use the `CAP_API_KEY` variable to create a :class:`~justopinion.download.CAPClient`.

    >>> from justopinion.download import CAPClient
    >>> client = CAPClient(CAP_API_KEY)

Fetching a Case
~~~~~~~~~~~~~~~~

Let’s download Oracle America v. Google, 750 F.3d 1339 (2014), a case that
appears in the :ref:`AuthoritySpoke tutorial <authorityspoke:introduction>`.

    >>> from justopinion import CAPClient
    >>> client = CAPClient(api_token=CAP_API_KEY)
    >>> oracle_download = client.fetch(cite="750 F.3d 1339")

By looking at a field from the API response, we can verify that this is the correct case name.

    >>> oracle_download["name"]
    'ORACLE AMERICA, INC., Plaintiff-Appellant, v. GOOGLE INC., Defendant-Cross-Appellant'

But we haven't loaded the case as a :class:`~justopinion.decisions.Decision` yet. Instead
it's just a Python :py:class:`dict`. To load the case as a :class:`~justopinion.decisions.Decision`,
we can use the :meth:`~justopinion.download.CAPClient.read_decision_from_response` method.

    >>> oracle = self.client.read_decision_from_response(oracle_download)
    >>> oracle.name_abbreviation
    "Oracle America, Inc. v. Google Inc."
    >>> oracle.id
    4066790
    >>> oracle.decision_date.isoformat()
    "2014-05-09"

Although the :class:`~justopinion.decisions.Decision` object has attributes with information
about the case, it doesn't have fields about the :class:`~justopinion.decisions.Opinion`\s
filed in the case. To get the :class:`~justopinion.decisions.Opinion`\s, we can set the
``full_case`` parameter to ``True``.

The CAP API `generally limits users to downloading 500 full cases per day <https://case.law/docs/policies/access_limits>`__. If you
accidentally make a query that returns hundreds of full cases, you could
hit your limit before you know it. You should first try out your API
queries without the ``full_case=True`` parameter, and then only
request full cases once you’re confident you’ll receive what you expect.

Using the ``full_case`` parameter allows us to access information extracted from the
text of the opinions, including the party names, on the ``casebody`` attribute.

    >>> thornton = client.read_cite("1 Breese 34", full_case=True)
    >>> thornton.casebody.data.parties[0]
    "John Thornton and others, Appellants, v. George Smiley and John Bradshaw, Appellees."

The ``full_case`` parameter also allows access to the ``opinions`` attribute.

    >>> thornton.opinions[0].type
    "majority"

The :meth:`~justopinion.decisions.Opinion.locate_text` method can be used to find the
start and endpoints of a phrase in the text of an opinion.

    >>> thornton.opinions[0].locate_text("The court knows of no power in the administrator")
    (23, 71)

The :meth:`~justopinion.decisions.Opinion.select_text` method goes in the opposite direction,
getting a text quotation from start and end positions.

    >>> selection = thornton.opinions.select_text([(259, 295), (313, 360)]))
    >>> str(selection)
    "…The note was made to West alone, and…the suit should have been commenced in his name…"
