# TextSight SDK: AI detector and AI humanizer API clients

Official open-source clients for the [TextSight](https://www.textsight.ai/) API. Detect AI-generated text from ChatGPT, Claude and Gemini with sentence-level scores, and humanize AI writing, from Python or JavaScript.

| Language | Folder | Install |
|---|---|---|
| Python 3.8+ | [`python/`](python/) | `pip install textsight` |
| Node.js 18+ / TypeScript | [`javascript/`](javascript/) | `npm install textsight` |

```python
from textsight import TextSight
print(TextSight().detect("Some text")["verdict"])
```

```js
import { TextSight } from "textsight";
console.log((await new TextSight().detect("Some text")).verdict);
```

Get an API key at [app.textsight.ai/signup](https://app.textsight.ai/signup). Full API reference: [textsight.ai/api-docs.html](https://www.textsight.ai/api-docs.html).

Looking for a free AI detector without code? Use [TextSight in the browser](https://www.textsight.ai/), an alternative to GPTZero, ZeroGPT, Originality.ai, Undetectable.ai and QuillBot.

MIT licensed.
