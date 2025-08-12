# BLUE-Invoice-extractor

A Python package to extract structured purchase order and invoice data from PDF files.

## Installation

```bash
pip install git+https://github.com/EeshanV/BLUE-invoice.git
```

## Usage

```python
from invoice_format_extractor import parse_and_stream_pos

parse_and_stream_pos("example.pdf", "output.json")
```
