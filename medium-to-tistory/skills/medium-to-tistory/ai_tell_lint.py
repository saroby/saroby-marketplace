#!/usr/bin/env python3
"""블로그 초안에서 'AI가 쓴 티' 가 나는 레이아웃·문체 패턴을 센다.

usage: ai_tell_lint.py post.md|post.tistory.md|post.html [--title "제목"]
exit 0 = FAIL 없음, 1 = FAIL 있음. 목표: FAIL 0, WARN 2 이하.

임계값은 2026-09-21 ithat.tistory.com 에서 보정했다:
AI 템플릿 글 6편 vs 주인이 직접 쓴 글 11편. 연구에서 흔히 쓰는 '문장 길이 분산',
'연결어미 뒤 쉼표', '~다 어미 비율' 은 이 블로그 주인에게 오히려 반대로 나와서 뺐다
(주인은 짧은 줄을 고르게 쓰고, '~는데,' 쉼표를 AI 보다 많이 쓴다).
"""
import html
import re
import sys


def load(path):
    raw = open(path, encoding="utf-8").read()
    title = ""
    m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    if m:
        t = re.search(r'^title:\s*"?(.*?)"?\s*$', m.group(1), re.M)
        title = t.group(1) if t else ""
        raw = raw[m.end():]
    return raw, title


