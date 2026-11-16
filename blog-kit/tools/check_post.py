#!/usr/bin/env python3
"""발행 전 점검. ERROR는 반드시 해결, WARN은 확인.

사용법: python3 tools/check_post.py posts/2026-11-16-01-travel.md
"""
import re
import sys
import pathlib
from collections import Counter

MIN_CHARS = {"travel": 1500, "restaurant": 1200, "info": 1800, "review": 1500, "issue": 1800}
MIN_PHOTOS = {"travel": 7, "restaurant": 6, "info": 3, "review": 6, "issue": 5}
NEEDS_SOURCE = ("info", "issue")        # 사실 정보 → 출처·기준일 필수
EXPERIENCE = ("travel", "restaurant", "review")  # 경험 글 → 직접 겪은 느낌 필요

PHOTO = re.compile(r"\[사진[^\]]*\]|📷\s*사진\s*\d+")
HEDGE = re.compile(r"것 같|보여요|보입니다|알려진|후기가 있|이야기가 자주|로 보이|듯해요|듯합니다")
HASHTAG = re.compile(r"(?<!\S)#[^\s#]+")
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
    if not (15 <= len(title) <= 45):
        warns.append(f"제목 길이 {len(title)}자 (권장 15~45자)")
    if kw and kw.replace(" ", "") not in title.replace(" ", ""):
        warns.append("제목에 핵심 키워드가 그대로 들어있지 않음")
    heads = re.findall(r"^##\s.*$", body, re.M)
    if kw and heads and not any(kw.replace(" ", "") in h.replace(" ", "") for h in heads):
        warns.append("소제목(##)에 핵심 키워드가 한 번도 없음")

    left = re.findall(r"\[\[.*?\]\]", body, re.S)
    if left:
        errors.append(f"직접 채워야 할 [[ ]] 항목 {len(left)}개 남음 (첫 항목: {left[0][:30]}…)")
    plain = re.sub(r"\[\[.*?\]\]", "", body, flags=re.S)

    chars = len(re.sub(r"\s", "", PHOTO.sub("", plain)))
    if chars < MIN_CHARS[cat]:
        warns.append(f"본문 {chars}자 (이 카테고리 권장 {MIN_CHARS[cat]}자 이상)")

    photos = len(PHOTO.findall(plain)) + len(PHOTO.findall("".join(left)))
    if photos < MIN_PHOTOS[cat]:
        warns.append(f"사진 자리 {photos}개 (권장 {MIN_PHOTOS[cat]}개 이상, 직접 찍은/출처 있는 사진 사용)")

    sponsored = meta.get("sponsored", "false").lower() == "true"
    if sponsored and not re.search(r"광고|협찬|제공받", body[:600]):
        errors.append("sponsored: true 인데 상단에 광고/협찬 표기가 없음")
    if not sponsored and re.search(r"제공받아|협찬|원고료|광고를 포함", plain):
        warns.append("협찬 문구가 있는데 sponsored: false 로 되어 있음")

    if cat == "review" and not re.search(r"단점|아쉬운", plain):
        errors.append("리뷰에 단점/아쉬운 점 섹션이 없음")
    if cat in NEEDS_SOURCE:
        if "기준일" not in plain:
            errors.append("기준일 표기가 없음 (사실 정보 글은 '○○ 기준' 필수)")
        if not re.search(r"출처|공식", plain):
            warns.append("출처/공식 채널 언급이 없음")
    if cat in ("travel", "restaurant") and not re.search(r"영업시간|운영시간|운영 시간", plain):
        warns.append("영업/운영시간 정보가 없음 (검색 의도 1순위)")
    if cat in ("travel", "restaurant", "review") and not re.search(r"\d[\d,]*\s*원|무료", plain):
        warns.append("가격/요금 정보가 없음 (무료면 '무료'라고 명시)")

    if cat in EXPERIENCE:
        n = len(HEDGE.findall(plain))
        if n >= 6:
            warns.append(f"추측·전언 표현 {n}회('것 같아요','보여요','알려진' 등) — 직접 겪은 사실로 바꾸거나, "
                         "직접 가지 않았다면 후기가 아니라 정보글로 표기")

    for h in HYPE:
        if h in plain:
            warns.append(f"과장 표현 '{h}' 사용 — 근거 없으면 삭제")

    fill = {w: plain.count(w) for w in AI_FILLER if plain.count(w) >= 2}
    if fill:
        warns.append(f"AI스러운 상투어 반복: {fill} — 내 말투로 고치기")
    habit = {w: len(re.findall(w, plain)) for w in ("잖아요", "ㅎㅎ|ㅋㅋ")}
    habit = {k: v for k, v in habit.items() if v >= 6}
    if habit:
        warns.append(f"말버릇 과다: {habit} — 글마다 똑같은 틀로 보이지 않게 줄이기")

    lines = [l.strip() for l in plain.splitlines() if len(l.strip()) > 15]
    dup = [l for l, c in Counter(lines).items() if c > 1]
    if dup:
        warns.append(f"중복 문장 {len(dup)}개 (예: {dup[0][:25]}…)")

    tags = len(HASHTAG.findall(plain))
    if tags < 5:
        warns.append(f"해시태그 {tags}개 (권장 5개 이상)")
    tail = [l.strip() for l in plain.splitlines() if l.strip() and not l.strip().startswith("#")]
    if tail and not tail[-1].rstrip(" ㅎㅋ").endswith("?"):
        warns.append("글 마지막이 독자 질문(댓글 유도)으로 끝나지 않음")

    print(f"== {path}  (본문 {chars}자, 사진 {photos}개, 해시태그 {tags}개)")
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
