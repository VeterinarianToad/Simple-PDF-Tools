# Simple PDF Merger
A simple script to combine multiple PDF files into a single file using Python.

## Features
- Merges multiple PDFs.
- Command-line interface (CLI) usage.
- Lightweight and fast.

## Requirements
- Python 3.7+
- PyPDF2

## Installation
```bash
pip install PyPDF2
```

## Usage
```bash
python merge.py mergedPdf.pdf pdfIn1.pdf pdfIn2.pdf ...
```

## How it Works
The script uses PdfReader and PdfWriter from the PyPDF2 library to iterate through the pages of each input file and append them into a single output document.

## Structure
```
pdf-merger/
├── merge.py
├── README.md
└── LICENSE
```

## License
MIT
