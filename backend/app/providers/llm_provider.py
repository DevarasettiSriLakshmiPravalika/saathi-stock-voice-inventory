"""
LLM provider abstraction for claim extraction and query intent parsing.

CRITICAL RULES (Contract §53):
- LLM extracts structured data ONLY.
- LLM NEVER directly modifies inventory.
- LLM NEVER approves or rejects statements.
- All LLM output is validated by Pydantic before use.
- Invalid LLM output is safely rejected.
"""
import json
import re
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, field_validator


class ExtractedClaim(BaseModel):
    """
    Structured claim extracted from transcript.
    All fields validated — invalid LLM output raises ValidationError.
    """
    product: str
    quantity: float
    unit: str
    direction: str  # IN or OUT
    actor: Optional[str] = "self"
    event_time: Optional[str] = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        v = v.upper()
        if v not in ("IN", "OUT"):
            raise ValueError(f"direction must be IN or OUT, got: {v}")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v


class QueryIntent(BaseModel):
    """Parsed intent from owner natural-language query."""
    intent: str  # CURRENT_STOCK | SALES_TODAY | RECEIPTS_TODAY | etc.
    product_name: Optional[str] = None
    date_filter: Optional[str] = None
    raw_query: str


class LLMProvider(ABC):
    @abstractmethod
    async def extract_claim(self, transcript: str) -> Optional[ExtractedClaim]:
        """Extract structured claim from transcript. Returns None if extraction fails."""
        ...

    @abstractmethod
    async def parse_query_intent(self, query: str) -> QueryIntent:
        """Parse owner natural-language query into structured intent."""
        ...

    @abstractmethod
    async def generate_explanation(self, context: dict) -> str:
        """Generate human-readable explanation based on actual backend evidence."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


class MockLLMProvider(LLMProvider):
    """
    Development LLM provider — uses rule-based parsing.
    Returns deterministic results for testing.
    Used when SAATHI_LLM_PROVIDER=mock.
    """

    @property
    def provider_name(self) -> str:
        return "mock-llm-v1"

    async def extract_claim(self, transcript: str) -> Optional[ExtractedClaim]:
        """
        Rule-based claim extraction for development/testing.
        Parses patterns like: "5 bags of rice received", "sold 10 kg sugar"
        """
        t = transcript.lower().strip()

        # Determine direction
        out_keywords = ["sold", "sell", "gave", "dispatched", "sent", "out", "sale", "delivered to customer"]
        in_keywords = ["received", "got", "added", "purchased", "bought", "in", "arrived", "delivered from supplier", "inward"]

        direction = "IN"
        for kw in out_keywords:
            if kw in t:
                direction = "OUT"
                break
        for kw in in_keywords:
            if kw in t:
                direction = "IN"
                break

        # Extract quantity (first number in transcript)
        numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", t)
        quantity = float(numbers[0]) if numbers else 1.0

        # Extract unit
        units = ["bag", "bags", "kg", "kgs", "liter", "liters", "litre", "litres",
                 "packet", "packets", "piece", "pieces", "box", "boxes", "ton", "tons",
                 "quintal", "quintals", "unit", "units", "carton", "cartons"]
        unit = "unit"
        for u in units:
            if u in t:
                unit = u.rstrip("s") if u.endswith("s") and u != "bags" else u
                # Normalize
                if u in ("bags", "bag"):
                    unit = "bag"
                elif u in ("kgs", "kg"):
                    unit = "kg"
                elif u in ("liters", "litre", "litres", "liter"):
                    unit = "liter"
                elif u in ("packets", "packet"):
                    unit = "packet"
                elif u in ("pieces", "piece"):
                    unit = "piece"
                elif u in ("boxes", "box"):
                    unit = "box"
                elif u in ("cartons", "carton"):
                    unit = "carton"
                break

        # Extract product name — last significant noun phrase
        # Remove numbers and units from transcript to find product
        # Strip punctuation first so trailing periods, commas, or question marks don't contaminate entity names
        clean = re.sub(r"[^\w\s]", " ", t)
        for n in numbers:
            clean = re.sub(r"\b" + re.escape(n) + r"\b", " ", clean)
        for u in units:
            clean = re.sub(r"\b" + u + r"\b", " ", clean)
        for kw in out_keywords + in_keywords + ["of", "the", "a", "an", "from", "to", "supplier", "customer", "please"]:
            clean = re.sub(r"\b" + kw + r"\b", " ", clean)
        # What's left is likely the product
        words = [w for w in clean.split() if len(w) >= 2]
        product = " ".join(words[:2]) if words else "unknown"

        if not product or product == "unknown":
            return None

        try:
            return ExtractedClaim(
                product=product.strip().title(),
                quantity=quantity,
                unit=unit,
                direction=direction,
            )
        except Exception:
            return None

    async def parse_query_intent(self, query: str) -> QueryIntent:
        """Rule-based query intent parsing."""
        q = query.lower().strip()

        if any(w in q for w in ["sold", "sell", "sales", "out today"]):
            intent = "SALES_TODAY"
        elif any(w in q for w in ["received", "came in", "incoming", "bought", "purchased", "in today"]):
            intent = "RECEIPTS_TODAY"
        elif any(w in q for w in ["review", "pending", "flagged", "approve"]):
            intent = "REVIEW_QUEUE"
        elif any(w in q for w in ["low", "running out", "reorder", "shortage"]):
            intent = "LOW_STOCK"
        elif any(w in q for w in ["history", "transactions", "statements"]):
            intent = "PRODUCT_HISTORY"
        elif any(w in q for w in ["who", "which speaker", "who delivered"]):
            intent = "STATEMENT_SEARCH"
        elif any(w in q for w in ["how much", "how many", "stock", "inventory", "left", "available", "remaining"]):
            intent = "CURRENT_STOCK"
        else:
            intent = "CURRENT_STOCK"

        # Try to extract product name cleanly
        product_name = None
        patterns = [
            r"(?:how much|how many|what is the stock of|check stock of|quantity of|stock of)\s+(?:bags of\s+|kg of\s+|packets of\s+)?([a-zA-Z0-9_\-]+)",
            r"([a-zA-Z0-9_\-]+)\s+(?:stock|left|remaining|available|inventory)",
        ]
        for pat in patterns:
            m = re.search(pat, q)
            if m:
                candidate = m.group(1).strip()
                stopwords = {"much", "many", "stock", "left", "the", "a", "an", "is", "are", "do", "we", "have", "any"}
                if candidate not in stopwords and len(candidate) > 1:
                    product_name = candidate
                    break

        if not product_name:
            for word in query.split():
                cleaned_word = re.sub(r"[^\w]", "", word)
                if len(cleaned_word) > 3 and cleaned_word[0].isupper():
                    product_name = cleaned_word
                    break

        return QueryIntent(intent=intent, product_name=product_name, raw_query=query)

    async def generate_explanation(self, context: dict) -> str:
        """Generate explanation based on actual backend evidence."""
        decision = context.get("decision", "UNKNOWN")
        trust_score = context.get("trust_score", 0)
        plausibility_passed = context.get("plausibility_passed", True)
        contradiction = context.get("contradiction_level", "NO_CONFLICT")
        speaker_status = context.get("speaker_status", "UNKNOWN")

        if decision == "AUTO_CONFIRMED":
            parts = []
            if speaker_status == "IDENTIFIED":
                parts.append("the speaker is enrolled and identified")
            if trust_score >= 0.7:
                parts.append(f"speaker trust score is high ({trust_score:.2f})")
            if plausibility_passed:
                parts.append("the quantity is within normal range for this product")
            if contradiction == "NO_CONFLICT":
                parts.append("no conflicting recent statements were found")
            return "Confirmed automatically because " + ", and ".join(parts) + "." if parts else "Confirmed automatically."

        elif decision == "REQUIRES_REVIEW":
            reasons = []
            if speaker_status != "IDENTIFIED":
                reasons.append("speaker could not be identified with confidence")
            if trust_score < 0.5:
                reasons.append(f"speaker trust score is low ({trust_score:.2f})")
            if not plausibility_passed:
                reasons.append("the quantity is outside the normal range for this product")
            if contradiction in ("POSSIBLE_CONFLICT", "STRONG_CONFLICT"):
                reasons.append("a conflicting recent statement was detected")
            return "Requires owner review because " + ", and ".join(reasons) + "." if reasons else "Requires review."

        elif decision == "REJECTED":
            return (
                "Rejected because the statement could not be verified — "
                "speaker is unknown, quantity is implausible, or a strong contradiction was detected."
            )

        return "Decision made by deterministic backend engine."


class RealLLMProvider(LLMProvider):
    """
    Real LLM provider using OpenAI API.
    Requires OPENAI_API_KEY in environment or .env.
    """

    @property
    def provider_name(self) -> str:
        return "gpt-4o"

    async def extract_claim(self, transcript: str) -> Optional[ExtractedClaim]:
        try:
            import os
            import openai
            from app.config import get_settings
            settings = get_settings()
            api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return None

            client = openai.AsyncOpenAI(api_key=api_key)
            prompt = f"""Extract inventory claim from this voice transcript.
