from __future__ import annotations
import pytest
from app.media.contracts import MediaCapability,MediaEvidenceStatus,MediaPolicy,MediaProviderError,SpeechToTextRequest,validate_policy
from app.media.deterministic import DeterministicMediaProvider
from app.media.registry import clear_registry,get_media_provider,register_provider
def test_consent_is_required():
    with pytest.raises(MediaProviderError): validate_policy(MediaPolicy("t",False))
def test_tenant_scope_is_required():
    with pytest.raises(MediaProviderError): validate_policy(MediaPolicy("",True))
def test_registry_fails_closed():
    clear_registry()
    with pytest.raises(MediaProviderError): get_media_provider("missing",MediaCapability.SPEECH_TO_TEXT)
@pytest.mark.asyncio
async def test_deterministic_provider_is_unverified():
    clear_registry(); register_provider("deterministic",DeterministicMediaProvider())
    out=await get_media_provider("deterministic",MediaCapability.SPEECH_TO_TEXT).speech_to_text(SpeechToTextRequest("r",MediaPolicy("tenant",True)))
    assert out.evidence_status is MediaEvidenceStatus.UNVERIFIED
