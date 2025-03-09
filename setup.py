from setuptools import setup, find_packages

setup(
    name="ai_comics_generate",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pytest",
        "pytest-asyncio",
        "pydantic-settings"
    ],
) 