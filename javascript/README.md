# TextSight JavaScript client: AI detector and AI humanizer API

Free, open-source Node.js library for the [TextSight](https://www.textsight.ai/) API. Check if text was written by ChatGPT, Claude or Gemini, get a sentence-by-sentence AI score, and rewrite AI-sounding text so it reads naturally.

A developer-friendly alternative to the GPTZero, Originality.ai and ZeroGPT APIs. Zero dependencies, TypeScript types included, Node 18+.

## Install

```bash
npm install textsight
```

## Quick start

```js
import { TextSight } from "textsight";

const ts = new TextSight({ apiKey: "sk_live_..." }); // or set TEXTSIGHT_API_KEY
const result = await ts.detect("Paste the essay or article here...");
console.log(result.verdict, result.humanization_score);
```

You need a TextSight API key. [Create one here](https://app.textsight.ai/signup) (Settings → API Keys). API access is on the Pro plan and up, see [pricing](https://www.textsight.ai/pricing.html). Keep the key on your server, never in browser code.

## How do I detect AI-generated text in JavaScript?

```js
const r = await ts.detect(text);
r.verdict;            // "human" | "mixed" | "ai"
r.humanization_score; // 0-100, higher means more human
r.sentences.forEach((s) => console.log(s.label, s.score, s.text));
```

Need only the number? `ts.score(text)` is lighter and faster.

## How do I humanize AI text in JavaScript?

```js
const r = await ts.rewrite(text, {
  tone: "professional",   // conversational, professional, academic, blog, email
  strength: 3,            // 1 light to 5 aggressive
  preserve: ["ACME Inc."] // words to keep unchanged
});
console.log(r.rewritten);
```

## Errors

Failed calls throw `TextSightError` with `status` (401, 403, 429, 503...), `code` and `message`. Rate limits (429) and brief outages (503) are retried automatically twice before throwing. Texts can be up to 50,000 characters. Detection is English only for now.

## FAQ

**Is this library free?** Yes, it's MIT licensed. API calls use your TextSight plan's quota.

**Can I try TextSight without code?** Yes, the [free AI detector](https://www.textsight.ai/) and humanizer work in the browser, no card needed.

**Where are the full API docs?** [textsight.ai/api-docs.html](https://www.textsight.ai/api-docs.html)

## License

MIT © TextSight
