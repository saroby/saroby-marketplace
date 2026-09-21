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

`medium-cli` 와 `tistory-cli` 를 묶어, 사람이 직접 쓴 것 같은 비공개 한국어 글을 티스토리에 올리는
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

### 2. 이미지 — 실제 산출물 우선, 없을 때만 `codex-util:imagegen`

추상 일러스트 hero 가 맨 위에 박혀 있는 것도 AI 글 티다. 우선순위:

1. 실제 스크린샷 (터미널, 에러 화면, diff, 앱 화면). 본문 중간, 해당 장면 옆에 넣고
   아래에 짧은 캡션 한 줄 (주인 글처럼 "1998년 화니백화점 외관" 식).
2. 그런 게 없고 이미지가 꼭 필요하면 `codex-util:imagegen`. 이때도 글 맨 위 고정이
   아니라 흐름상 어울리는 자리에 둔다. 이미지가 없어도 된다.

생성이 필요하면 **항상 `codex-util:imagegen` 을 통해 생성**한다. `Skill` 도구로 호출:

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
  `image_generation_user_error` 로 거부. 정사각으로 시작한다. 본문에 `<style>` 로 크기를 줄이지 않는다 (AI 템플릿 지문).
- 본인 블로그 헤더 배너가 _다크 네이비_ 일 가능성이 있으니 hero 는 _가능하면 다른
  계열_ (warm cream, pastel peach, ivory 등) 로. 헤더와 같은 톤이면 페이지 상단이 한
  덩어리로 무거워 보인다.
- 글자/로고/사람 얼굴은 프롬프트에서 명시적으로 _제외_. moderation 거절 회피 +
  추상성 유지.
- 위 가이드대로 해도 moderation 거절이 나면 프롬프트를 _3 줄 이내_ 의 단순한 형태로
  줄여 재시도.

### 3. 한국어 본문 작성 (substantially original)

목표는 이 블로그 주인(치킨치)이 직접 쓴 글처럼 읽히는 것이다. 잘 정리된 보고서처럼 보이면 실패다. 2026-09-21 에 올린 "멀티 에이전트 — 쪼개는 것보다 넘겨주는 게 어렵다" 가 AI 티 난다는 지적을 받았는데, 원인은 문장보다 레이아웃 템플릿이었다. 번호 소제목 여섯 개, 섹션마다 구분선, 천 자당 네 곳 넘는 굵은 글씨, "한 줄 룰" 박스, 그리고 경험 하나 없이 "예를 들어 ~했다고 하자" 로 때운 예시. 이 절의 규칙과 점검 스크립트는 그 글과 주인이 직접 쓴 글 11편을 비교해서 만들었다.

#### 3-0. 쓰기 전에: 실제 경험과 재료를 모은다

사람 글과 AI 글을 가르는 가장 큰 차이는 구체적인 내 장면이다. 날짜, 도구 이름, 에러 메시지, 걸린 시간, 틀렸던 판단 같은 것. Google 도 E-E-A-T 의 Experience 를 보고, 네이버는 AI 자동 발행 블로그를 통째로 누락시킨 사례가 보고돼 있다. 그렇다고 겪지 않은 일을 1인칭으로 지어내면 거짓말이니 절대 하지 않는다.

현재 대화나 작업 맥락에 실제 사건이 있으면 그걸 쓴다. 없으면 `AskUserQuestion` 으로 한 번만 묻는다. 질문은 "이 주제로 직접 겪은 일 하나만 알려주세요 (한두 줄이면 됨)" 이고, 선택지는 "직접 적을게요" 와 "경험 없이 관찰자 시점으로 써줘" 두 개. 관찰자 시점이면 "요즘 보면", "써 본 사람들 얘기로는" 같은 톤으로 쓰고 가짜 에피소드는 넣지 않는다. 실제 로그, 명령어, 스크린샷이 있으면 같이 모은다. 진짜 산출물이 가장 강한 사람 흔적이다.

#### 3-1. 목소리

주인이 직접 쓴 글은 이런 식이다 (`5월 20일`):

> 아빠의 사업실패라는 흔한 이유로,
> 가족이 사글세방에 살던 때가 있었다.
> 봉지라면 한개 반을 나누여 먹어야 할 만큼 가난했던 걸로 기억한다.
> 나는 분명 신라면이라고 생각했는데,
> 상모를 돌리는 풍물놀이패가 그려진건 삼양의 '이백냥 라면'이라는 걸 오늘에야 깨달았다.
>
> 가장 기억에 남는 건 "피구왕 통키"의 오프닝곡.

한 줄에 한 문장씩 끊고, 몇 줄 묶음 사이를 한 줄 띄운다. 기억과 감각이 먼저 나오고 생각은 그 뒤에 따라온다. "~던 걸로 기억한다", "~였는지도 모르겠다", "대학생(?) 형" 처럼 모르는 건 모른다고 흐린다. 어미는 담백한 "~다" 체가 기본인데, 사이사이에 "~의 오프닝곡." 같은 명사로 끝나는 짧은 줄, 혼잣말 같은 질문, "~더랬다" 같은 말투가 끼어든다. "~는데," 로 문장을 이어 붙이는 쉼표도 자주 쓴다. 이건 주인 버릇이니 일부러 없애지 않는다 (연구에서는 AI 티로 꼽지만 이 블로그에서는 반대로 나왔다).

