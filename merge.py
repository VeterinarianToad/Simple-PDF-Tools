import sys
from PyPDF2 import PdfReader, PdfWriter

def merge_pdfs(files, out):
    writer = PdfWriter()

    for file in files:
        try:
            reader = PdfReader(file)
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            print(f"[ERROR] Failed to read file {file}: {e}")

    with open(out, "wb") as f:
        writer.write(f)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Missing arguments. Command example: python merge.py mergedPdf.pdf pdfIn1.pdf pdfIn2.pdf ...")
        sys.exit(1)

    out = sys.argv[1]
    input = sys.argv[2:]

    merge_pdfs(input, out)
    print(f"[OK] PDF merged: {out}")