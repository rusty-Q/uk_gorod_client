from setuptools import setup, find_packages

setup(
    name="uk-gorod",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
    ],
    author="rusty-Q",
    author_email="rustam2701@yandex.ru",
    description="Библиотека для работы с порталом УК Город",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="uk gorod utility meters readings automation",
    python_requires=">=3.6",
)