기술 글이어도 이 목소리를 가져온다. 개념을 먼저 설명하고 예시를 붙이지 말고, 일어난 일을 먼저 쓰고 거기서 알게 된 걸 쓴다. 확신 없는 건 확신 없다고 쓰고, 삽질한 건 숨기지 않는다. 결론을 요약하며 끝내지 말고 마지막으로 할 말을 하고 멈춘다. 아직 모르는 것이나 다음에 해 볼 것으로 끝나도 된다. 원문(Medium)의 골격은 버리고 내 사건을 중심으로 다시 짠다. 출처 표기는 하지 않는다 (사용자 기본 요구).

길이는 1500 ~ 4000 자. 주인 글은 대개 2000 자 안팎이고, 할 말이 끝나면 짧아도 멈춘다.

#### 3-2. 레이아웃

초안은 `/tmp/m2t/<slug>/post.md` 에 가벼운 마크다운으로 쓴다. HTML 을 직접 쓰지 않는다. 발행 직전에 3-4 의 변환기가 티스토리 에디터가 만드는 마크업으로 바꿔 준다.

```markdown
---
title: "<평범한 한 문장 제목>"
tags: [태그1, 태그2, ...]
visibility: private
draft: false
mode: html
---

지난주에 ~하다가 ~했다.
한 줄에 한 문장.

빈 줄은 묶음 사이에만.

![이미지 아래에 붙을 캡션](./images/shot.png)

## 소제목은 필요할 때만, 말하듯이

...
```

제목은 "에이전트한테 일 넘기다 반나절 날린 얘기" 처럼 평범한 한 문장으로 짓는다. "A — B" 부제 공식은 이 블로그의 AI 글 6편 중 5편이 쓴 지문이다. 소제목은 없어도 되고, 쓰더라도 천 자당 하나 정도에 번호는 붙이지 않는다. 구분선, 박스, 이모지, `<style>` 은 쓰지 않는다. 굵은 글씨는 정말 강조할 한두 곳만. 목록은 실제로 단계나 항목일 때만 쓰고, "- **라벨:** 설명" 식으로 늘어놓지 않는다. 이미지는 `![캡션](경로)` 로 쓰면 tistory-cli 가 alt 를 사진 캡션으로 붙여 준다.

문장에서 피할 공식은 이렇다. "A가 아니라 B다" 대비는 글 전체에 한 번까지 (AI 글은 천 자당 0.5~3.6 번, 주인 글은 대부분 0). 문단 끝마다 격언 한 줄 붙이기. "좋은 X는 / 나쁜 X는" 대칭. "세 가지", "첫째/둘째" 열거. "예를 들어 ~하자" 가상 예시. "결론적으로, 이를 통해, 이처럼, 중요한 것은, ~로 이어진다, 시사하는 바가 크다" 같은 정리·강조 상투어. "혁신적, 획기적, 패러다임" 과장. "~에 대해, ~를 통해, ~에 있어" 번역투 반복. "알아보겠습니다, 도움이 되었으면" 블로그 상투구.

#### 3-3. 점검과 고쳐 쓰기 (발행 전 필수)

초안을 쓴 직후 기계 점검을 돌린다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/medium-to-tistory/ai_tell_lint.py /tmp/m2t/<slug>/post.md
```

목표는 FAIL 0, WARN 2 이하. 기준으로 보면, 주인이 직접 쓴 일기류 글 11편은 전부 0/0 이고 AI 템플릿 글 6편은 FAIL 1~5 또는 WARN 5~9 다. 수치를 맞추려고 문장을 억지로 비틀지는 않는다. WARN 이 걸리면 그 문장이 왜 거기 있는지부터 다시 본다.

스크립트는 레이아웃과 상투어만 잡는다. 그래서 통과한 뒤에 따로 한 번 읽는다. 쓴 사람이 아니라 처음 보는 독자 입장에서 "이 글에서 AI 가 쓴 티가 나는 곳이 어디지?" 라고 묻고 걸리는 곳을 적는다. 흔히 걸리는 건 이렇다. 모든 문단이 비슷한 모양(주장 → 근거 → 정리). 누구나 쓸 수 있는 첫 두 문단. 독자가 알 만한 걸 굳이 설명하는 부분. 놀라운 것이나 분명한 입장이 하나도 없는 것. 적은 곳만 고치고, 사실·숫자·고유명사·인용은 건드리지 않고, 새 주장도 보태지 않는다. 앞머리 빌드업과 끝의 요약은 대개 통째로 지워도 된다. 고친 뒤 lint 를 한 번 더 돌린다.

`humanize-korean` 플러그인이 설치돼 있으면 (`/plugin install humanize-korean@saroby-marketplace`) 이 단계에서 본문 문장만 한 번 윤문해도 된다. 번역투, 접속사 남발, 겹친 얼버무림을 잘 잡는다. 레이아웃은 건드리지 않고 원문 대비 30% 넘게 바꾸지 않도록 설계돼 있어서 3-2 를 대신하지는 못한다. 윤문 결과가 주인의 "~는데," 쉼표나 짧은 줄 끊기를 지우면 되돌린다.

#### 3-4. 에디터 마크업으로 변환

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/medium-to-tistory/to_tistory_html.py /tmp/m2t/<slug>/post.md
# → /tmp/m2t/<slug>/post.tistory.md
python3 ${CLAUDE_PLUGIN_ROOT}/skills/medium-to-tistory/ai_tell_lint.py /tmp/m2t/<slug>/post.tistory.md
```

