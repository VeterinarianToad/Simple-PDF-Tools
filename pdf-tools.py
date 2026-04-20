"""
pdf_tool.py — Multi-function PDF utility
Requires: pypdf, reportlab, pikepdf, pillow

  pip install pypdf reportlab pikepdf pillow
"""

import io
import os
import sys
from pypdf import PdfReader, PdfWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_reader(path, password=None):
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            if not password:
                print(f"[ERROR] '{path}' is password-protected. Use --password <pwd>")
                sys.exit(1)
            if not reader.decrypt(password):
                print(f"[ERROR] Wrong password for '{path}'")
                sys.exit(1)
        return reader
    except Exception as e:
        print(f"[ERROR] Could not read '{path}': {e}")
        sys.exit(1)


def _save(writer, path):
    with open(path, "wb") as f:
        writer.write(f)


def parse_page_ranges(page_str, total_pages, allow_duplicates=False):
    """
    Parse "1,2,5-7" into a list of 0-indexed page numbers.
    If allow_duplicates=True (reorder), preserves order and repetitions.
    """
    result = []
    seen = set()
    for part in page_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a.strip()), int(b.strip())
            if a < 1 or b > total_pages or a > b:
                raise ValueError(f"Invalid range '{part}' for a {total_pages}-page PDF.")
            for p in range(a, b + 1):
                if allow_duplicates or p - 1 not in seen:
                    result.append(p - 1)
                    seen.add(p - 1)
        else:
            p = int(part)
            if p < 1 or p > total_pages:
                raise ValueError(f"Page {p} out of range (PDF has {total_pages} pages).")
            if allow_duplicates or p - 1 not in seen:
                result.append(p - 1)
                seen.add(p - 1)
    return result


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def merge_pdfs(files, out, password=None):
    """Merge multiple PDFs into one output file."""
    writer = PdfWriter()
    total = 0
    for file in files:
        reader = _open_reader(file, password)
        for page in reader.pages:
            writer.add_page(page)
            total += 1
    _save(writer, out)
    print(f"[OK] Merged {len(files)} file(s), {total} pages → '{out}'")


def _fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} GB"


def optimize_pdf(file_in, file_out, password=None):
    """Reduce PDF size by compressing content streams and deduplicating objects."""
    size_in = os.path.getsize(file_in)
    reader  = _open_reader(file_in, password)
    writer  = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    for page in writer.pages:
        page.compress_content_streams()
    try:
        writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
    except TypeError:
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    _save(writer, file_out)

    size_out    = os.path.getsize(file_out)
    total_saved = size_in - size_out
    pct         = (total_saved / size_in * 100) if size_in else 0

    print(f"[OK] Optimized '{file_in}' → '{file_out}'")
    print(f"     Before : {_fmt_bytes(size_in):>12}")
    print(f"     After  : {_fmt_bytes(size_out):>12}")
    print(f"     Saved  : {_fmt_bytes(total_saved):>12}  ({pct:.1f}%)")


def cut_pdf(file_in, page_str, file_out, password=None):
    """Keep only the specified pages."""
    reader = _open_reader(file_in, password)
    total  = len(reader.pages)
    try:
        indices = parse_page_ranges(page_str, total)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    writer = PdfWriter()
    for i in indices:
        writer.add_page(reader.pages[i])
    _save(writer, file_out)
    kept = [i + 1 for i in indices]
    print(f"[OK] Cut '{file_in}' → '{file_out}'")
    print(f"     Kept {len(kept)} of {total} pages: {kept}")


def rotate_pdf(file_in, angle, file_out, page_str=None, password=None):
    """
    Rotate pages by angle (90, 180, 270).
    If page_str is given, only those pages are rotated; otherwise all pages.
    """
    if angle not in (90, 180, 270):
        print("[ERROR] Angle must be 90, 180, or 270.")
        sys.exit(1)
    reader = _open_reader(file_in, password)
    total  = len(reader.pages)
    if page_str:
        try:
            targets = set(parse_page_ranges(page_str, total))
        except ValueError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        targets = set(range(total))

    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i in targets:
            page.rotate(angle)
        writer.add_page(page)
    _save(writer, file_out)
    rotated = sorted(t + 1 for t in targets)
    print(f"[OK] Rotated {angle}° pages {rotated} in '{file_in}' → '{file_out}'")


