"""Fail-closed media provider registry for W19."""
from __future__ import annotations
from .contracts import MediaCapability,MediaProvider,MediaProviderError
_PROVIDERS: dict[str,MediaProvider]={}
def register_provider(name:str,provider:MediaProvider)->None:
    key=name.strip().lower()
    if not key: raise ValueError("provider name required")
    _PROVIDERS[key]=provider
def get_media_provider(name:str,capability:MediaCapability)->MediaProvider:
    provider=_PROVIDERS.get(name.strip().lower())
    if provider is None: raise MediaProviderError(f"unsupported media provider: {name}")
    if not provider.supports(capability): raise MediaProviderError(f"provider lacks capability: {capability.value}")
    return provider
def clear_registry()->None: _PROVIDERS.clear()