기존 AI 글은 맨 `<p>` 를 수십 개 썼고, 주인 글은 에디터가 만든 `<p data-ke-size="size16">` 하나 안에 줄마다 `<br>`, 묶음 사이 `<br><br>` 를 쓴다. 변환기는 이 모양을 그대로 만들고, 소제목·인용·코드·목록·구분선도 에디터 속성(`data-ke-size`, `data-ke-style`, `data-ke-type`)을 붙여 준다. 굵게는 `<b>` 로 바꾼다 (에디터 기본값). 이미지 줄은 마크다운 그대로 남겨서 tistory-cli 업로더가 잡게 한다. tistory-cli 의 markdown-it(`html: true`)이 이 HTML 을 손대지 않고 통과시키는 건 2026-09-21 에 확인했다.

### 4. tistory 발행

```bash
cd /tmp/m2t/<slug>
tistory-cli post post.tistory.md --pretty   # 3-4 에서 변환한 파일
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
- 이미지가 있다면 페이지 상단을 _절반 이상_ 덮지 않음 (헤더와 분리감)
- 스크린샷을 훑었을 때 "정돈된 보고서"처럼 보이지 않음 (번호 소제목·구분선·박스 없음)
- 이미지 아래 캡션이 붙어 있음 (alt 텍스트 → figcaption)

## 흔한 실패와 대응

| 증상 | 원인 | 대응 |
|---|---|---|
| 본문이 비어 발행됨 | tistory-cli writeMarkdownArea 의 CM 동기화 깨짐 | tistory-cli 가 fix 후 빌드/설치 됐는지 확인 (`writeMarkdownArea` 가 ta.fill 우선 + clearBody 가 CM-direct) |
| 이미지 0 개 | `<img src="./...">` 같은 raw HTML 사용 | markdown `![](./images/x.png)` 로 바꿔야 medium-cli 의 scanLocalImages 가 잡음 |
| `EDIT_FAILED [editor:imageUpload]` 2 장째 | imageUploader 의 file input 재마운트 누락 | tistory-cli 픽스 적용본인지 확인 (`uploadImages` 루프 안에서 `ensureFileInputMounted` 재호출) |
| `EDIT_FAILED [editor:modeSwitch]` | mode 버튼이 role=presentation 이라 Playwright 가 거부 | `ensureHtmlMode` 에 JS `.click()` 폴백 들어가 있는지 확인 |
| markup 이 본문에 토큰 그대로 노출 | md→html 변환에서 placeholder restore 실패 | `htmlConverter.ts` 가 HTML 주석 placeholder 쓰는지 확인 |
| hero 가 헤더와 한 덩어리로 보임 | hero 가 페이지 헤더와 같은 톤/너비 | 위 §2 의 가이드대로 다른 톤, 필요하면 hero 자체를 빼거나 본문 중간으로 |
| "AI 가 쓴 것 같다" 피드백 | 번호 소제목·`<hr>`·callout·균일 문단 템플릿 | §3 전체: 실제 경험 확보 → 목소리 → lint FAIL 0 / WARN ≤2 → 에디터 마크업 변환 |

## 운영 메모

- 작업 디렉터리는 `/tmp/m2t/<slug>` 로 고정. 사용자가 명시 안 하면 묻지 말고 거기 쓴다.
- 사용자가 `mode` 를 따로 지정 안 하면 항상 `html`. 마크다운 모드는 빈 `<p>` /
  blockquote phantom span 같은 cosmetic 잡티가 따라온다.
- 사용자가 `visibility` 를 따로 지정 안 하면 항상 `private`. 공개 발행은 명시 요청이
  있을 때만.
- 발행 후 결과 URL + id 를 사용자에게 보고. 가능하면 시각 검증 스크린샷도.
- 비공개로 올리고 사용자가 읽어 본 뒤 공개하는 흐름을 유지한다. 하루에 여러 편을
  몰아 올리지 않는다. 네이버가 AI 자동 발행 티스토리를 통째로 누락시킨 사례와
  Google 의 scaled content abuse 정책이 둘 다 '양산' 을 겨냥한다.
- lint 임계값은 주인 글 11편 / AI 글 6편으로 보정했다 (2026-09-21). 주인이 새 글을
  직접 쓰면 가끔 그 글에 lint 를 돌려 WARN 이 나오는 규칙이 있는지 확인하고 조정한다.
