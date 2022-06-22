Changelog
=========

0.3.0 (2022-06-22)
------------------
* support Python 3.10

0.2.5 (2021-10-09)
------------------
* bump anchorpoint version to 0.7.0
* add python-ranges as dependency

0.2.4 (2021-08-12)
------------------
* switch from setup.cfg to setup.py
* bump anchorpoint version to 0.5.3

0.2.3 (2021-08-11)
------------------
* add install_requires to setup.cfg

0.2.2 (2021-08-10)
------------------
* add exception for wrong API key
* change package detection in setup.cfg

0.2.1 (2021-08-09)
------------------
* add default value for CaseBody.status
* add Decision.find_matching_opinion
* fix links in setup.cfg

0.2.0 (2021-08-04)
------------------
* add validator for opinion author
* read_decision_from_response works with single result
* add locate_text and select_text methods
* bump anchorpoint version
* change class names from CAPOpinion and CAPDecision to Opinion and Decision
* make separate citations module

0.1.1 (2021-07-16)
------------------
* add fields from Case Access Project API data model
* add functionality to citations from Eyecite library
* use Pydantic for data validation