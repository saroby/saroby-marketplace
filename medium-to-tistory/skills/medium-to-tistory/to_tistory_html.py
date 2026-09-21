#!/usr/bin/env python3
"""post.md (가벼운 마크다운) → 티스토리 에디터가 만드는 것과 같은 모양의 HTML 본문.

usage: to_tistory_html.py post.md [-o post.tistory.md]

주인이 에디터로 쓴 글의 마크업을 그대로 흉내 낸다:
  - 연속된 문단 묶음은 <p data-ke-size="size16"> 하나에 넣고, 줄바꿈은 <br>,
    문단 사이는 <br><br>. (draft 에서 한 줄에 한 문장씩 쓰면 그대로 줄바꿈이 된다)
  - ## → <h2 data-ke-size="size26">, ### → <h3 data-ke-size="size23">
  - > → <blockquote data-ke-style="style2">, --- → 에디터 구분선 hr
  - ``` → <pre data-ke-type="codeblock">, - 목록 → <ul data-ke-list-type="disc">
  - **굵게** → <b>, `코드` → <code>, [글](url) → <a target="_blank" rel="noopener">
  - ![캡션](./images/x.png) 줄은 마크다운 그대로 둔다 (tistory-cli 이미지 업로더가 잡아야 함)
frontmatter 는 그대로 복사한다. 결과 파일을 tistory-cli post 에 넘긴다.
"""
import html
import re
import sys

P_OPEN = '<p data-ke-size="size16">'
IMAGE_RE = re.compile(r"^!\[[^\]]*\]\([^)]+\)\s*$")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def convert(body):
    out, text_paras = [], []

    def flush_text():
        if text_paras:
            joined = "<br><br>".join("<br>".join(inline(l) for l in p) for p in text_paras)
            out.append(P_OPEN + joined + "</p>")
            text_paras.clear()

    lines = body.split("\n")
    i, para = 0, []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if para: text_paras.append(para); para = []
            flush_text()
            lang = stripped[3:].strip()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            attrs = f' data-ke-language="{lang}"' if lang else ""
            cls = f' class="{lang}"' if lang else ""
            out.append(f'<pre{cls} data-ke-type="codeblock"{attrs}><code>'
                       + html.escape("\n".join(code), quote=False) + "</code></pre>")
            i += 1
            continue

        block = None
        if not stripped:
            if para: text_paras.append(para); para = []
        elif stripped.startswith("<"):  # 이미 HTML 인 줄은 손대지 않는다
            block = stripped
        elif IMAGE_RE.match(stripped):
            block = stripped
        elif m := re.match(r"^(#{2,4})\s+(.*)$", stripped):
            size = {2: ("h2", "size26"), 3: ("h3", "size23"), 4: ("h4", "size20")}[len(m.group(1))]
            block = f'<{size[0]} data-ke-size="{size[1]}">{inline(m.group(2))}</{size[0]}>'
        elif re.fullmatch(r"-{3,}|\*{3,}", stripped):
            block = '<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style1" />'
        elif stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(inline(lines[i].strip().lstrip(">").strip())); i += 1
            i -= 1
            block = '<blockquote data-ke-style="style2">' + "<br>".join(quote) + "</blockquote>"
        elif re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", lines[i])) + "</li>"); i += 1
            i -= 1
            block = '<ul style="list-style-type: disc;" data-ke-list-type="disc">' + "".join(items) + "</ul>"
        else:
            para.append(stripped)

        if block is not None:
            if para: text_paras.append(para); para = []
            flush_text()
            out.append(block)
        i += 1

    if para: text_paras.append(para)
    flush_text()
    # 각 블록을 빈 줄로 분리해야 tistory-cli 의 markdown-it 이 HTML 블록/이미지 줄을 따로 본다
    return "\n\n".join(out) + "\n"


def main():
    src = sys.argv[1]
    dst = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else re.sub(r"\.md$", "", src) + ".tistory.md"
    raw = open(src, encoding="utf-8").read()
    m = re.match(r"^---\n.*?\n---\n", raw, re.S)
    front, body = (m.group(0), raw[m.end():]) if m else ("", raw)
    open(dst, "w", encoding="utf-8").write(front + "\n" + convert(body))
    print(dst)


if __name__ == "__main__":
    main()
