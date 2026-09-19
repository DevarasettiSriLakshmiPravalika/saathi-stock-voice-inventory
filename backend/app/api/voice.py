"""
Voice API — enrollment and audio processing.

POST /api/v1/voice/enroll    — enroll speaker voice profile
POST /api/v1/voice/process   — complete voice processing pipeline

This is the core Saathi workflow endpoint.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.voice_profile import VoiceProfile

from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, StatementSource
from app.dependencies import get_current_user, get_shop_or_404, require_shop_member
from app.services import voice_service, statement_service
from app.services.entity_resolution_service import resolve_product, resolve_unit
from app.services.trust_service import calculate_trust, record_trust_event
from app.services.plausibility_service import check_plausibility
from app.services.contradiction_service import check_contradiction
from app.services.decision_service import make_decision
from app.providers.asr_provider import get_asr_provider
from app.providers.llm_provider import get_llm_provider
from app.config import get_settings

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])
settings = get_settings()

MAX_AUDIO_BYTES = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}


def _validate_audio(file: UploadFile, content: bytes):
    """Validate audio file for safety and size."""
    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext and ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_AUDIO", "message": f"Unsupported audio format: {ext}. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"},
        )
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_AUDIO", "message": f"Audio file too large. Maximum size: {settings.MAX_AUDIO_SIZE_MB}MB."},
        )
    if len(content) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_AUDIO", "message": "Audio file is too small or empty."},
        )


@router.post("/enroll")
async def enroll_voice(
    shop_id: uuid.UUID = Form(...),
    member_user_id: Optional[uuid.UUID] = Form(None),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enroll a speaker voice profile.

    shop_id: The shop to enroll for.
    member_user_id: User to enroll (defaults to current_user). Owner can enroll other members.
    audio: Audio file containing speaker sample.
    """
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    # Determine who we're enrolling
    enroll_user_id = member_user_id or current_user.id

    # If enrolling someone else, must be owner
    if enroll_user_id != current_user.id:
        from app.dependencies import require_shop_owner
        await require_shop_owner(shop_id, current_user, db)

    content = await audio.read()
    _validate_audio(audio, content)

    import os
    safe_filename = os.path.basename(audio.filename or "audio.wav")

    profile = await voice_service.enroll_voice(
        db=db,
        user_id=enroll_user_id,
        shop_id=shop_id,
        audio_bytes=content,
        filename=safe_filename,
    )

    audit = AuditLog(
        shop_id=shop_id,
        actor_id=current_user.id,
        action=AuditAction.VOICE_ENROLLED.value,
        entity_type="voice_profile",
        entity_id=profile.id,
        metadata_={
            "enrolled_user_id": str(enroll_user_id),
            "status": profile.enrollment_status.value,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(profile)

    return {
        "success": True,
        "data": {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "shop_id": str(profile.shop_id),
            "enrollment_status": profile.enrollment_status.value,
            "quality_score": profile.quality_score,
            "audio_duration_seconds": profile.audio_duration_seconds,
            "model_version": profile.model_version,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
            # embedding intentionally omitted
        },
    }


@router.get("/profiles")
async def list_voice_profiles(
    shop_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List voice profiles for a shop (safe metadata only)."""
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    result = await db.execute(
        select(VoiceProfile).where(VoiceProfile.shop_id == shop_id)
    )
    profiles = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(p.id),
                "user_id": str(p.user_id),
                "shop_id": str(p.shop_id),
                "enrollment_status": p.enrollment_status.value,
                "quality_score": p.quality_score,
                "audio_duration_seconds": p.audio_duration_seconds,
                "model_version": p.model_version,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in profiles
        ],
    }


@router.post("/process")
async def process_voice(
    shop_id: uuid.UUID = Form(...),
    audio: Optional[UploadFile] = File(None),
    transcript_override: Optional[str] = Form(None),
    source: Optional[str] = Form("MOBILE_WEB"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Central Saathi voice processing pipeline.

    Accepts audio OR a transcript_override (for testing without real audio).

    Pipeline:
    Audio → ASR → Speaker ID → Claim Extraction → Entity Resolution →
    Trust → Plausibility → Contradiction → Decision → Statement
    """
    started_at = datetime.now(timezone.utc)
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    # Clean transcript_override if empty or whitespace
    if transcript_override is not None:
        transcript_override = transcript_override.strip() or None

    # Validate audio source
    if audio is None and not transcript_override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Either audio file or transcript_override is required."},
        )

    audio_bytes = None
    safe_filename = "audio.wav"
    if audio:
        audio_bytes = await audio.read()
        import os
        safe_filename = os.path.basename(audio.filename or "audio.wav")
        # If client submitted an empty 0-byte audio file while providing a transcript override, treat as text-only
        if len(audio_bytes) == 0 and transcript_override:
            audio_bytes = None
        else:
            _validate_audio(audio, audio_bytes)

    # ── STEP 1: Speaker Identification ─────────────────────────────────────────
    speaker_result = None
    speaker_status = "UNKNOWN"
    speaker_confidence = 0.0
    voice_profile_id = None

    if audio_bytes:
        speaker_result = await voice_service.identify_speaker(db, shop_id, audio_bytes, safe_filename)
        speaker_status = speaker_result.status
        speaker_confidence = speaker_result.confidence
        if speaker_result.voice_profile_id:
            voice_profile_id = uuid.UUID(speaker_result.voice_profile_id)

    actor_id = None
    if speaker_result and speaker_result.user_id:
        actor_id = uuid.UUID(speaker_result.user_id)
    elif not audio_bytes and transcript_override:
        actor_id = current_user.id
        speaker_status = "IDENTIFIED"
        speaker_confidence = 1.0

    # ── STEP 2: ASR (Speech to Text) ───────────────────────────────────────────
    transcript = transcript_override
    asr_confidence = 1.0
    asr_language = "en"
    asr_provider_name = "override"

    if audio_bytes and not transcript_override:
        asr_provider = get_asr_provider()
        asr_result = await asr_provider.transcribe(audio_bytes, safe_filename)
        if not asr_result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "TRANSCRIPTION_FAILED", "message": asr_result.error or "Transcription failed."},
            )
        transcript = asr_result.transcript
        asr_confidence = asr_result.confidence
        asr_language = asr_result.language
        asr_provider_name = asr_result.provider

    # ── STEP 3: Claim Extraction (LLM) ─────────────────────────────────────────
    llm_provider = get_llm_provider()
    claim = await llm_provider.extract_claim(transcript or "")

    raw_claim = None
    product_id = None
    quantity = None
    unit = None
    direction = None

    if claim:
        raw_claim = {
            "product": claim.product,
            "quantity": claim.quantity,
            "unit": claim.unit,
            "direction": claim.direction,
            "actor": claim.actor,
            "event_time": claim.event_time,
        }

        # ── STEP 4: Entity Resolution ───────────────────────────────────────────
        entity_result = await resolve_product(db, shop_id, claim.product)
        resolved_unit = await resolve_unit(db, shop_id, claim.unit)

        quantity = claim.quantity
        unit = resolved_unit or claim.unit
        direction = claim.direction

        if entity_result.resolved:
            product_id = entity_result.product.id
        # If ambiguous, product_id stays None — will go to REQUIRES_REVIEW

    # ── STEP 5: Trust Evaluation ────────────────────────────────────────────────
    trust = await calculate_trust(
        db=db,
        shop_id=shop_id,
        user_id=actor_id,
        speaker_status=speaker_status,
        speaker_confidence=speaker_confidence,
    )

    # ── STEP 6: Plausibility Check ──────────────────────────────────────────────
    plausibility = await check_plausibility(
        db=db,
        shop_id=shop_id,
        product_id=product_id,
        quantity=quantity or 0,
        direction=direction or "IN",
    )

    # ── STEP 7: Contradiction Check ─────────────────────────────────────────────
    contradiction = await check_contradiction(
        db=db,
        shop_id=shop_id,
        product_id=product_id,
        quantity=quantity or 0,
        direction=direction or "IN",
    )

    # ── STEP 8: Decision Engine ─────────────────────────────────────────────────
    # If no claim extracted, force REQUIRES_REVIEW
    if not claim:
        from app.services.decision_service import DecisionResult
        decision_result = DecisionResult("REQUIRES_REVIEW", {
            "reason": "Could not extract a structured claim from transcript.",
            "trust_score": trust.score,
            "speaker_status": speaker_status,
        })
    elif not product_id:
        from app.services.decision_service import DecisionResult
        decision_result = DecisionResult("REQUIRES_REVIEW", {
            "reason": "Product could not be resolved — ambiguous or not found.",
            "trust_score": trust.score,
            "speaker_status": speaker_status,
        })
    else:
        decision_result = make_decision(trust, plausibility, contradiction, speaker_status)

    # ── STEP 9: Generate Explanation ────────────────────────────────────────────
    explanation = await llm_provider.generate_explanation({
        "decision": decision_result.decision,
        "trust_score": trust.score,
        "plausibility_passed": plausibility.passed,
        "contradiction_level": contradiction.level,
        "speaker_status": speaker_status,
    })

    completed_at = datetime.now(timezone.utc)

    # ── STEP 10: Create Statement ────────────────────────────────────────────────
    statement = await statement_service.create_statement(
        db=db,
        shop_id=shop_id,
        actor_id=actor_id,
        voice_profile_id=voice_profile_id,
        product_id=product_id,
        speaker_status=speaker_status,
        speaker_confidence=speaker_confidence,
        transcript=transcript,
        raw_claim=raw_claim,
        quantity=quantity,
        unit=unit,
        direction=direction,
        decision=decision_result.decision,
        source=source or "MOBILE_WEB",
    )

    # ── STEP 11: Create Processing Record ───────────────────────────────────────
    await statement_service.create_statement_processing(
        db=db,
        statement_id=statement.id,
        asr_provider=asr_provider_name,
        asr_confidence=asr_confidence,
        asr_language=asr_language,
        speaker_model_version=get_speaker_provider_version(),
        speaker_confidence=speaker_confidence,
        llm_provider=llm_provider.provider_name,
        trust_score=trust.score,
        trust_result=trust.components,
        plausibility_passed=plausibility.passed,
        plausibility_result=plausibility.to_dict(),
        contradiction_detected=contradiction.level != "NO_CONFLICT",
        contradiction_result=contradiction.to_dict(),
        decision_explanation=explanation,
        started_at=started_at,
        completed_at=completed_at,
    )

    # ── STEP 12: Queue Review if Needed ─────────────────────────────────────────
    review = await statement_service.create_review_if_needed(db, statement)

    # ── STEP 13: Update Trust History ───────────────────────────────────────────
    if actor_id:
        await record_trust_event(
            db=db,
            shop_id=shop_id,
            user_id=actor_id,
            new_score=trust.score,
            trigger_event="STATEMENT_PROCESSED",
            statement_id=statement.id,
            reason=f"Statement processed with decision: {decision_result.decision}",
        )

    await db.commit()

    return {
        "success": True,
        "data": {
            "statement_id": str(statement.id),
            "status": statement.status.value,
            "decision": statement.decision.value if statement.decision else None,
            "transcript": transcript,
            "speaker_status": speaker_status,
            "speaker_confidence": speaker_confidence,
            "actor_id": str(actor_id) if actor_id else None,
            "product_id": str(product_id) if product_id else None,
            "quantity": quantity,
            "unit": unit,
            "direction": direction,
            "trust_score": trust.score,
            "plausibility_passed": plausibility.passed,
            "contradiction_level": contradiction.level,
            "explanation": explanation,
            "review_id": str(review.id) if review else None,
            "raw_claim": raw_claim,
        },
    }


def get_speaker_provider_version() -> str:
    from app.providers.speaker_provider import get_speaker_provider
    return get_speaker_provider().model_version
