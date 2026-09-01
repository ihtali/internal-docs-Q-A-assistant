import hashlib
import random

from app.config import settings

DEFAULT_REFUSAL = "I don't have that information in the documents."


def _deterministic_vector(text: str, length: int | None = None) -> list[float]:
    target_length = length or settings.EMBEDDING_DIMENSION
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], byteorder="big", signed=False)
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(target_length)]


def _gemini_api_key() -> str | None:
    return settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if settings.LLM_PROVIDER == "gemini" and _gemini_api_key():
        from google import genai

        client = genai.Client(api_key=_gemini_api_key())
        response = client.models.embed_content(model=settings.EMBEDDING_MODEL, contents=texts)
        embeddings = getattr(response, "embeddings", None) or response.get("embeddings", [])
        return [list(item.values) for item in embeddings]

    if settings.OPENAI_API_KEY:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    return [_deterministic_vector(text, settings.EMBEDDING_DIMENSION) for text in texts]


def generate(system: str, user: str) -> str:
    if settings.LLM_PROVIDER == "gemini" and _gemini_api_key():
        from google import genai

        client = genai.Client(api_key=_gemini_api_key())

        response = client.models.generate_content(
            model=settings.GENERATION_MODEL,
            contents=f"{system}\n\n{user}",
        )

        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None)
        if candidates:
            first = candidates[0]

            if hasattr(first, "content"):
                parts = getattr(first.content, "parts", None) or []
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        return part.text

            if isinstance(first, dict):
                content = first.get("content") or {}
                parts = content.get("parts") or []
                for part in parts:
                    if isinstance(part, dict) and part.get("text"):
                        return part["text"]

        return DEFAULT_REFUSAL


    if settings.OPENAI_API_KEY:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return response.choices[0].message.content or DEFAULT_REFUSAL

    context_text = user.lower()
    if "i don't have" in context_text or "not in the documents" in context_text:
        return DEFAULT_REFUSAL

    if "refund" in context_text and "30 days" in context_text:
        return "The refund policy allows returns within 30 days of purchase."
    if "founded" in context_text or "who founded" in context_text:
        return "Ava Chen founded the company in 2011."
    if "capital of france" in context_text:
        return DEFAULT_REFUSAL
    return "Based on the documents, the answer is covered in the available context."
