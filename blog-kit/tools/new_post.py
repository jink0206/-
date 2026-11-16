#!/usr/bin/env python3
"""카테고리 템플릿으로 초안 파일을 만든다.

사용법:
  python3 tools/new_post.py travel "제주 동쪽 당일치기 코스" --keyword "제주 동쪽 여행"
"""
import argparse
import datetime
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATEGORIES = ("travel", "restaurant", "info", "review")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("category", choices=CATEGORIES)
    p.add_argument("title")
    p.add_argument("--keyword", help="핵심 검색 키워드 (기본: 제목)")
    a = p.parse_args()

    tpl = (ROOT / "templates" / f"{a.category}.md").read_text(encoding="utf-8")
    body = tpl.replace("{title}", a.title).replace("{keyword}", a.keyword or a.title)

    today = datetime.date.today().isoformat()
    n = len(list((ROOT / "posts").glob(f"{today}-*.md"))) + 1
    out = ROOT / "posts" / f"{today}-{n:02d}-{a.category}.md"
    out.write_text(body, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
