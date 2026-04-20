# PDF Tool

A command-line utility to manipulate PDF files using Python.

## Features

- **Merge** — combine multiple PDFs into one
- **Optimize** — reduce file size by compressing content streams
- **Cut** — keep only selected pages
- **Rotate** — rotate pages 90°, 180°, or 270°
- **Reorder** — rearrange pages in any order
- **Split** — extract pages into separate files (one per page or in blocks)
- **Encrypt / Decrypt** — add or remove password protection
- **Number** — stamp page numbers with configurable position and format
- **Compress Images** — recompress embedded images as JPEG with optional downsampling
- **Metadata** — edit title, author, subject, and other document properties

## Requirements

- Python 3.7+
- pypdf
- reportlab
- pikepdf
- pillow

## Installation

```bash
pip install pypdf reportlab pikepdf pillow
```

## Usage

```bash
python pdf_tool.py <command> [arguments] [options]
```

### Merge

Combine multiple PDFs into a single file.

```bash
python pdf_tool.py merge output.pdf file1.pdf file2.pdf ...
```

### Optimize

Reduce file size by compressing content streams and deduplicating identical objects.

```bash
python pdf_tool.py optimize input.pdf output.pdf
```

### Cut

Keep only the specified pages and discard the rest.

```bash
python pdf_tool.py cut input.pdf output.pdf "1,2,5-7"
```

### Rotate

Rotate all pages or a specific selection by 90°, 180°, or 270°.

```bash
python pdf_tool.py rotate input.pdf output.pdf <90|180|270>
python pdf_tool.py rotate input.pdf output.pdf 90 --pages "1,3-5"
```

### Reorder

Rearrange pages using the same page-range format.

```bash
python pdf_tool.py reorder input.pdf output.pdf "3,1,2,5-7"
```

### Split

Extract pages into separate files. Defaults to one file per page; use `--block N` to group pages.

```bash
python pdf_tool.py split input.pdf output_dir/
python pdf_tool.py split input.pdf output_dir/ --block 3
```

Output files are named after the original file: `input_001.pdf`, `input_002.pdf`, …

### Encrypt / Decrypt

Add or remove password protection.

```bash
python pdf_tool.py encrypt input.pdf output.pdf <password>
python pdf_tool.py decrypt input.pdf output.pdf <password>
```

An optional owner password can be set separately on encrypt:

```bash
python pdf_tool.py encrypt input.pdf output.pdf <user-pwd> --owner-pwd <owner-pwd>
```

### Number

Stamp page numbers onto every page.

```bash
python pdf_tool.py number input.pdf output.pdf
python pdf_tool.py number input.pdf output.pdf --pos bottom-right --start 1
python pdf_tool.py number input.pdf output.pdf --prefix "Pág. " --suffix " / 10"
```

| Option | Default | Description |
|---|---|---|
| `--pos` | `bottom-center` | Position: `top/bottom` + `left/center/right` |
| `--start` | `1` | First page number |
| `--font-size` | `10` | Font size in points |
| `--margin` | `20` | Distance from edge in points |
| `--prefix` | _(empty)_ | Text before the number |
| `--suffix` | _(empty)_ | Text after the number |

### Compress Images

Recompress embedded images as JPEG, with optional downsampling based on DPI. Useful for PDFs with high-resolution scans.

```bash
python pdf_tool.py compress-images input.pdf output.pdf
python pdf_tool.py compress-images input.pdf output.pdf --quality 60 --max-dpi 100
python pdf_tool.py compress-images input.pdf output.pdf --max-dpi 0
```

| Option | Default | Description |
|---|---|---|
| `--quality` | `75` | JPEG quality, 1–95 |
| `--max-dpi` | `150` | Images above this DPI are downsampled before recompression. Use `0` to disable downsampling |

### Metadata

Edit document properties without altering content.

```bash
python pdf_tool.py metadata input.pdf output.pdf --title "My Document" --author "Jane Doe"
```

Available fields: `--title`, `--author`, `--subject`, `--creator`, `--producer`, `--keywords`

## Global Option

Any command can open a password-protected PDF by passing `--password`:

```bash
python pdf_tool.py cut input.pdf output.pdf "1-5" --password mypassword
```

## Page Range Format

Commands that accept page selections use a consistent format:

| Input | Result |
|---|---|
| `"1,3,5"` | Pages 1, 3, and 5 |
| `"2-6"` | Pages 2 through 6 |
| `"1,3,5-8,10"` | Mix of individual pages and ranges |

## Examples by PDF Type

### Scanned document (photos of pages)

The file size is almost entirely images. `optimize` won't help much — use `compress-images` instead.

```bash
# Good balance of quality and size
python pdf_tool.py compress-images scan.pdf output.pdf

# More aggressive — screen reading only
python pdf_tool.py compress-images scan.pdf output.pdf --quality 60 --max-dpi 100

# Maximum reduction: compress images, then deduplicate objects
python pdf_tool.py compress-images scan.pdf tmp.pdf
python pdf_tool.py optimize tmp.pdf output.pdf
```

### Digital PDF (exported from Word, LibreOffice, etc.)

No embedded images, or images already compressed. `optimize` targets streams and duplicate objects.

```bash
python pdf_tool.py optimize doc.pdf output.pdf
```

### Mixed PDF (text + images)

Run both passes. Order matters — compress images first, then deduplicate.

```bash
python pdf_tool.py compress-images mixed.pdf tmp.pdf
python pdf_tool.py optimize tmp.pdf output.pdf
```

### Scanned document with wrong orientation

```bash
# Rotate all pages
python pdf_tool.py rotate scan.pdf output.pdf 90

# Rotate only specific pages
python pdf_tool.py rotate scan.pdf output.pdf 90 --pages "1,3,5"
```

### Split a report and share individual sections

```bash
# One file per page
python pdf_tool.py split report.pdf pages/

# Keep only the relevant pages first
python pdf_tool.py cut report.pdf section.pdf "5-12"
```

### Prepare a document for sharing

```bash
# Add page numbers, set metadata, and protect with a password
python pdf_tool.py number doc.pdf tmp1.pdf --pos bottom-right
python pdf_tool.py metadata tmp1.pdf tmp2.pdf --title "Q3 Report" --author "Acme Corp"
python pdf_tool.py encrypt tmp2.pdf output.pdf secretpassword
```

## Structure

```
pdf-tool/
├── pdf_tool.py
├── README.md
└── LICENSE
```

## License

MIT
