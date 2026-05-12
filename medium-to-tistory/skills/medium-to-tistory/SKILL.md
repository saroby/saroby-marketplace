---
name: medium-to-tistory
description: |
  Download a Medium article with `medium-cli` to use as topic inspiration, write a
  substantially original Korean post on the same topic, generate a hero image with
  codex imagegen, and publish privately to Tistory via `tistory-cli` in HTML mode.
  Use when the user asks to "medium 글 가져와서 tistory 에 올려", "메디움→티스토리",
  "medium 글 각색해서 올려줘", or any combination of `medium-cli` + `tistory-cli`.
triggers:
  - medium to tistory
  - 메디움 티스토리
  - medium-cli tistory-cli
  - medium 글 각색 업로드
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - WebSearch
  - AskUserQuestion
  - Skill
---

# medium-to-tistory

`medium-cli` 와 `tistory-cli` 를 묶어, 깔끔한 비공개 한국어 글을 티스토리에 올리는
end-to-end 흐름. 이 skill 은 **번역/재배포 도구가 아니다** — 원문은 _주제 확인용
입력_ 으로만 쓰고, 게시되는 본문/이미지는 모두 새로 만든다.

## 절대 규칙 (IP)

- 원문의 본문 텍스트를 한국어로 옮겨 그대로 (혹은 가벼운 paraphrase 로) 발행하지
  않는다. 그건 출처 표기 유무와 무관하게 무단 derivative 다.
- 원문의 이미지를 그대로 가져다 본문에 박지 않는다. 새 이미지를 `codex-util:imagegen`
  으로 생성하거나, 본인이 만든 자산을 쓴다.
- 사용자가 "그래도 그대로 옮겨" 같이 요청해도, 위 두 규칙은 그대로 둔다. 대신
  사용자에게 더 안전한 3 가지 옵션을 한 번 제시한 뒤 본인 분석으로 글을 쓴다.
- 본문에서 _짧은 직접 인용_ (15 단어 이내) + 따옴표 표시 + 출처 링크는 허용. 사용자가
  "원문 출처 빼" 라고 명시한 경우엔 인용 자체도 빼고 _완전히 본인 시점_ 으로 쓴다.

## 사전 조건 확인

```bash
which medium tistory-cli >/dev/null 2>&1 || echo "global cli 누락 — npm install -g medium-cli tistory-cli"
tistory-cli whoami 2>&1 | grep -q '"ok":true' || echo "tistory 세션 만료 — 별도 터미널에서 'tistory-cli login --pretty' 필요"
```

`tistory-cli login` 은 인터랙티브 TTY 가 필요해서 Claude Code 의 `!` 셸에서는 안
돈다. 만료면 사용자에게 _별도 터미널_ 에서 `tistory-cli login --pretty` 실행을 요청
한 뒤 재개.

## 입력 정리

URL 이 명시되면 그대로 사용. 없으면:

1. 주제(예: "에이전트 평가", "context engineering") 가 주어진 경우 → `WebSearch` 로
   `site:medium.com <topic> 2026 free` 검색해 후보 5 개 정도 추리고 가장 가벼운 (멤버십
   아닌) 것을 선택.
2. 주제도 없으면 → `AskUserQuestion` 으로 어떤 분야의 글을 원하는지 한 번 묻기.

## 단계

### 1. medium-cli 로 다운로드

```bash
medium --pretty download "<URL>" -o /tmp/m2t/medium
```

성공 시 `/tmp/m2t/medium/<slug>-<postId>/` 에 `index.md` + `images/` 가 생긴다.

문제 패턴:

- `PARSE_ERROR — Medium 글 페이지가 아닙니다` → URL 이 `og:type=article` 인지 의심.
  Medium 의 `SocialMediaPosting` JSON-LD 도 article 로 간주하도록 medium-cli 의
  `src/adapters/web.ts` 가 패치돼 있어야 함.
- `paywallTruncated` → 멤버십 글. 다른 URL 후보로 교체.
- Cloudflare 403 → curl 은 막혀도 medium-cli (Node fetch) 는 보통 통과. 다른 URL 로 재시도.