def reorder_pdf(file_in, page_str, file_out, password=None):
    """
    Reorder pages. page_str defines the new order (e.g. "3,1,2").
    Every page in the document must appear at least once.
    """
    reader = _open_reader(file_in, password)
    total  = len(reader.pages)
    try:
        indices = parse_page_ranges(page_str, total, allow_duplicates=True)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    writer = PdfWriter()
    for i in indices:
        writer.add_page(reader.pages[i])
    _save(writer, file_out)
    print(f"[OK] Reordered '{file_in}' → '{file_out}'")
    print(f"     New order: {[i + 1 for i in indices]}")


def split_pdf(file_in, out_dir, block=1, password=None):
    """
    Split a PDF into separate files.
    block=1 → one file per page.
    block=N → groups of N pages.
    Output files are named <out_dir>/<stem>_001.pdf, _002.pdf, …
    """
    reader = _open_reader(file_in, password)
    total  = len(reader.pages)
    stem   = os.path.splitext(os.path.basename(file_in))[0]
    os.makedirs(out_dir, exist_ok=True)

    chunk_num = 1
    i = 0
    files_created = []
    while i < total:
        writer = PdfWriter()
        chunk  = reader.pages[i : i + block]
        for page in chunk:
            writer.add_page(page)
        name = os.path.join(out_dir, f"{stem}_{chunk_num:03d}.pdf")
        _save(writer, name)
        files_created.append(name)
        i += block
        chunk_num += 1

    print(f"[OK] Split '{file_in}' into {len(files_created)} file(s) in '{out_dir}/'")
    for f in files_created:
        print(f"     {f}")


def encrypt_pdf(file_in, file_out, user_pwd, owner_pwd=None):
    """Encrypt a PDF with a user password (and optionally an owner password)."""
    reader = _open_reader(file_in)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_pwd, owner_pwd or user_pwd)
    _save(writer, file_out)
    print(f"[OK] Encrypted '{file_in}' → '{file_out}'")


def decrypt_pdf(file_in, file_out, password):
    """Remove password protection from a PDF."""
    reader = _open_reader(file_in, password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    _save(writer, file_out)
    print(f"[OK] Decrypted '{file_in}' → '{file_out}'")


def add_page_numbers(file_in, file_out, password=None,
                     position="bottom-center", start=1, font_size=10,
                     margin=20, prefix="", suffix=""):
    """
    Stamp page numbers onto every page using reportlab.
    position: bottom-center | bottom-left | bottom-right
              top-center    | top-left    | top-right
    """
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter
        import io
        from pypdf import PageObject
    except ImportError:
        print("[ERROR] reportlab is required: pip install reportlab")
        sys.exit(1)

    reader = _open_reader(file_in, password)
    writer = PdfWriter()

    for idx, page in enumerate(reader.pages):
        # Page dimensions
        box    = page.mediabox
        pw     = float(box.width)
        ph     = float(box.height)

        # Build a transparent overlay with the page number
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(pw, ph))
        c.setFont("Helvetica", font_size)

        label = f"{prefix}{start + idx}{suffix}"

        pos = position.lower()
        if "bottom" in pos:
            y = margin
        else:
            y = ph - margin - font_size

        if "left" in pos:
            c.drawString(margin, y, label)
        elif "right" in pos:
            c.drawRightString(pw - margin, y, label)
        else:  # center
            c.drawCentredString(pw / 2, y, label)

        c.save()
        packet.seek(0)

        # Merge overlay onto the page
        overlay_reader = PdfReader(packet)
        overlay_page   = overlay_reader.pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    _save(writer, file_out)
    print(f"[OK] Added page numbers to '{file_in}' → '{file_out}'")
    print(f"     Pages {start}–{start + len(reader.pages) - 1}  |  position: {position}")


