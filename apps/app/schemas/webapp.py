from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class WebAppAuthRequest(BaseModel):
    init_data: str | None = None
    dev_shared_secret: str | None = None


class WebAppUser(BaseModel):
    tg_id: int
    username: str | None = None


class WebAppAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: WebAppUser


class WebAppContextResponse(BaseModel):
    user: WebAppUser
    selected_design_id: int | None = None
    selected_design_name: str | None = None
    pricing_config_id: int | None = None


class SelectedDesignRequest(BaseModel):
    tattoo_id: int = Field(gt=0)


class SelectedDesignResponse(BaseModel):
    ok: bool
    selected_design_id: int


class PricingCalcRequest(BaseModel):
    style_id: int = Field(gt=0)
    body_zone: str = Field(min_length=1, max_length=50)
    promo_code: str | None = None


class PricingCalcResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pricing_config_id: int
    base_price: int
    min_price: int
    style_coefficient: Decimal
    body_zone_coefficient: Decimal
    raw_price: Decimal
    bounded_price: Decimal
    discount_multiplier: Decimal
    final_price: int
    rounding_policy: str
