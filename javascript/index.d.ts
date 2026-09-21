export type Verdict = "human" | "mixed" | "ai";
export type Tone = "conversational" | "professional" | "academic" | "blog" | "email";

export interface SentenceScore {
  text: string;
  score: number;
  label: "human" | "ai";
}

export interface DetectResult {
  humanization_score: number;
  ai_probability: number;
  verdict: Verdict;
  sentences: SentenceScore[];
  confidence: number;
  model: string;
  request_id: string;
}

export interface ScoreResult {
  humanization_score: number;
  ai_probability: number;
  confidence: number;
  request_id: string;
}

export interface RewriteResult {
  rewritten: string;
  humanization_score: number;
  ai_probability: number;
  score_reliable: boolean;
  request_id: string;
}

export interface RewriteOptions {
  tone?: Tone;
  strength?: 1 | 2 | 3 | 4 | 5;
  preserve?: string[];
}

export interface TextSightOptions {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

export declare class TextSightError extends Error {
  status?: number;
  code?: string;
  body?: unknown;
}

export declare class TextSight {
  constructor(opts?: TextSightOptions);
  detect(text: string): Promise<DetectResult>;
  score(text: string): Promise<ScoreResult>;
  rewrite(text: string, opts?: RewriteOptions): Promise<RewriteResult>;
  humanize(text: string, opts?: RewriteOptions): Promise<RewriteResult>;
}

export default TextSight;
