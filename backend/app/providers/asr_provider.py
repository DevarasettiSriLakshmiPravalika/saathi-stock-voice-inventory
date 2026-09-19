"""
ASR (Automatic Speech Recognition) provider abstraction.

Supports:
  - MockASRProvider: returns configurable mock transcripts for testing
  - WhisperASRProvider: placeholder for real Whisper integration

Language support: English, Hindi, Telugu, Hinglish, code-mixed.
"""
from abc import ABC, abstractmethod
from typing import Optional


class ASRResult:
    def __init__(
        self,
        transcript: str,
        language: str,
        confidence: float,
        provider: str,
        success: bool,
        error: Optional[str] = None,
    ):
        self.transcript = transcript
        self.language = language
        self.confidence = confidence
        self.provider = provider
        self.success = success
        self.error = error


class ASRProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        """Transcribe audio bytes to text."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


class MockASRProvider(ASRProvider):
    """
    Development ASR provider — returns a configurable mock transcript.
    Used when SAATHI_ASR_PROVIDER=mock.
    """

    @property
    def provider_name(self) -> str:
        return "mock-asr-v1"

    async def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        import os
        from app.config import get_settings
        settings = get_settings()
        default_transcript = getattr(settings, "SAATHI_MOCK_ASR_TRANSCRIPT", None) or os.environ.get(
            "SAATHI_MOCK_ASR_TRANSCRIPT", "Sold 5 bags of rice."
        )
        return ASRResult(
            transcript=default_transcript,
            language="en",
            confidence=0.95,
            provider=self.provider_name,
            success=True,
        )


class WhisperASRProvider(ASRProvider):
    """
    Real Whisper ASR provider.
    Requires openai API key (OPENAI_API_KEY in .env or environment).
    """

    @property
    def provider_name(self) -> str:
        return "whisper-v3"

    async def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        try:
            import os
            import io
            import openai
            from app.config import get_settings
            settings = get_settings()

            api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return ASRResult(
                    transcript="",
                    language="en",
                    confidence=0.0,
                    provider=self.provider_name,
                    success=False,
                    error="OPENAI_API_KEY is not configured. Set OPENAI_API_KEY in .env or set SAATHI_ASR_PROVIDER=mock.",
                )

            client = openai.AsyncOpenAI(api_key=api_key)
            audio_file = io.BytesIO(audio_bytes)
            # OpenAI requires a recognizable audio extension
            ext = os.path.splitext(filename or "")[1].lower()
            if not ext:
                audio_file.name = "audio.wav"
            else:
                audio_file.name = filename

            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )
            return ASRResult(
                transcript=response.text,
                language=getattr(response, "language", "en"),
                confidence=0.90,
                provider=self.provider_name,
                success=True,
            )
        except Exception as e:
            return ASRResult(
                transcript="",
                language="en",
                confidence=0.0,
                provider=self.provider_name,
                success=False,
                error=str(e),
            )


class GroqASRProvider(ASRProvider):
    """
    Real Groq ASR provider using Whisper on Groq Cloud.
    Requires GROQ_API_KEY in environment or .env.
    Supports multilingual transcription: English, Hindi, Telugu, and Hinglish / code-mixed speech.
    """

    def __init__(self, model: Optional[str] = None):
        from app.config import get_settings
        settings = get_settings()
        import os
        self.model = model or getattr(settings, "GROQ_ASR_MODEL", None) or os.environ.get("GROQ_ASR_MODEL", "whisper-large-v3-turbo")

    @property
    def provider_name(self) -> str:
        return f"groq-{self.model}"

    async def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        import os
        import io
        import re
        from app.config import get_settings
        settings = get_settings()

        api_key = getattr(settings, "GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
        if not api_key:
            return ASRResult(
                transcript="",
                language="en",
                confidence=0.0,
                provider=self.provider_name,
                success=False,
                error="GROQ_API_KEY is not configured. Set GROQ_API_KEY in .env or environment.",
            )

        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)

            # Ensure recognizable audio extension for Groq Whisper
            ext = os.path.splitext(filename or "")[1].lower()
            safe_name = filename if ext else "audio.wav"

            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = safe_name

            # Transcribe via Groq Whisper API
            # Omit language so Whisper auto-detects language (multilingual / Hinglish)
            response = await client.audio.transcriptions.create(
                file=audio_file,
                model=self.model,
                response_format="verbose_json",
                temperature=0.0,
            )

            text = getattr(response, "text", "") or ""
            detected_lang = getattr(response, "language", "en") or "en"

            return ASRResult(
                transcript=text.strip(),
                language=str(detected_lang),
                confidence=0.95,
                provider=self.provider_name,
                success=True,
            )
        except Exception as e:
            # Safely mask any credentials if present in exception
            err_msg = str(e)
            err_msg = re.sub(r"gsk_[a-zA-Z0-9_-]+", "[REDACTED]", err_msg)
            err_msg = re.sub(r"Bearer\s+[a-zA-Z0-9_\.\-]+", "Bearer [REDACTED]", err_msg)
            return ASRResult(
                transcript="",
                language="en",
                confidence=0.0,
                provider=self.provider_name,
                success=False,
                error=err_msg,
            )


def get_asr_provider() -> ASRProvider:
    from app.config import get_settings
    settings = get_settings()
    provider_type = (settings.SAATHI_ASR_PROVIDER or "mock").lower().strip()
    if provider_type == "groq":
        return GroqASRProvider()
    elif provider_type == "whisper":
        return WhisperASRProvider()
    return MockASRProvider()
