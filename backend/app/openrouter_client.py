import json
import re
import time
import httpx
from typing import List, Dict, Any, Tuple, Optional, Union, AsyncGenerator
from app.config import settings
from app.models import SourceCitation


DISCLAIMER_TEXT = "Note: Real estate listings, prices, availability, and auction dates reflect the official verified scraping snapshot and should be confirmed on the official websites (darglobal.co.uk / wasalt.sa)."

def clean_llm_response(text: str) -> str:
    if not text:
        return ""
    # Strip <think>...</think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip reasoning traces like "Here's a thinking process: ... \n\n"
    if "thinking process" in text.lower():
        parts = re.split(r"(?:Here's a thinking process:.*?)(?:\n\n(?=[A-Z#\*])|\Z)", text, flags=re.DOTALL | re.IGNORECASE)
        if len(parts) > 1 and parts[-1].strip():
            text = parts[-1].strip()
    return text.strip()


class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None

    def get_http_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=45.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20, keepalive_expiry=60.0)
            )
        return self._client

    async def aclose(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def build_system_prompt(self) -> str:
        return (
            "You are an expert AI Real Estate Assistant specialized exclusively in DarGlobal and Wasalt.\n"
            "You answer questions ONLY using the verified knowledge base passages provided below.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Grounding: Answer strictly using facts from the provided context. Never invent prices, dates, units, licenses, or facts.\n"
            "2. URL Citations: For every project, property, license, or corporate fact you mention, include the exact official source URL from the context as a markdown link [Title](URL).\n"
            "3. Company Boundary: DarGlobal is a London-listed luxury real estate developer operating in the UAE, Qatar, Oman, Spain, UK, and Saudi Arabia. Wasalt is an AI-backed PropTech platform in Saudi Arabia licensed by REGA and Infath. Do not confuse them.\n"
            "4. Missing Information: If the context does not contain enough information to answer, state clearly: 'I cannot find this information in the official verified sources for DarGlobal and Wasalt.'\n"
            "5. Tone: Professional, authoritative, factual, and concise.\n"
            "6. Output Format: Output only the final response directly. Do NOT include any thinking logs, reasoning traces, or internal preamble."
        )


    def build_user_prompt(self, query: str, citations: List[SourceCitation], full_chunks: Dict[str, str]) -> str:
        context_blocks = []
        for i, cit in enumerate(citations, 1):
            full_text = full_chunks.get(cit.chunk_id, cit.content_snippet)
            context_blocks.append(
                f"[Source {i}] {cit.title} (Company: {cit.company}, Category: {cit.category})\n"
                f"Source URL: {cit.source_url}\n"
                f"Content:\n{full_text}"
            )
        context_str = "\n\n---\n\n".join(context_blocks)
        return (
            f"Context from Verified Knowledge Base:\n\n{context_str}\n\n"
            f"User Question: {query}\n\n"
            f"Please provide an accurate, grounded answer citing relevant source URLs as markdown links."
        )

    async def generate_response(
        self,
        query: str,
        citations: List[SourceCitation],
        full_chunks: Dict[str, str],
        return_timings: bool = False
    ) -> Union[Tuple[str, bool], Tuple[str, bool, Dict[str, float]]]:
        """
        Generates response using OpenRouter free model with connection pooling and timing instrumentation.
        """
        timings = {"context_prep_ms": 0.0, "openrouter_api_ms": 0.0}

        if not self.api_key:
            fallback = self._build_passage_fallback(query, citations, full_chunks, "OpenRouter API key is not configured on the backend.")
            return (fallback, True, timings) if return_timings else (fallback, True)

        if not citations:
            msg = "I cannot find this information in the official verified sources for DarGlobal and Wasalt."
            return (msg, False, timings) if return_timings else (msg, False)

        # Context Preparation Timing
        t_prep_start = time.perf_counter()
        sys_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(query, citations, full_chunks)
        timings["context_prep_ms"] = round((time.perf_counter() - t_prep_start) * 1000, 2)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://wasalt.sa",
            "X-Title": "DarGlobal & Wasalt Real Estate AI",
            "Content-Type": "application/json"
        }

        model_candidates = [self.model]
        for alt in ["google/gemma-4-26b-a4b-it:free", "nvidia/nemotron-3.5-lightning:free"]:
            if alt not in model_candidates:
                model_candidates.append(alt)

        client = self.get_http_client()
        last_err = ""
        t_api_start = time.perf_counter()

        for candidate_model in model_candidates:
            payload = {
                "model": candidate_model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": settings.MAX_TOKENS,
                "reasoning": {"effort": "none"}
            }
            try:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        raw_text = msg.get("content") or msg.get("reasoning") or ""
                        cleaned = clean_llm_response(raw_text)
                        if cleaned:
                            timings["openrouter_api_ms"] = round((time.perf_counter() - t_api_start) * 1000, 2)
                            return (cleaned, False, timings) if return_timings else (cleaned, False)
                elif res.status_code in (429, 502, 503):
                    last_err = f"HTTP {res.status_code} on {candidate_model}"
                    continue
                else:
                    last_err = f"OpenRouter returned HTTP {res.status_code} ({res.text[:120]})"
                    break
            except Exception as e:
                last_err = str(e)
                continue

        timings["openrouter_api_ms"] = round((time.perf_counter() - t_api_start) * 1000, 2)
        fallback = self._build_passage_fallback(query, citations, full_chunks, last_err)
        return (fallback, True, timings) if return_timings else (fallback, True)

    async def stream_response(
        self,
        query: str,
        citations: List[SourceCitation],
        full_chunks: Dict[str, str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams LLM response token-by-token using SSE over OpenRouter.
        Safely handles thinking traces, failovers before first token,
        and ensures no duplicate text is emitted on failure.
        """
        t_api_start = time.perf_counter()

        if not self.api_key:
            fallback = self._build_passage_fallback(query, citations, full_chunks, "OpenRouter API key is not configured on the backend.")
            for chunk in fallback.split("\n\n"):
                yield {"type": "token", "token": chunk + "\n\n"}
            yield {
                "type": "done",
                "answer": fallback,
                "model": "passage_fallback_retrieval",
                "citations": citations,
                "fallback_applied": True,
                "ttft_ms": 0.0,
                "total_api_ms": 0.0,
                "disclaimer": DISCLAIMER_TEXT
            }
            return

        if not citations:
            msg = "I cannot find this information in the official verified sources for DarGlobal and Wasalt."
            yield {"type": "token", "token": msg}
            yield {
                "type": "done",
                "answer": msg,
                "model": self.model,
                "citations": [],
                "fallback_applied": False,
                "ttft_ms": 0.0,
                "total_api_ms": 0.0,
                "disclaimer": DISCLAIMER_TEXT
            }
            return

        sys_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(query, citations, full_chunks)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://wasalt.sa",
            "X-Title": "DarGlobal & Wasalt Real Estate AI",
            "Content-Type": "application/json"
        }

        model_candidates = [self.model]
        for alt in ["google/gemma-4-26b-a4b-it:free", "nvidia/nemotron-3.5-lightning:free"]:
            if alt not in model_candidates:
                model_candidates.append(alt)

        client = self.get_http_client()
        first_token_time = None
        tokens_streamed = []
        streaming_started = False
        last_err = ""

        for candidate_model in model_candidates:
            payload = {
                "model": candidate_model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": settings.MAX_TOKENS,
                "reasoning": {"effort": "none"},
                "stream": True
            }
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        last_err = f"HTTP {response.status_code} on {candidate_model}"
                        continue

                    buffer = ""
                    inside_think = False
                    stream_done = False

                    async for raw_line in response.aiter_lines():
                        line = raw_line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            stream_done = True
                            break

                        try:
                            chunk = json.loads(data_str)
                        except Exception:
                            continue

                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content") or ""
                        if not content:
                            continue

                        # Clean thinking tokens (<think>...</think> and "Here's a thinking process:")
                        if inside_think:
                            buffer += content
                            if "</think>" in buffer:
                                parts = buffer.split("</think>", 1)
                                buffer = ""
                                inside_think = False
                                remainder = parts[1].lstrip()
                                if remainder:
                                    if not streaming_started:
                                        streaming_started = True
                                        first_token_time = time.perf_counter()
                                    tokens_streamed.append(remainder)
                                    yield {"type": "token", "token": remainder}
                        elif not streaming_started:
                            buffer += content
                            if "<think>" in buffer:
                                inside_think = True
                            elif "Here's a thinking process:" in buffer:
                                if "\n\n" in buffer:
                                    parts = buffer.split("\n\n", 1)
                                    remainder = parts[1].lstrip()
                                    buffer = ""
                                    if remainder:
                                        streaming_started = True
                                        first_token_time = time.perf_counter()
                                        tokens_streamed.append(remainder)
                                        yield {"type": "token", "token": remainder}
                            elif len(buffer) >= 6 and not buffer.startswith("<") and not buffer.startswith("Here"):
                                streaming_started = True
                                first_token_time = time.perf_counter()
                                tokens_streamed.append(buffer)
                                yield {"type": "token", "token": buffer}
                                buffer = ""
                        else:
                            tokens_streamed.append(content)
                            yield {"type": "token", "token": content}

                    # Flush any remaining buffer if stream ended cleanly
                    if buffer and not inside_think:
                        cleaned = clean_llm_response(buffer)
                        if cleaned:
                            if not streaming_started:
                                streaming_started = True
                                first_token_time = time.perf_counter()
                            tokens_streamed.append(cleaned)
                            yield {"type": "token", "token": cleaned}

                    if streaming_started or stream_done:
                        t_total_ms = (time.perf_counter() - t_api_start) * 1000
                        ttft_ms = (first_token_time - t_api_start) * 1000 if first_token_time else t_total_ms
                        full_answer_text = "".join(tokens_streamed).strip()
                        yield {
                            "type": "done",
                            "answer": full_answer_text,
                            "model": candidate_model,
                            "citations": citations,
                            "fallback_applied": False,
                            "ttft_ms": round(ttft_ms, 2),
                            "total_api_ms": round(t_total_ms, 2),
                            "disclaimer": DISCLAIMER_TEXT
                        }
                        return
                    else:
                        last_err = f"Model {candidate_model} returned empty stream"
                        continue

            except Exception as e:
                if streaming_started:
                    # User Rule 2: If streaming has already started and fails,
                    # do not restart another model silently or duplicate generated text.
                    partial = "".join(tokens_streamed).strip()
                    yield {
                        "type": "error",
                        "message": f"Streaming interrupted: {str(e)}",
                        "answer": partial,
                        "citations": citations,
                        "model": candidate_model,
                        "disclaimer": DISCLAIMER_TEXT
                    }
                    return
                else:
                    last_err = str(e)
                    continue

        # If all candidates failed before any tokens were streamed:
        fallback = self._build_passage_fallback(query, citations, full_chunks, last_err)
        for chunk in fallback.split("\n\n"):
            yield {"type": "token", "token": chunk + "\n\n"}
        t_total_ms = (time.perf_counter() - t_api_start) * 1000
        yield {
            "type": "done",
            "answer": fallback,
            "model": "passage_fallback_retrieval",
            "citations": citations,
            "fallback_applied": True,
            "ttft_ms": 0.0,
            "total_api_ms": round(t_total_ms, 2),
            "disclaimer": DISCLAIMER_TEXT
        }



    def _build_passage_fallback(self, query: str, citations: List[SourceCitation], full_chunks: Dict[str, str], reason: str) -> str:
        """
        Direct passage-based fallback returning the exact retrieved records with citations.
        Strictly compliant with Rule 4: No guessing or hallucinating.
        """
        if not citations:
            return f"No matching records found in the verified knowledge base.\n*(Status: {reason})*"

        lines = [
            f"*(Direct Knowledge Base Passages — {reason})*\n",
            f"Here are the most relevant verified records retrieved for **\"{query}\"**:\n"
        ]

        for i, c in enumerate(citations, 1):
            text = full_chunks.get(c.chunk_id, c.content_snippet)
            lines.append(f"### {i}. [{c.title}]({c.source_url})")
            lines.append(f"- **Company**: {c.company.upper()} | **Category**: {c.category}")
            lines.append(f"- **Official URL**: [{c.source_url}]({c.source_url})")
            lines.append(f"```\n{text}\n```\n")

        return "\n".join(lines)