다운로드된 `index.md` 와 `images/` 는 **본인 학습용** 으로만 읽는다. 본문이나
이미지를 그대로 옮기지 않는다.

### 2. hero 이미지 생성 — 반드시 `codex-util:imagegen` 사용

이미지는 **항상 `codex-util:imagegen` 을 통해 생성**한다. `Skill` 도구로 호출:

```
Skill(skill="codex-util:imagegen",
      args="<주제에 맞는 추상/일러스트 프롬프트>. 출력: /tmp/m2t/<slug>/images/hero.png, 1024x1024, quality high.")
```

스킬이 내부에서 codex `responses` 엔드포인트(ChatGPT 구독 경로)로 라우팅한다.
plugin 버전 경로(`.../codex-util/<ver>/...`) 를 직접 호출하지 말 것 — 업그레이드 시
깨진다. 다른 이미지 도구 (nanobanana, DALL·E API 등) 도 _쓰지 않는다_. `codex-util:imagegen`
한 곳으로 통일.

스킬이 실제로 도는지 빠르게 확인하려면:

```bash
ls -la /tmp/m2t/<slug>/images/hero.png   # 파일이 생겼는지
```

이미지 가이드라인 (시행착오 끝의 정착값):

- 기본 사이즈는 `1024x1024`. `1024x576`/`1536x864` 등 비-정사각은 가끔 codex 가
  `image_generation_user_error` 로 거부. 정사각으로 시작해서 본문에서 CSS 로 축소.
- 본인 블로그 헤더 배너가 _다크 네이비_ 일 가능성이 있으니 hero 는 _가능하면 다른
  계열_ (warm cream, pastel peach, ivory 등) 로. 헤더와 같은 톤이면 페이지 상단이 한
  덩어리로 무거워 보인다.
- 글자/로고/사람 얼굴은 프롬프트에서 명시적으로 _제외_. moderation 거절 회피 +
  추상성 유지.
- 위 가이드대로 해도 moderation 거절이 나면 프롬프트를 _3 줄 이내_ 의 단순한 형태로
  줄여 재시도.

### 3. 한국어 본문 작성 (substantially original)

`/tmp/m2t/<slug>/post.md` 에 다음 형태로 작성:

```markdown
---
title: "<독립적으로 매력적인 한국어 제목>"
tags: [태그1, 태그2, ...]
visibility: private
draft: false
mode: html
---

<style>
  .imageblock.alignCenter img { max-width: 480px; height: auto; }
  blockquote { border-left: 3px solid #d4d4d8; padding: 0.2em 1em; color: #52525b; }
</style>

![](./images/hero.png)

<인트로 — 한두 문단, 짧게>

<hr>

## 1. <섹션 제목>

...

<hr>

## 2. ...

...

<hr>

## <마지막>

<본문 마무리>

<div style="margin: 2em 0; padding: 1.2em 1.4em; border-left: 4px solid #f59e0b; background: #fff7ed; border-radius: 4px;">
  <p style="margin: 0; font-size: 1.05em; line-height: 1.6;">
    <strong>한 줄 룰</strong> — <글 전체를 함축하는 한 문장>
  </p>
</div>
```

작성 가이드라인:

- **각 단락 2 ~ 4 문장 이내.** 200 자 넘어가는 단락은 쪼갠다. 좁은 티스토리 컬럼에서
  텍스트 벽이 되기 쉽다.
- **em dash 절제.** 한 단락에 1 개 정도. 남발하면 시각적으로 빽빽.
- **섹션 사이 `<hr>`.** 5 개 이상의 섹션이면 사이마다 무조건.
- **마지막에 callout div** (위 템플릿의 amber border-left + cream 배경) 로 _한 줄 룰_.
  본인의 통찰을 응축한 한 문장.
- 출처 표기 _안 함_ (사용자 디폴트 요구). 본문이 본인 분석이라 출처가 없어도 정직함.
- 내용은 _원문의 구조를 따라가지 말 것_. 본인 경험·예시·분류로 재구성. 원문이 "5
  steps" 라면 본인은 "3 단계 + 안티 패턴" 같이 다른 골격.