Return ONLY valid JSON with fields: product, quantity (number), unit, direction (IN or OUT), actor, event_time (null if not mentioned).
Transcript: "{transcript}"
JSON:"""
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200,
            )
            raw = response.choices[0].message.content.strip()
            # Extract JSON from response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                return None
            data = json.loads(match.group())
            if data.get("product"):
                data["product"] = re.sub(r"[^\w\s]", "", str(data["product"])).strip().title()
            return ExtractedClaim(**data)
        except Exception:
            return None

    async def parse_query_intent(self, query: str) -> QueryIntent:
        try:
            import os
            import openai
            from app.config import get_settings
            settings = get_settings()
            api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                mock = MockLLMProvider()
                return await mock.parse_query_intent(query)

            client = openai.AsyncOpenAI(api_key=api_key)
            intents = "CURRENT_STOCK|SALES_TODAY|RECEIPTS_TODAY|PRODUCT_HISTORY|LOW_STOCK|REVIEW_QUEUE|STATEMENT_SEARCH"
            prompt = f"""Classify this inventory query intent.
Intents: {intents}
Return JSON: {{"intent": "...", "product_name": null_or_string, "date_filter": null_or_string}}
Query: "{query}"
JSON:"""
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            raw = response.choices[0].message.content.strip()
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError("No JSON in response")
            data = json.loads(match.group())
            prod = data.get("product_name")
            if prod:
                prod = re.sub(r"[^\w\s]", "", str(prod)).strip()
            return QueryIntent(intent=data.get("intent", "CURRENT_STOCK"), product_name=prod, raw_query=query)
        except Exception:
            mock = MockLLMProvider()
            return await mock.parse_query_intent(query)

    async def generate_explanation(self, context: dict) -> str:
        # Fall back to deterministic explanation
        provider = MockLLMProvider()
        return await provider.generate_explanation(context)


def get_llm_provider() -> LLMProvider:
    from app.config import get_settings
    settings = get_settings()
    if settings.SAATHI_LLM_PROVIDER == "openai":
        return RealLLMProvider()
    return MockLLMProvider()
