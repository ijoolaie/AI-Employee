"""Provider-neutral governed voice/visual capability contracts for W19."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class MediaCapability(str, Enum):
    SPEECH_TO_TEXT="speech_to_text"; TEXT_TO_SPEECH="text_to_speech"; VISUAL_RENDER="visual_render"
class MediaEvidenceStatus(str, Enum):
    VERIFIED="VERIFIED"; UNVERIFIED="UNVERIFIED"; UNKNOWN="UNKNOWN"; NOT_APPLICABLE="NOT_APPLICABLE"
class MediaSensitivity(str, Enum):
    STANDARD="standard"; SENSITIVE="sensitive"; RESTRICTED="restricted"

@dataclass(frozen=True)
class MediaPolicy:
    tenant_id: str
    consent_granted: bool
    sensitivity: MediaSensitivity = MediaSensitivity.STANDARD
    max_cost_tier: int = 0
@dataclass(frozen=True)
class SpeechToTextRequest:
    request_id: str; policy: MediaPolicy; language: str|None=None; audio_format: str|None=None; duration_seconds: float|None=None
@dataclass(frozen=True)
class SpeechToTextResult:
    transcript: str; provider: str; model: str; latency_ms: int; cost_usd: float; evidence_status: MediaEvidenceStatus
@dataclass(frozen=True)
class TextToSpeechRequest:
    request_id: str; policy: MediaPolicy; text: str; language: str|None=None; voice: str|None=None
@dataclass(frozen=True)
class TextToSpeechResult:
    audio_ref: str|None; provider: str; model: str; duration_seconds: float|None; latency_ms: int; cost_usd: float; evidence_status: MediaEvidenceStatus

class MediaProviderError(RuntimeError): pass
class MediaProvider:
    name: str
    def supports(self, capability: MediaCapability)->bool: raise NotImplementedError
    async def speech_to_text(self, request: SpeechToTextRequest)->SpeechToTextResult: raise MediaProviderError("speech_to_text unsupported")
    async def text_to_speech(self, request: TextToSpeechRequest)->TextToSpeechResult: raise MediaProviderError("text_to_speech unsupported")
def validate_policy(policy: MediaPolicy)->None:
    if not policy.tenant_id: raise MediaProviderError("tenant scope required")
    if not policy.consent_granted: raise MediaProviderError("explicit media consent required")
