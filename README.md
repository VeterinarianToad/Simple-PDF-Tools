# PDF Tool

A simple command-line utility to manipulate PDF files using Python.

## Features

- **Merge** — combine multiple PDFs into one
- **Optimize** — reduce file size by compressing content streams
- **Cut** — keep only selected pages
- **Rotate** — rotate pages 90°, 180°, or 270°
- **Reorder** — rearrange pages in any order
- **Split** — extract pages into separate files (one per page or in blocks)
- **Encrypt / Decrypt** — add or remove password protection
- **Number** — stamp page numbers with configurable position and format
- **Metadata** — edit title, author, subject, and other document properties

## Requirements

- Python 3.7+
- pypdf
- reportlab

## Installation

```bash
pip install pypdf reportlab
```

## Usage

```bash
python pdf-tools.py <command> [arguments] [options]
```

### Merge

Combine multiple PDFs into a single file.

```bash
python pdf-tools.py merge output.pdf file1.pdf file2.pdf ...
```

### Optimize

Reduce file size by compressing internal content streams.

```bash
python pdf-tools.py optimize input.pdf output.pdf
```

### Cut

Keep only the specified pages and discard the rest.

```bash
python pdf-tools.py cut input.pdf output.pdf "1,2,5-7"
```

### Rotate

Rotate all pages or a specific selection by 90°, 180°, or 270°.

```bash
python pdf-tools.py rotate input.pdf output.pdf <90|180|270>
python pdf-tools.py rotate input.pdf output.pdf 90 --pages "1,3-5"
```

### Reorder

Rearrange pages using the same page-range format.

```bash
python pdf-tools.py reorder input.pdf output.pdf "3,1,2,5-7"
```

### Split

Extract pages into separate files. Defaults to one file per page; use `--block N` to group pages.

```bash
python pdf-tools.py split input.pdf output_dir/
python pdf-tools.py split input.pdf output_dir/ --block 3
```

Output files are named after the original file: `input_001.pdf`, `input_002.pdf`, …

### Encrypt / Decrypt

Add or remove password protection.

```bash
python pdf-tools.py encrypt input.pdf output.pdf <password>
python pdf-tools.py decrypt input.pdf output.pdf <password>
```

An optional owner password can be set separately on encrypt:

```bash
python pdf-tools.py encrypt input.pdf output.pdf <user-pwd> --owner-pwd <owner-pwd>
```

### Number

Stamp page numbers onto every page.

```bash
python pdf-tools.py number input.pdf output.pdf
python pdf-tools.py number input.pdf output.pdf --pos bottom-right --start 1
python pdf-tools.py number input.pdf output.pdf --prefix "Pág. " --suffix " / 10"
```

| Option | Default | Description |
|---|---|---|
| `--pos` | `bottom-center` | Position: `top/bottom` + `left/center/right` |
| `--start` | `1` | First page number |
| `--font-size` | `10` | Font size in points |
| `--margin` | `20` | Distance from edge in points |
| `--prefix` | _(empty)_ | Text before the number |
| `--suffix` | _(empty)_ | Text after the number |

### Metadata

Edit document properties without altering content.

```bash
python pdf-tools.py metadata input.pdf output.pdf --title "My Document" --author "Jane Doe"
```

Available fields: `--title`, `--author`, `--subject`, `--creator`, `--producer`, `--keywords`

## Global Option

Any command can open a password-protected PDF by passing `--password`:

```bash
python pdf-tools.py cut input.pdf output.pdf "1-5" --password mypassword
```

## Page Range Format

Commands that accept page selections use a consistent format:

| Input | Result |
|---|---|
| `"1,3,5"` | Pages 1, 3, and 5 |
| `"2-6"` | Pages 2 through 6 |
| `"1,3,5-8,10"` | Mix of individual pages and ranges |

## Structure

```
pdf-tool/
├── pdf-tools.py
├── README.md
└── LICENSE
```

## License

MIT
