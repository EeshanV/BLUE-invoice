from setuptools import setup, find_packages

setup(
    name="blue_invoice",
    version="0.1.0",
    description="Extract structured invoice and PO data from PDFs",
    author="Eeshan V",
    packages=find_packages(),
    install_requires=[
        "pdfplumber"
    ],
    python_requires=">=3.8",
)
