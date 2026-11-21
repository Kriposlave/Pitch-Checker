"""Извлекает текст из .pptx, .docx, .pdf, .txt, .md в UTF-8 файл.

Использование:
    python3 -I extract_text.py <входной файл> <выходной .txt>

Без внешних библиотек для pptx/docx (читает XML внутри архива).
Для pdf пробует pypdf, затем утилиту pdftotext.
Результат всегда пишется в файл в UTF-8, чтобы не было проблем
с кодировкой консоли Windows (cp1251).
"""
import html
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _paragraphs(xml: str, para_tag: str, text_tag: str) -> list[str]:
    paras = re.findall(rf"<{para_tag}[ >].*?</{para_tag}>", xml, re.S)
    out = []
    for p in paras:
        t = "".join(re.findall(rf"<{text_tag}(?: [^>]*)?>(.*?)</{text_tag}>", p, re.S))
        t = html.unescape(t).strip()
        if t:
            out.append(t)
    return out


def _num(name: str) -> int:
    m = re.search(r"(\d+)\.xml$", name)
    return int(m.group(1)) if m else 0


def extract_pptx(path: Path) -> str:
    z = zipfile.ZipFile(path)
    names = z.namelist()
    parts = []
    slides = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)), key=_num)
    for n in slides:
        i = _num(n)
        text = _paragraphs(z.read(n).decode("utf-8"), "a:p", "a:t")
        parts.append(f"=== Слайд {i}\n" + "\n".join(text))
        notes = f"ppt/notesSlides/notesSlide{i}.xml"
        if notes in names:
            nt = [t for t in _paragraphs(z.read(notes).decode("utf-8"), "a:p", "a:t") if not t.isdigit()]
            if nt:
                parts.append(f"[Заметки к слайду {i}]\n" + "\n".join(nt))
    return "\n\n".join(parts)


def extract_docx(path: Path) -> str:
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8")
    return "\n".join(_paragraphs(xml, "w:p", "w:t"))


def extract_pdf(path: Path) -> str:
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(path))
        return "\n\n".join(f"=== Страница {i}\n{p.extract_text() or ''}" for i, p in enumerate(reader.pages, 1))
    except ImportError:
        pass
    exe = shutil.which("pdftotext")
    if exe:
        # pdftotext не открывает пути длиннее 260 символов (Windows MAX_PATH),
        # поэтому сначала копируем файл во временную папку с коротким именем.
        with tempfile.TemporaryDirectory() as tmp:
            short = Path(tmp) / "in.pdf"
            shutil.copyfile(path, short)
            res = subprocess.run([exe, "-enc", "UTF-8", "-layout", str(short), "-"], capture_output=True)
        if res.returncode == 0:
            return res.stdout.decode("utf-8", errors="replace")
        raise RuntimeError("pdftotext завершился с ошибкой: " + res.stderr.decode("utf-8", "replace"))
    raise RuntimeError("Нет pypdf и нет pdftotext: используйте skill pdf для извлечения текста.")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not src.exists():
        sys.exit(f"ОШИБКА: файл не найден: {src}\nПроверьте путь (возьмите его в кавычки целиком, без сокращений).")
    ext = src.suffix.lower()
    try:
        if ext == ".pptx":
            text = extract_pptx(src)
        elif ext == ".docx":
            text = extract_docx(src)
        elif ext == ".pdf":
            text = extract_pdf(src)
        elif ext in (".txt", ".md"):
            text = src.read_text(encoding="utf-8")
        else:
            sys.exit(f"Неподдерживаемый формат: {ext}")
    except Exception as e:  # понятное сообщение вместо трассировки
        sys.exit(f"ОШИБКА при извлечении текста из {src.name}: {e}")
    dst.write_text(text, encoding="utf-8")
    words = len(re.findall(r"\w+", text))
    print(f"OK: {dst} ({len(text)} символов, ~{words} слов)")
    if words < 20:
        print("ВНИМАНИЕ: текста почти нет. Возможно, это скан или картинки — нужен OCR (skill pdf).")


if __name__ == "__main__":
    main()
