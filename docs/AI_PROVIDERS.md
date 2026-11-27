# AI providers

| Priority | Routine | Complex | Eligibility |
| --- | --- | --- | --- |
| Groq | `openai/gpt-oss-20b` | `openai/gpt-oss-120b` | The official rate-limit table lists both for the free plan. Both support strict structured output. |
| Gemini | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | The official pricing page lists free input and output for standard inference. The free account and regional terms apply. |
| OpenRouter | `openrouter/free` | `openrouter/free` | Zero-priced router or an explicitly configured `:free` variant. Requests require structured output support, so unavailable combinations can fail. |

Use accounts without billing enabled for Groq and Gemini, and a dedicated OpenRouter key restricted to
free models. Verify these upstream settings before setting each `*_FREE_TIER_CONFIRMED=1`.
The flag attests to account configuration. SIGNAL cannot verify billing state from a general inference
response. The gateway has no paid fallback and does not request paid tools or service tiers.

Each stage uses a validated structured response. Failed, rate-limited, and schema-invalid requests
move to the next eligible provider. Repeated recent failures temporarily open that provider's circuit.
No eligible response leaves the durable job queued with bounded exponential backoff. A successful
response can be reused for identical validated stage inputs. A conservative local token reservation
counts UTF-8 prompt bytes plus the output cap and is shared across workers; it is not a provider quota.
Token totals only include values returned by providers.

Optional cloud embeddings use Gemini `gemini-embedding-001` with 768 dimensions and a single
model namespace. Perform an explicit re-embedding migration before moving to another vector space.
There is no NVIDIA NIM dependency. Check applicable terms before sending content or enabling billing.

Official documentation follows.

- [Groq rate limits](https://console.groq.com/docs/rate-limits) and [structured outputs](https://console.groq.com/docs/structured-outputs).
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) and [embeddings](https://ai.google.dev/gemini-api/docs/embeddings).
- [OpenRouter free router](https://openrouter.ai/openrouter/free) and [API limits](https://openrouter.ai/docs/api_reference/limits).
