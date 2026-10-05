"""Deterministic test-only media provider; never represents external execution."""
from .contracts import MediaCapability,MediaEvidenceStatus,MediaProvider,SpeechToTextRequest,SpeechToTextResult,TextToSpeechRequest,TextToSpeechResult,validate_policy
class DeterministicMediaProvider(MediaProvider):
    name="deterministic"
    def supports(self,capability): return capability in {MediaCapability.SPEECH_TO_TEXT,MediaCapability.TEXT_TO_SPEECH}
    async def speech_to_text(self,request):
        validate_policy(request.policy)
        return SpeechToTextResult("[deterministic transcript]",self.name,"fixture",0,0.0,MediaEvidenceStatus.UNVERIFIED)
    async def text_to_speech(self,request):
        validate_policy(request.policy)
        return TextToSpeechResult(None,self.name,"fixture",None,0,0.0,MediaEvidenceStatus.UNVERIFIED)
