import setuptools

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="justopinion",
    version="0.2.4",
    author="Matt Carey",
    author_email="matt@authorityspoke.com",
    description="Download client for legal opinions",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/mscarey/justopinion",
    project_urls={"Bug Tracker": "https://github.com/mscarey/justopinion/issues"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: Free To Use But Restricted",
        "Natural Language :: English",
    ],
    packages=setuptools.find_packages(exclude=["tests"]),
    install_requires=["requests", "anchorpoint>=0.5.3", "eyecite>=2.2.0", "pydantic"],
    python_requires=">=3.8",
)
