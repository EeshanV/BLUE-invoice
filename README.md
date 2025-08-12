# BLUE-Invoice-Extractor

A Python package to extract structured purchase order and invoice data from PDF files.

## Installation

```bash
pip install git+https://github.com/EeshanV/blue_invoice.git
```

## Usage

```python
from blue_invoice import parse_and_stream_pos

parse_and_stream_pos("example.pdf", "output.json")
```
