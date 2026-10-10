"""API contracts for World Mode one-time commerce."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated, Literal

from pydantic import model_validator


ShortKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]


class WorldCatalogueItemResponse(BaseModel):
    id: UUID
    code: str
    item_type: str
    name: str
    description: str | None
    price_options: dict
    is_free: bool
    lease_duration_days: int | None = None
    model_config = ConfigDict(from_attributes=True)


class WorldOrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_code: ShortKey
    currency: str = Field(pattern="^(IRR|USD|USDT|WORLD_CREDIT)$")
    payment_method: str = Field(pattern="^(manual_transfer|gateway|crypto|world_credit)$")
    payment_provider: str = Field(min_length=1, max_length=64)
    idempotency_key: ShortKey


class WorldPaymentSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_transaction_ref: str = Field(min_length=1, max_length=255)


class WorldPaymentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = Field(default=None, max_length=2000)


class WorldOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    buyer_user_id: UUID
    item_code_snapshot: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_provider: str
    provider_transaction_ref: str | None
    status: str
    payment_submitted_at: datetime | None
    approved_by_user_id: UUID | None
    approved_by_username: str | None
    approved_at: datetime | None
    activated_by_user_id: UUID | None
    activated_by_username: str | None
    activated_at: datetime | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldFeatureEntitlementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    item_code: str
    item_type: str
    source_order_id: UUID
    status: str
    activated_by_user_id: UUID | None
    activated_by_username: str | None
    activated_at: datetime
    revoked_at: datetime | None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldFeatureAccessResponse(BaseModel):
    item_code: str
    granted: bool
    access_source: str
    entitlement_id: UUID | None = None
    item_type: str | None = None


class WorldCommerceEventResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    order_id: UUID
    event_type: str
    actor_user_id: UUID | None
    actor_username: str | None
    from_status: str | None
    to_status: str | None
    details: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldSupportOrderSummary(BaseModel):
    id: UUID
    item_code_snapshot: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorldSupportEntitlementSummary(BaseModel):
    item_code: str
    item_type: str
    status: str
    activated_at: datetime
    revoked_at: datetime | None
    expires_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class WorldSupportDiagnosticsResponse(BaseModel):
    tenant_id: UUID
    order_counts_by_status: dict[str, int]
    active_entitlement_count: int
    recent_orders: list[WorldSupportOrderSummary]
    entitlements: list[WorldSupportEntitlementSummary]


class WorldCataloguePriceOption(BaseModel):
    """Server-managed price and allowed checkout choices for one currency."""
    model_config = ConfigDict(extra="forbid")
    amount: Decimal = Field(gt=0, max_digits=24, decimal_places=8)
    providers: list[ShortKey] = Field(min_length=1, max_length=12)
    payment_methods: list[Literal["manual_transfer", "gateway", "crypto"]] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def require_unique_choices(self):
        if len(set(self.providers)) != len(self.providers):
            raise ValueError("providers must be unique")
        if len(set(self.payment_methods)) != len(self.payment_methods):
            raise ValueError("payment_methods must be unique")
        return self


class WorldCatalogueAdminWriteRequest(BaseModel):
    """Full replacement/create payload; never accepts client-owned database fields."""
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")]
    item_type: Literal["room", "layout", "appearance", "personality", "furniture", "facility", "support"]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    description: str | None = Field(default=None, max_length=4000)
    price_options: dict[Literal["IRR", "USD", "USDT"], WorldCataloguePriceOption] = Field(default_factory=dict)
    is_free: bool = False
    is_active: bool = True
    lease_duration_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def validate_price_options(self):
        if self.is_free and self.price_options:
            raise ValueError("free catalogue items must not define paid price options")
        if not self.is_free and not self.price_options:
            raise ValueError("paid catalogue items require at least one configured currency")
        if self.item_type == "room" and not self.is_free and self.lease_duration_days is None:
            raise ValueError("paid room items require lease_duration_days")
        if self.item_type != "room" and self.lease_duration_days is not None:
            raise ValueError("lease_duration_days is only valid for room items")
        return self

class WorldRoomInventoryResponse(BaseModel):
    room_instance_id: UUID
    item_code: str
    status: str
    expires_at: datetime | None = None
    scene_config: dict = Field(default_factory=dict)


class WorldRoomInventoryAccessResponse(BaseModel):
    item_code: str
    granted: bool
    reason: str
    room_instance_id: UUID | None = None
    expires_at: datetime | None = None

class WorldRoomFurniturePlacement(BaseModel):
    """A bounded placement of a built-in, non-executable room prop."""
    model_config = ConfigDict(extra="forbid")
    placement_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    kind: Literal["desk", "chair", "plant", "cabinet", "meeting_table"]
    x: float = Field(ge=-3.5, le=3.5)
    z: float = Field(ge=-3.5, le=3.5)
    rotation: int = Field(default=0, ge=0, le=359)


class WorldRoomSceneConfig(BaseModel):
    """Versioned, bounded client-renderable room configuration; never an access grant."""
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    layout_preset: Literal["starter"] = "starter"
    furniture: list[WorldRoomFurniturePlacement] = Field(default_factory=list, max_length=40)

    @model_validator(mode="after")
    def validate_unique_placement_ids(self):
        ids = [item.placement_id for item in self.furniture]
        if len(ids) != len(set(ids)):
            raise ValueError("placement_id values must be unique")
        return self


class WorldRoomSceneConfigResponse(BaseModel):
    room_instance_id: UUID
    item_code: str
    scene_config: WorldRoomSceneConfig
    updated_at: datetime

