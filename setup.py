from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lazyi18n",
    version="0.1.0",
    author="Tade Strehk",
    description="A TUI for managing i18next translation files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Strehk/lazyi18n",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    py_modules=["main"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.12",
    install_requires=[
        "linkify-it-py>=2.0.3",
        "markdown-it-py>=4.0.0",
        "mdit-py-plugins>=0.5.0",
        "mdurl>=0.1.2",
        "platformdirs>=4.5.1",
        "Pygments>=2.19.2",
        "rich>=14.2.0",
        "textual>=6.10.0",
        "typing_extensions>=4.15.0",
    ],
    entry_points={
        "console_scripts": [
            "lazyi18n=main:main",
        ],
    },
)
