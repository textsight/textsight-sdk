// TextSight API client: AI content detection and AI text humanizing.
// Docs: https://www.textsight.ai/api-docs.html
// Get an API key: https://app.textsight.ai/signup

const DEFAULT_BASE_URL = "https://api.textsight.ai/v2";
const TONES = ["conversational", "professional", "academic", "blog", "email"];
const MAX_CHARS = 50000;
const RETRYABLE = new Set([429, 500, 502, 503, 504]);

export class TextSightError extends Error {
  constructor(message, { status, code, body } = {}) {
    super(message);
    this.name = "TextSightError";
    this.status = status;
    this.code = code;
    this.body = body;
  }
}

export class TextSight {
  /**
   * @param {object} [opts]
   * @param {string} [opts.apiKey]  defaults to process.env.TEXTSIGHT_API_KEY
   * @param {string} [opts.baseUrl]
   * @param {number} [opts.timeout] ms, default 60000
   * @param {number} [opts.maxRetries] default 2
   */
  constructor(opts = {}) {
    const envKey =
      typeof process !== "undefined" && process.env ? process.env.TEXTSIGHT_API_KEY : undefined;
    this.apiKey = opts.apiKey || envKey;
    if (!this.apiKey) {
      throw new TextSightError(
        "No API key. Pass { apiKey } or set TEXTSIGHT_API_KEY. Get a key at https://app.textsight.ai/signup",
        { status: 401, code: "unauthorized" }
      );
    }
    this.baseUrl = (opts.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.timeout = opts.timeout ?? 60000;
    this.maxRetries = opts.maxRetries ?? 2;
  }

  /** Detect AI-generated text with sentence-level scores. */
  detect(text) {
    return this.#post("/detect", { text: checkText(text) });
  }

  /** Lightweight authenticity score (no sentence breakdown). */
  score(text) {
    return this.#post("/score", { text: checkText(text) });
  }

  /** Humanize AI-sounding text. */
  rewrite(text, { tone = "conversational", strength = 3, preserve } = {}) {
    if (!TONES.includes(tone)) throw new RangeError(`tone must be one of ${TONES.join(", ")}`);
    if (!(strength >= 1 && strength <= 5)) throw new RangeError("strength must be between 1 and 5");
    const body = { text: checkText(text), tone, strength: Math.trunc(strength) };
    if (typeof preserve === "string") preserve = [preserve];
    if (preserve && preserve.length) body.preserve = preserve.map(String);
    return this.#post("/rewrite", body);
  }

  humanize(text, opts) {
    return this.rewrite(text, opts);
  }

  async #post(path, body) {
    for (let attempt = 0; ; attempt++) {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), this.timeout);
      let res;
      try {
        res = await fetch(this.baseUrl + path, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(body),
          signal: ctrl.signal,
        });
      } catch (e) {
        clearTimeout(timer);
        if (attempt < this.maxRetries) {
          await sleep(backoff(attempt));
          continue;
        }
        const why = e && e.name === "AbortError" ? `timed out after ${this.timeout} ms` : e.message;
        throw new TextSightError(`Network error: ${why}`);
      }
      clearTimeout(timer);
      const raw = await res.text();
      let data;
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        if (res.ok) {
          throw new TextSightError("Unexpected non-JSON response from TextSight API", {
            status: res.status,
            body: raw.slice(0, 500),
          });
        }
        data = {};
      }
      if (res.ok) return data;
      if (RETRYABLE.has(res.status) && attempt < this.maxRetries) {
        await sleep(backoff(attempt, res.headers.get("retry-after")));
        continue;
      }
      const err = data && data.error;
      const code = typeof err === "object" && err ? err.code : err;
      const message =
        (typeof err === "object" && err && err.message) || data.message || `HTTP ${res.status}`;
      throw new TextSightError(message, { status: res.status, code, body: data });
    }
  }
}

function checkText(text) {
  if (typeof text !== "string" || !text.trim()) throw new TypeError("text must be a non-empty string");
  if (text.length > MAX_CHARS) throw new RangeError(`text is longer than ${MAX_CHARS} characters`);
  return text;
}

function backoff(attempt, retryAfter) {
  const s = Number(retryAfter);
  if (retryAfter != null && !Number.isNaN(s)) return Math.min(s * 1000, 30000);
  return Math.min(500 * 2 ** attempt, 8000);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export default TextSight;
