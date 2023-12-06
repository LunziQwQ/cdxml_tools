from setuptools import setup, find_packages

setup(
    name="cdxml_tools",
    version="0.1.0",
    author="KylinJiang",
    author_email="me@lunzi.space",
    description="CDXML Tools",
    packages=find_packages(),
    install_requires=[
        "Pillow",
        "wind",
    ]
)
