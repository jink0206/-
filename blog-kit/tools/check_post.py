#!/usr/bin/env python3
"""발행 전 점검. ERROR는 반드시 해결, WARN은 확인.

사용법: python3 tools/check_post.py posts/2026-11-16-01-travel.md
"""
import re
import sys
import pathlib
from collections import Counter

MIN_CHARS = {"travel": 1500, "restaurant": 1200, "info": 1800, "review": 1500}
MIN_PHOTOS = {"travel": 8, "restaurant": 6, "info": 3, "review": 6}
AI_FILLER = ["다양한", "알아보겠습니다", "살펴보겠습니다", "마무리하겠습니다",
             "도움이 되셨기를", "결론적으로", "이처럼", "뿐만 아니라"]
HYPE = ["무조건", "100%", "최고의", "역대급", "완벽한", "반드시 사세요"]


def parse(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def main(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    meta, body = parse(text)
    errors, warns = [], []

    cat = meta.get("category", "")
    title = meta.get("title", "")
    kw = meta.get("keyword", "")

    if cat not in MIN_CHARS:
        errors.append(f"category 값이 올바르지 않음: '{cat}'")
        cat = "info"
    if not (15 <= len(title) <= 40):
        warns.append(f"제목 길이 {len(title)}자 (권장 15~40자)")
    if kw and kw.replace(" ", "") not in title.replace(" ", ""):
        warns.append("제목에 핵심 키워드가 그대로 들어있지 않음")

    left = re.findall(r"\[\[.*?\]\]", body, re.S)
    if left:
        errors.append(f"직접 채워야 할 [[ ]] 항목 {len(left)}개 남음 (첫 항목: {left[0][:30]}…)")

    chars = len(re.sub(r"\s", "", re.sub(r"\[\[.*?\]\]|\[사진:.*?\]", "", body, flags=re.S)))
    if chars < MIN_CHARS[cat]:
        warns.append(f"본문 {chars}자 (이 카테고리 권장 {MIN_CHARS[cat]}자 이상)")

    photos = len(re.findall(r"\[사진:", body))
    if photos < MIN_PHOTOS[cat]:
        warns.append(f"사진 자리 {photos}개 (권장 {MIN_PHOTOS[cat]}개 이상, 직접 찍은 사진 사용)")

    sponsored = meta.get("sponsored", "false").lower() == "true"
    head = body[:600]
    if sponsored and not re.search(r"광고|협찬|제공받", head):
        errors.append("sponsored: true 인데 상단에 광고/협찬 표기가 없음")
    plain = re.sub(r"\[\[.*?\]\]", "", body, flags=re.S)
    if not sponsored and re.search(r"제공받아|협찬|원고료|광고를 포함", plain):
        warns.append("협찬 문구가 있는데 sponsored: false 로 되어 있음")

    if cat == "review" and not re.search(r"단점|아쉬운", body):
        errors.append("리뷰에 단점/아쉬운 점 섹션이 없음")
    if cat == "info" and "기준일" not in body:
        errors.append("정보글에 기준일/출처 표기가 없음")

    for h in HYPE:
        if h in body:
            warns.append(f"과장 표현 '{h}' 사용 — 근거 없으면 삭제")

    fill = {w: body.count(w) for w in AI_FILLER if body.count(w) >= 2}
    if fill:
        warns.append(f"AI스러운 상투어 반복: {fill} — 내 말투로 고치기")

    lines = [l.strip() for l in body.splitlines() if len(l.strip()) > 15]
    dup = [l for l, c in Counter(lines).items() if c > 1]
    if dup:
        warns.append(f"중복 문장 {len(dup)}개 (예: {dup[0][:25]}…)")

    print(f"== {path}  (본문 {chars}자, 사진 {photos}개)")
    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN ", w)
    if not errors and not warns:
        print("OK 발행 전 점검 통과")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