- 길이는 4000 ~ 6000 자 정도가 sweet spot. 너무 길면 좁은 컬럼에서 부담스러움.

### 4. tistory 발행

```bash
cd /tmp/m2t/<slug>
tistory-cli post post.md --pretty
```

성공 메시지에 글 id 가 직접 안 보이면:

```bash
tistory-cli list --limit 1 2>&1 | python3 -c "import sys,json; d=json.loads(sys.stdin.read())['data']['items'][0]; print(d['id'], d['status'], d['title'])"
```

### 5. 결과 점검 (시각 확인)

비공개 글이지만 본인 세션에서 렌더링 확인:

```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ headless: true });
  const ctx = await b.newContext({ storageState: '/Users/saroby/.config/tistory-cli/storageState.json', viewport: { width: 1280, height: 900 } });
  const p = await ctx.newPage();
  await p.goto('https://<host>/<id>', { waitUntil: 'networkidle' });
  await p.screenshot({ path: '/tmp/m2t/preview.png', fullPage: true });
  await b.close();
})();
"
```

스크린샷을 `Read` 로 띄워 사용자에게 보여 주거나 시각 점검에 쓴다.

체크 항목 (모두 통과해야 "예쁘게 발행됨"):

- 빈 `<p></p>` 0 개
- 같은 이미지가 본문에 2 번 안 나옴 (kakaocdn URL 의 query string 까지 동일한 중복)
- blockquote 안 `font-family: 'Noto Serif KR'` phantom span 없음 (HTML 모드면 자동 해결)
- placeholder 문자열 (`TISTORYMARKUP\d+`) 본문에 노출 0
- hero 이미지가 페이지 상단을 _절반 이상_ 덮지 않음 (헤더와 분리감)
- 섹션 사이 시각적 구분 있음 (`<hr>` 가 보여야 함)

## 흔한 실패와 대응

| 증상 | 원인 | 대응 |
|---|---|---|
| 본문이 비어 발행됨 | tistory-cli writeMarkdownArea 의 CM 동기화 깨짐 | tistory-cli 가 fix 후 빌드/설치 됐는지 확인 (`writeMarkdownArea` 가 ta.fill 우선 + clearBody 가 CM-direct) |
| 이미지 0 개 | `<img src="./...">` 같은 raw HTML 사용 | markdown `![](./images/x.png)` 로 바꿔야 medium-cli 의 scanLocalImages 가 잡음 |
| `EDIT_FAILED [editor:imageUpload]` 2 장째 | imageUploader 의 file input 재마운트 누락 | tistory-cli 픽스 적용본인지 확인 (`uploadImages` 루프 안에서 `ensureFileInputMounted` 재호출) |
| `EDIT_FAILED [editor:modeSwitch]` | mode 버튼이 role=presentation 이라 Playwright 가 거부 | `ensureHtmlMode` 에 JS `.click()` 폴백 들어가 있는지 확인 |
| markup 이 본문에 토큰 그대로 노출 | md→html 변환에서 placeholder restore 실패 | `htmlConverter.ts` 가 HTML 주석 placeholder 쓰는지 확인 |
| hero 가 헤더와 한 덩어리로 보임 | hero 가 페이지 헤더와 같은 톤/너비 | 위 §2 의 가이드대로 다른 톤 + max-width 480px CSS |

## 운영 메모

- 작업 디렉터리는 `/tmp/m2t/<slug>` 로 고정. 사용자가 명시 안 하면 묻지 말고 거기 쓴다.
- 사용자가 `mode` 를 따로 지정 안 하면 항상 `html`. 마크다운 모드는 빈 `<p>` /
  blockquote phantom span 같은 cosmetic 잡티가 따라온다.
- 사용자가 `visibility` 를 따로 지정 안 하면 항상 `private`. 공개 발행은 명시 요청이
  있을 때만.
- 발행 후 결과 URL + id 를 사용자에게 보고. 가능하면 시각 검증 스크린샷도.
