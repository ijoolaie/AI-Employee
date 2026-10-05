"""W19 real-stack contract boundary verification."""
from __future__ import annotations
import asyncio,os,sys
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)
from app.media.contracts import MediaCapability,MediaPolicy,MediaProviderError,SpeechToTextRequest,validate_policy
from app.media.deterministic import DeterministicMediaProvider
from app.media.registry import clear_registry,get_media_provider,register_provider
async def run():
    clear_registry()
    for policy in (MediaPolicy("",True),MediaPolicy("w19",False)):
        try: validate_policy(policy); raise AssertionError("policy did not fail closed")
        except MediaProviderError: pass
    try: get_media_provider("missing",MediaCapability.SPEECH_TO_TEXT); raise AssertionError("provider did not fail closed")
    except MediaProviderError: pass
    register_provider("deterministic",DeterministicMediaProvider())
    result=await get_media_provider("deterministic",MediaCapability.SPEECH_TO_TEXT).speech_to_text(SpeechToTextRequest("w19-e2e",MediaPolicy("tenant",True)))
    assert result.evidence_status.value=="UNVERIFIED"
    print("W19 PROVIDER FAIL-CLOSED PASS"); print("W19 TENANT+CONSENT POLICY PASS"); print("W19 FIXTURE EVIDENCE BOUNDARY PASS")
if __name__=="__main__": asyncio.run(run())