def edit_metadata(file_in, file_out, password=None, **kwargs):
    """
    Edit PDF metadata. Accepted kwargs:
      title, author, subject, creator, producer, keywords
    """
    from datetime import datetime, timezone
    reader = _open_reader(file_in, password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Copy existing metadata then overwrite supplied fields
    existing = reader.metadata or {}
    meta = {
        "/Title":    kwargs.get("title",    existing.get("/Title",    "")),
        "/Author":   kwargs.get("author",   existing.get("/Author",   "")),
        "/Subject":  kwargs.get("subject",  existing.get("/Subject",  "")),
        "/Creator":  kwargs.get("creator",  existing.get("/Creator",  "")),
        "/Producer": kwargs.get("producer", existing.get("/Producer", "")),
        "/Keywords": kwargs.get("keywords", existing.get("/Keywords", "")),
    }
    # Remove empty keys
    meta = {k: v for k, v in meta.items() if v}
    writer.add_metadata(meta)
    _save(writer, file_out)

    print(f"[OK] Metadata updated '{file_in}' → '{file_out}'")
    for k, v in meta.items():
        print(f"     {k[1:]:<10} {v}")


def compress_images(file_in, file_out, quality=75, max_dpi=150, password=None):
    """
    Recompress embedded images as JPEG with optional downsampling.

    quality  : JPEG quality 1-95 (default 75).
    max_dpi  : Images whose estimated DPI exceeds this value are downsampled
               before recompression (default 150).
               Use 0 to skip downsampling and only recompress.
    """
    try:
        import pikepdf
        from pikepdf import PdfImage
    except ImportError:
        print("[ERROR] pikepdf is required: pip install pikepdf")
        sys.exit(1)

    try:
        from PIL import Image
    except ImportError:
        print("[ERROR] Pillow is required: pip install pillow")
        sys.exit(1)

    open_kwargs = {"password": password} if password else {}
    try:
        pdf = pikepdf.open(file_in, **open_kwargs)
    except Exception as e:
        print(f"[ERROR] Could not open '{file_in}': {e}")
        sys.exit(1)

    total_imgs  = 0
    downsampled = 0

    with pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            for name, img_obj in page.images.items():
                try:
                    pil = PdfImage(img_obj).as_pil_image()
                except Exception as e:
                    print(f"  [SKIP] page {page_num} {name}: {e}")
                    continue

                orig_w, orig_h = pil.size
                total_imgs += 1

                # Estimate DPI relative to the page dimensions
                if max_dpi > 0:
                    page_w_in = float(page.mediabox[2]) / 72
                    page_h_in = float(page.mediabox[3]) / 72
                    est_dpi   = max(orig_w / max(page_w_in, 0.01),
                                   orig_h / max(page_h_in, 0.01))
                    if est_dpi > max_dpi:
                        scale  = max_dpi / est_dpi
                        new_w  = max(1, int(orig_w * scale))
                        new_h  = max(1, int(orig_h * scale))
                        pil    = pil.resize((new_w, new_h), Image.LANCZOS)
                        downsampled += 1
                        print(f"  page {page_num} {name}: "
                              f"{orig_w}x{orig_h} → {new_w}x{new_h} "
                              f"(~{est_dpi:.0f} → {max_dpi} DPI)")
                    else:
                        print(f"  page {page_num} {name}: "
                              f"{orig_w}x{orig_h}, ~{est_dpi:.0f} DPI — recompressing only")
                else:
                    print(f"  page {page_num} {name}: {orig_w}x{orig_h} — recompressing only")

                # Re-encode as JPEG and replace stream in-place
                buf = io.BytesIO()
                pil.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)

                img_obj.write(buf.getvalue(), filter=pikepdf.Name("/DCTDecode"))
                img_obj.stream_dict["/Width"]             = pil.width
                img_obj.stream_dict["/Height"]            = pil.height
                img_obj.stream_dict["/ColorSpace"]        = pikepdf.Name("/DeviceRGB")
                img_obj.stream_dict["/BitsPerComponent"]  = 8

        pdf.save(file_out)

    size_in  = os.path.getsize(file_in)
    size_out = os.path.getsize(file_out)
    saved    = size_in - size_out
    pct      = (saved / size_in * 100) if size_in else 0

    print(f"[OK] Compressed images in '{file_in}' → '{file_out}'")
    print(f"     Images found  : {total_imgs}")
    print(f"     Downsampled   : {downsampled}")
    print(f"     Quality       : {quality}")
    print(f"     Max DPI       : {max_dpi if max_dpi > 0 else 'off'}")
    print(f"     Before : {_fmt_bytes(size_in):>12}")
    print(f"     After  : {_fmt_bytes(size_out):>12}")
    print(f"     Saved  : {_fmt_bytes(saved):>12}  ({pct:.1f}%)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

USAGE = """
pdf_tool.py — PDF utility belt
Requires: pip install pypdf reportlab pikepdf pillow

COMMANDS
────────────────────────────────────────────────────────────────────────
  merge      output.pdf file1.pdf file2.pdf ...
  optimize   input.pdf output.pdf
  cut        input.pdf output.pdf "1,2,5-7"
  rotate     input.pdf output.pdf <90|180|270> [--pages "1,3-5"]
  reorder    input.pdf output.pdf "3,1,2,5-7"
  split      input.pdf output_dir/ [--block N]
  encrypt    input.pdf output.pdf <password> [--owner-pwd <pwd>]
  decrypt    input.pdf output.pdf <password>
  number     input.pdf output.pdf [--pos bottom-center] [--start 1]
             [--font-size 10] [--margin 20] [--prefix ""] [--suffix ""]
  compress-images  input.pdf output.pdf [--quality 75] [--max-dpi 150]
  metadata   input.pdf output.pdf [--title X] [--author X]
             [--subject X] [--creator X] [--keywords X]

Global option (any command): --password <pwd>   open a protected PDF

Page format: comma-separated numbers and/or ranges, e.g.  "1,3,5-8,10"
────────────────────────────────────────────────────────────────────────
"""


def _arg(args, flag, default=None):
    """Extract --flag value from args list, returns (value, remaining_args)."""
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            val = args[i + 1]
            rest = args[:i] + args[i + 2:]
            return val, rest
    return default, args


def _flag(args, flag):
    """Check if a boolean --flag is present, returns (bool, remaining_args)."""
    if flag in args:
        return True, [a for a in args if a != flag]
    return False, args


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(USAGE)
        sys.exit(0)

    command = args[0].lower()
    args    = args[1:]

    # Global option
    password, args = _arg(args, "--password")

    # ── merge ───────────────────────────────────────────────────────────────
    if command == "merge":
        if len(args) < 3:
            print("[ERROR] merge: output.pdf file1.pdf file2.pdf ...")
            sys.exit(1)
        merge_pdfs(args[1:], args[0], password)

    # ── optimize ────────────────────────────────────────────────────────────
    elif command == "optimize":
        if len(args) != 2:
            print("[ERROR] optimize: input.pdf output.pdf")
            sys.exit(1)
        optimize_pdf(args[0], args[1], password)

    # ── cut ─────────────────────────────────────────────────────────────────
    elif command == "cut":
        if len(args) != 3:
            print('[ERROR] cut: input.pdf output.pdf "pages"')
            sys.exit(1)
        cut_pdf(args[0], args[2], args[1], password)

    # ── rotate ──────────────────────────────────────────────────────────────
    elif command == "rotate":
        if len(args) < 3:
            print("[ERROR] rotate: input.pdf output.pdf <90|180|270> [--pages ...]")
            sys.exit(1)
        page_str, args = _arg(args, "--pages")
        file_in, file_out, angle_str = args[0], args[1], args[2]
        try:
            angle = int(angle_str)
        except ValueError:
            print("[ERROR] Angle must be an integer: 90, 180, or 270")
            sys.exit(1)
        rotate_pdf(file_in, angle, file_out, page_str, password)

    # ── reorder ─────────────────────────────────────────────────────────────
    elif command == "reorder":
        if len(args) != 3:
            print('[ERROR] reorder: input.pdf output.pdf "order"')
            sys.exit(1)
        reorder_pdf(args[0], args[2], args[1], password)

    # ── split ───────────────────────────────────────────────────────────────
    elif command == "split":
        if len(args) < 2:
            print("[ERROR] split: input.pdf output_dir/ [--block N]")
            sys.exit(1)
        block_str, args = _arg(args, "--block", "1")
        try:
            block = int(block_str)
        except ValueError:
            print("[ERROR] --block must be an integer")
            sys.exit(1)
        split_pdf(args[0], args[1], block, password)

    # ── encrypt ─────────────────────────────────────────────────────────────
    elif command == "encrypt":
        if len(args) < 3:
            print("[ERROR] encrypt: input.pdf output.pdf <password> [--owner-pwd <pwd>]")
            sys.exit(1)
        owner_pwd, args = _arg(args, "--owner-pwd")
        encrypt_pdf(args[0], args[1], args[2], owner_pwd)

    # ── decrypt ─────────────────────────────────────────────────────────────
    elif command == "decrypt":
        if len(args) != 3:
            print("[ERROR] decrypt: input.pdf output.pdf <password>")
            sys.exit(1)
        decrypt_pdf(args[0], args[1], args[2])

    # ── number ──────────────────────────────────────────────────────────────
    elif command == "number":
        if len(args) < 2:
            print("[ERROR] number: input.pdf output.pdf [options]")
            sys.exit(1)
        pos,       args = _arg(args, "--pos",       "bottom-center")
        start_str, args = _arg(args, "--start",     "1")
        fs_str,    args = _arg(args, "--font-size", "10")
        margin_str,args = _arg(args, "--margin",    "20")
        prefix,    args = _arg(args, "--prefix",    "")
        suffix,    args = _arg(args, "--suffix",    "")
        add_page_numbers(
            args[0], args[1], password,
            position=pos,
            start=int(start_str),
            font_size=int(fs_str),
            margin=int(margin_str),
            prefix=prefix,
            suffix=suffix,
        )

    # ── metadata ────────────────────────────────────────────────────────────
    elif command == "metadata":
        if len(args) < 2:
            print("[ERROR] metadata: input.pdf output.pdf [--title X] ...")
            sys.exit(1)
        title,    args = _arg(args, "--title")
        author,   args = _arg(args, "--author")
        subject,  args = _arg(args, "--subject")
        creator,  args = _arg(args, "--creator")
        producer, args = _arg(args, "--producer")
        keywords, args = _arg(args, "--keywords")
        edit_metadata(
            args[0], args[1], password,
            title=title, author=author, subject=subject,
            creator=creator, producer=producer, keywords=keywords,
        )

    # ── compress-images ─────────────────────────────────────────────────────
    elif command == "compress-images":
        if len(args) < 2:
            print("[ERROR] compress-images: input.pdf output.pdf [--quality 75] [--max-dpi 150]")
            sys.exit(1)
        quality_str, args = _arg(args, "--quality", "75")
        max_dpi_str, args = _arg(args, "--max-dpi", "150")
        try:
            quality = int(quality_str)
            max_dpi = int(max_dpi_str)
        except ValueError:
            print("[ERROR] --quality and --max-dpi must be integers")
            sys.exit(1)
        compress_images(args[0], args[1], quality, max_dpi, password)

    else:
        print(f"[ERROR] Unknown command '{command}'")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
