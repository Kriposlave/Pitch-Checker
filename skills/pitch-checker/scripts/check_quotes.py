"""Сверяет цитаты из отчёта с текстом работы.

Использование:
    python3 -I check_quotes.py <текст работы .txt> <отчёт .md> [<выход .txt>]

Берёт из отчёта все цитаты в «ёлочках» и ищет каждую в тексте работы.
Сравнение терпимо к регистру, ё/е, лишним пробелам, видам кавычек и тире.
Многоточие («…» или «...») делит цитату на части; каждая часть ищется
по порядку.

Итог:
  НАЙДЕНО      — цитата есть в работе.
  НЕ НАЙДЕНО   — цитаты нет в работе. Это допустимо ТОЛЬКО если это цитата
                 из внешнего источника (тогда её надо сверить с источником).
                 Если это цитата из работы студента — ошибка, исправить отчёт.
Результат пишется в UTF-8 файл (по умолчанию <отчёт>.quotes.txt).
"""
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    s = s.lower().replace("ё", "е").replace("­", "")  # мягкие переносы (архивные копии БРЭ)
    s = re.sub(r"[«»„“”\"'`]", "", s)
    s = re.sub(r"[‐-―−]", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,;:!?")


def extract_quotes(report: str) -> list[str]:
    # «...» с учётом вложенных кавычек вида «текст «Название» текст»
    quotes, depth, buf = [], 0, []
    for ch in report:
        if ch == "«":
            if depth > 0:
                buf.append(ch)
            depth += 1
        elif ch == "»" and depth > 0:
            depth -= 1
            if depth == 0:
                quotes.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        elif depth > 0:
            buf.append(ch)
    seen, out = set(), []
    for q in quotes:
        q = q.strip()
        if len(re.findall(r"\w+", q)) >= 3 and q not in seen:  # пропускаем короткие названия
            seen.add(q)
            out.append(q)
    return out


def found(quote: str, text: str) -> bool:
    parts = [norm(p) for p in re.split(r"…|\.\.\.", quote)]
    parts = [p for p in parts if p]
    pos = 0
    for p in parts:
        i = text.find(p, pos)
        if i < 0:
            return False
        pos = i + len(p)
    return True


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    work = norm(Path(sys.argv[1]).read_text(encoding="utf-8"))
    report_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) == 4 else report_path.with_suffix(".quotes.txt")
    quotes = extract_quotes(report_path.read_text(encoding="utf-8"))
    ok = [q for q in quotes if found(q, work)]
    miss = [q for q in quotes if not found(q, work)]
    lines = [f"Цитат в отчёте: {len(quotes)}. Найдено в работе: {len(ok)}. Не найдено: {len(miss)}.", ""]
    lines += ["НЕ НАЙДЕНО в работе (должны быть цитатами из внешних источников — проверить каждую):"]
    lines += [f"  - «{q}»" for q in miss] or ["  (нет)"]
    lines += ["", "НАЙДЕНО в работе:"]
    lines += [f"  - «{q}»" for q in ok] or ["  (нет)"]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Цитат: {len(quotes)}, найдено в работе: {len(ok)}, не найдено: {len(miss)}. Подробно: {out_path}")


if __name__ == "__main__":
    main()
