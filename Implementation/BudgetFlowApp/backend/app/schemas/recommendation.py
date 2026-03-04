import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskAnswers(BaseModel):
    """Five-question risk profile questionnaire. Each answer 1-5 (low to high risk tolerance)."""
    market_drop_reaction: int = Field(3, ge=1, le=5, description="1=sell all, 5=buy more")
    investment_experience: int = Field(2, ge=1, le=5, description="1=none, 5=expert")
    income_stability: int = Field(3, ge=1, le=5, description="1=unstable, 5=very stable")
    loss_tolerance_pct: int = Field(2, ge=1, le=5, description="1=0%, 5=30%+")
    goal_priority: int = Field(3, ge=1, le=5, description="1=preserve capital, 5=max growth")


class RiskProfileCreate(BaseModel):
    answers: RiskAnswers
    horizon_months: int = Field(60, ge=6, le=360)
    liquidity_need: Literal["low", "moderate", "high"] = "moderate"


class RiskProfileRead(BaseModel):
    score: int
    horizon_months: int
    liquidity_need: str
    answers_json: Optional[dict] = None
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RunRequest(BaseModel):
    risk_profile: Optional[RiskProfileCreate] = None
    horizon_months: Optional[int] = Field(None, ge=6, le=360)

    @model_validator(mode="after")
    def check_horizon(self) -> "RunRequest":
        if self.horizon_months is not None and self.horizon_months < 6:
            raise ValueError("horizon_months must be >= 6")
        return self


class RecommendationItemRead(BaseModel):
    id: uuid.UUID
    priority: int
    type: str
    title: str
    details: Optional[dict] = None
    confidence: float
    model_config = ConfigDict(from_attributes=True)


class ProjectionPoint(BaseModel):
    month: int
    median: float
    p10: float
    p90: float


class AllocationSlice(BaseModel):
    asset: str
    ticker: str
    pct: float
    rationale: str


class GateResult(BaseModel):
    code: str
    passed: bool
    reason: str


class RiskDetail(BaseModel):
    score: int
    bucket: str
    horizon_adjustment: int = 0


class SimulationAssumptions(BaseModel):
    expected_return: float
    volatility: float
    paths: int
    step: str = "monthly"
    inflation_assumed: float = 0.025
    buffer_factor: float = 0.80


class RunOutputs(BaseModel):
    needs_profile: bool = False
    risk_bucket: Optional[str] = None
    risk_score: Optional[int] = None
    monthly_spending_avg: float = 0.0
    emergency_fund_months: float = 0.0
    investable_monthly: float = 0.0
    cashflow_positive: bool = True
    safety_warnings: List[str] = []
    allocation: List[AllocationSlice] = []
    projection: List[ProjectionPoint] = []
    gates: List[GateResult] = []
    risk: Optional[RiskDetail] = None
    allocation_rationale: List[str] = []
    assumptions: Optional[SimulationAssumptions] = None


class RecommendationRunRead(BaseModel):
    id: uuid.UUID
    status: str
    inputs_snapshot: Optional[dict] = None
    outputs: Optional[RunOutputs] = None
    items: List[RecommendationItemRead] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecommendationRunListItem(BaseModel):
    id: uuid.UUID
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
