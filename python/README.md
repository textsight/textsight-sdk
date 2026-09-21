# TextSight Python client: AI detector and AI humanizer API

Free, open-source Python library for the [TextSight](https://www.textsight.ai/) API. Check if text was written by ChatGPT, Claude or Gemini, get a sentence-by-sentence AI score, and rewrite AI-sounding text so it reads naturally.

A developer-friendly alternative to the GPTZero, Originality.ai and ZeroGPT APIs. No dependencies, Python 3.8+.

## Install

```bash
pip install textsight
```

## Quick start

```python
from textsight import TextSight

ts = TextSight(api_key="sk_live_...")   # or set TEXTSIGHT_API_KEY
result = ts.detect("Paste the essay or article here...")
print(result["verdict"], result["humanization_score"])
```

You need a TextSight API key. [Create one here](https://app.textsight.ai/signup) (Settings → API Keys). API access is on the Pro plan and up, see [pricing](https://www.textsight.ai/pricing.html).

## How do I detect AI-generated text in Python?

```python
r = ts.detect(text)
r["verdict"]             # "human", "mixed" or "ai"
r["humanization_score"]  # 0-100, higher means more human
r["ai_probability"]      # 0-1
for s in r["sentences"]: # which sentences look AI-written
    print(s["label"], round(s["score"], 2), s["text"])
```

Need only the number? `ts.score(text)` is lighter and faster.

## How do I humanize AI text in Python?

```python
r = ts.rewrite(
    text,
    tone="academic",          # conversational, professional, academic, blog, email
    strength=3,               # 1 light to 5 aggressive
    preserve=["Smith (2021)"] # words to keep unchanged
)
print(r["rewritten"])
```

## Command line

```bash
export TEXTSIGHT_API_KEY=sk_live_...
textsight detect essay.txt
textsight rewrite draft.txt --tone blog
```

## Errors

| Exception | When |
|---|---|
| `AuthenticationError` | missing or wrong API key (401) |
| `PermissionDeniedError` | no API access on your plan, or monthly quota used up (403) |
| `RateLimitError` | too many requests per minute (429), retried automatically first |
| `ServiceUnavailableError` | detector briefly down (503), retried automatically first |

All inherit from `TextSightError`. Texts can be up to 50,000 characters. Detection is English only for now.

## FAQ

**Is this library free?** Yes, it's MIT licensed. API calls use your TextSight plan's quota.

**Can I try TextSight without code?** Yes, the [free AI detector](https://www.textsight.ai/) and humanizer work in the browser, no card needed.

**Where are the full API docs?** [textsight.ai/api-docs.html](https://www.textsight.ai/api-docs.html)

## License

MIT © TextSight