def split(raw):
    """md/html 섞인 본문 → (headings, paragraphs)"""
    s = re.sub(r"<pre.*?</pre>|```.*?```", "\n\n", raw, flags=re.S)  # 코드는 문체 검사에서 제외
    s = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n\n## \1\n\n", s, flags=re.S)
    s = re.sub(r"</p>|<br\s*/?>|</li>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    headings, paras = [], []
    for block in re.split(r"\n\s*\n", s):
        b = block.strip()
        if not b or b.startswith("!["):
            continue
        if b.startswith("#"):
            headings.append(b.lstrip("# ").strip())
        else:
            paras.append(re.sub(r"\s+", " ", b))
    return headings, paras


def count(pattern, text):
    return len(re.findall(pattern, text, re.M))


def main():
    args = sys.argv[1:]
    title_override = None
    if "--title" in args:
        i = args.index("--title")
        title_override = args[i + 1]
        del args[i:i + 2]
    raw, title = load(args[0])
    title = html.unescape(html.unescape(title_override or title))
    headings, paras = split(raw)
    body = "\n".join(paras)
    k = max(len(body), 1) / 1000  # 1000 자당 비율용
    sentences = [x for x in re.split(r"(?<=[.?!])\s+|(?<=다)\s+", body) if len(x) > 3]

    fails, warns = [], []

    def check(cond, level, msg):
        if cond:
            (fails if level == "FAIL" else warns).append(msg)

    # ---- 레이아웃 (AI 템플릿 지문) ----
    check(re.search(r"\s[—–]\s|&mdash;", title), "FAIL", f"제목의 'A — B' 부제 공식: {title!r}")
    check(re.search(r":\s", title), "WARN", f"제목의 'A: B' 부제 공식: {title!r}")
    hr = count(r"<hr\b|^\s*(-{3,}|\*{3,})\s*$", raw)
    check(hr > 2, "FAIL", f"구분선 {hr}개 (사람 글 0~2, AI 템플릿 7~9)")
    check(re.search(r"한 줄 룰|핵심 요약|TL;DR|한 줄 요약|3줄 요약", raw), "FAIL", "'한 줄 룰/요약' 박스")
    check(re.search(r"<div[^>]*style=", raw), "FAIL", "스타일 박스 div (callout)")
    check("<style" in raw, "FAIL", "본문 <style> 블록")
    emoji = count(r"[✅✨❌⭐\U0001F300-\U0001FAFF]", body + " ".join(headings))
    check(emoji > 0, "FAIL", f"이모지 {emoji}개 (✅🚀💡 류)")
    plain_p = count(r"<p>(?!\s*(&nbsp;)?\s*</p>)", raw)  # 에디터가 남기는 빈 <p> 는 무시
    check(plain_p >= 3 and "data-ke-size" in raw, "FAIL",
          f"에디터 속성 없는 <p> {plain_p}개 섞임 (to_tistory_html.py 로 변환)")
    check(plain_p > 0 and "data-ke-size" not in raw, "WARN",
          "에디터 마크업(data-ke-*)이 아님 — 발행 전 to_tistory_html.py 로 변환")

    max_h = max(3, round(k))
    check(len(headings) > max_h, "WARN", f"소제목 {len(headings)}개 (이 길이면 {max_h}개 이하)")
    numbered = [h for h in headings if re.match(r"^\d+[.)]\s", h)]
    check(len(numbered) >= 3, "WARN", f"번호 소제목 {len(numbered)}개 (1., 2., 3. …)")
    check(any(re.fullmatch(r"(마무리|결론|정리|맺음말|요약|나가며|마치며)", h) for h in headings), "WARN",
          "'마무리/결론' 소제목")
    bold = count(r"\*\*[^*]+\*\*|<strong>|<b>", raw)
    check(bold > 2 and bold / k > 1.5, "WARN", f"굵은 글씨 {bold}곳 ({bold / k:.1f}/천자, 사람 글 ≤1.1, AI 3.7~7.8)")
    label_bullets = count(r"^\s*[-*]\s+\*\*[^*]+:?\*\*:?", raw)
    check(label_bullets >= 2, "WARN", f"'- **라벨:** 설명' 목록 {label_bullets}개 — 문장으로 풀기")
    check(len(body) > 5000, "WARN", f"본문 {len(body)}자 (주인 글은 대개 2000자 안팎, 5000 이하 권장)")

    # ---- 문장/어휘 공식 ----
    contrast = count(r"(이|가|게|건|것이) 아니라|것이 아니다|건 아니다|인가, .{1,20}인가", body)
    check(contrast >= 3 and contrast / k > 1.0, "WARN",
          f"'A가 아니라 B' 대비 {contrast}회 (사람 글 대부분 0, 1번까지만)")
    first = count(r"(^|\s)(나는|내가|나도|난 |내 |나에게|저는|제가|우리 집|우리 팀)", body)
    check(len(body) > 500 and first / k < 1.0, "WARN",
          f"1인칭 {first}회 ({first / k:.1f}/천자, 주인 글 대부분 1.5 이상) — 실제 겪은 장면이 없음")
    dash = body.count("—") + body.count("–")
    check(dash > 2, "WARN", f"본문 em dash {dash}개 (2개 이하)")
    enum = count(r"(두|세|네|다섯) 가지|(둘|셋|넷)이다|첫째|둘째|셋째", body)
    check(enum >= 2, "WARN", f"'N 가지/첫째 둘째' 열거 공식 {enum}회")
    hypo = count(r"예를 들어[^.]*?(하자|보자)\b", body)
    check(hypo > 0, "WARN", f"가상 예시('예를 들어 ~하자') {hypo}회 — 실제 겪은 일로")
    wrap = re.findall(r"결론적으로|요약하면|종합하면|이를 통해|그러므로|이처럼|나아가|요컨대", body)
    check(len(wrap) >= 2, "WARN", f"정리·연결 상투어 {len(wrap)}회: {sorted(set(wrap))}")
    cleft = re.findall(r"(?:중요한|필요한|핵심은|핵심인) (?:것은|건)|로 이어진다|하는 이유다|시사하는 바|주목할 만하다", body)
    check(len(cleft) >= 2, "WARN", f"강조 공식 {len(cleft)}회: {sorted(set(cleft))}")
    hype = re.findall(r"혁신적|획기적|압도적|파격적|게임 ?체인저|패러다임|폭발적", body)
    check(len(hype) >= 2, "WARN", f"과장 어휘 {len(hype)}회: {sorted(set(hype))}")
    transl = re.findall(r"에 대해|[을를] 통해|에 있어서?|되어진다|에 의해|함에 있어", body)
    check(len(transl) / k > 1.5, "WARN", f"번역투 {len(transl)}회: {sorted(set(transl))}")
    boiler = re.findall(r"알아보겠습니다|알아봅시다|살펴보겠습니다|도움이 되었으면|도움이 되셨|하는 것이 중요합니다|다음과 같다|다음과 같습니다", body)
    check(boiler, "WARN", f"블로그 상투구: {sorted(set(boiler))}")
    hedge = re.findall(r"수 있을 (?:것으로|가능성)|라고 할 수 있", body)
    check(len(hedge) >= 2, "WARN", f"겹친 얼버무림 {len(hedge)}회")
    ends = [re.sub(r"[.?!\"'”’) ]+$", "", s)[-2:] for s in sentences]
    run = best = 1
    for a, b in zip(ends, ends[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    check(best >= 4, "WARN", f"같은 어미 {best}문장 연속 (3개까지)")

    for m in fails:
        print("FAIL ", m)
    for m in warns:
        print("WARN ", m)
    print(f"-- chars={len(body)} headings={len(headings)} sentences={len(sentences)} "
          f"fail={len(fails)} warn={len(warns)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
