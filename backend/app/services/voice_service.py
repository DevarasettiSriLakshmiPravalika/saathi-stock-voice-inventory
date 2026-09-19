"""
Voice enrollment and speaker identification service.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.voice_profile import VoiceProfile
from app.models.shop_member import ShopMember
from app.models.enums import VoiceEnrollmentStatus, MembershipStatus
from app.providers.speaker_provider import get_speaker_provider, SpeakerIdentificationResult

SIMILARITY_THRESHOLD_IDENTIFIED = 0.75
SIMILARITY_THRESHOLD_LOW_CONFIDENCE = 0.5


async def enroll_voice(
    db: AsyncSession,
    user_id: uuid.UUID,
    shop_id: uuid.UUID,
    audio_bytes: bytes,
    filename: str,
) -> VoiceProfile:
    """
    Extract embedding from audio and create/update voice profile.
    Embedding is stored securely and never returned through API.
    """
    provider = get_speaker_provider()
    result = await provider.extract_embedding(audio_bytes, filename)

    if not result.success:
        status = VoiceEnrollmentStatus.FAILED
        embedding = None
    elif result.quality_score < 0.5:
        status = VoiceEnrollmentStatus.LOW_QUALITY
        embedding = result.embedding
    else:
        status = VoiceEnrollmentStatus.ENROLLED
        embedding = result.embedding

    # Check for existing profile
    existing = await db.execute(
        select(VoiceProfile).where(
            VoiceProfile.user_id == user_id,
            VoiceProfile.shop_id == shop_id,
        )
    )
    profile = existing.scalar_one_or_none()

    if profile:
        profile.enrollment_status = status
        profile.quality_score = result.quality_score
        profile.audio_duration_seconds = result.duration_seconds
        profile.model_version = result.model_version
        # embedding stored as JSONB list
        profile.embedding = {"vector": embedding} if embedding else None
    else:
        profile = VoiceProfile(
            user_id=user_id,
            shop_id=shop_id,
            enrollment_status=status,
            quality_score=result.quality_score,
            audio_duration_seconds=result.duration_seconds,
            model_version=result.model_version,
            embedding={"vector": embedding} if embedding else None,
        )
        db.add(profile)

    await db.flush()
    return profile


async def identify_speaker(
    db: AsyncSession,
    shop_id: uuid.UUID,
    audio_bytes: bytes,
    filename: str,
) -> SpeakerIdentificationResult:
    """
    Compare audio against all enrolled members of the shop.
    Returns identification result with safe metadata only (no raw embeddings).
    """
    provider = get_speaker_provider()

    # Extract embedding from incoming audio
    embed_result = await provider.extract_embedding(audio_bytes, filename)
    if not embed_result.success:
        return SpeakerIdentificationResult(
            user_id=None,
            confidence=0.0,
            status="UNKNOWN",
        )

    incoming_embedding = embed_result.embedding

    # Get all enrolled profiles for this shop
    result = await db.execute(
        select(VoiceProfile).where(
            VoiceProfile.shop_id == shop_id,
            VoiceProfile.enrollment_status == VoiceEnrollmentStatus.ENROLLED,
        )
    )
    profiles = result.scalars().all()

    if not profiles:
        return SpeakerIdentificationResult(
            user_id=None,
            confidence=0.0,
            status="UNKNOWN",
        )

    # Find best match
    best_similarity = 0.0
    best_profile = None

    for profile in profiles:
        if not profile.embedding or not profile.embedding.get("vector"):
            continue
        stored_embedding = profile.embedding["vector"]
        similarity = await provider.compute_similarity(incoming_embedding, stored_embedding)
        if similarity > best_similarity:
            best_similarity = similarity
            best_profile = profile

    if best_profile is None or best_similarity < SIMILARITY_THRESHOLD_LOW_CONFIDENCE:
        return SpeakerIdentificationResult(
            user_id=None,
            confidence=best_similarity,
            status="UNKNOWN",
        )
    elif best_similarity < SIMILARITY_THRESHOLD_IDENTIFIED:
        return SpeakerIdentificationResult(
            user_id=str(best_profile.user_id),
            confidence=best_similarity,
            status="LOW_CONFIDENCE",
            voice_profile_id=str(best_profile.id),
        )
    else:
        return SpeakerIdentificationResult(
            user_id=str(best_profile.user_id),
            confidence=best_similarity,
            status="IDENTIFIED",
            voice_profile_id=str(best_profile.id),
        )
