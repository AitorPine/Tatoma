from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# --- AUTH ---
class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = Field(default="planner", pattern="^(admin|planner|viewer)$")


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


# --- WORKERS ---
class WorkerAbsenceItem(BaseModel):
    week: str
    hours: float = Field(..., gt=0)
    reason: str = "vacaciones"  # vacaciones, baja


class WorkerCreate(BaseModel):
    name: str
    station_id: Optional[str] = None
    skills: List[str] = ["general"]


class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    station_id: Optional[str] = None
    skills: Optional[List[str]] = None


class WorkerOut(BaseModel):
    id: int
    name: str
    station_id: Optional[str]
    skills: List[str]
    absences: List[WorkerAbsenceItem]


class WorkerAbsencesUpdate(BaseModel):
    absences: List[WorkerAbsenceItem]


# --- PLANT, AREAS, WORKFLOW & STATIONS ---
class StationPositionItem(BaseModel):
    id: str
    x: int
    y: int
    w: int
    h: int


class PlantLayoutUpdate(BaseModel):
    name: Optional[str] = None
    cols: int = Field(..., gt=0)
    rows: int = Field(..., gt=0)
    positions: Optional[List[StationPositionItem]] = None


class StationCreate(BaseModel):
    id: str
    name: str
    area: str
    x: int = 0
    y: int = 0
    w: int = 2
    h: int = 2
    workers: int = 2
    shifts: int = 1
    max_shifts: int = 2
    hoursPerShift: float = 8.0
    unitsPerShift: Optional[int] = None
    status: str = "active"  # active, stopped, maintenance
    skills: List[str] = ["general"]


class StationUpdate(BaseModel):
    name: Optional[str] = None
    area: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    workers: Optional[int] = None
    shifts: Optional[int] = None
    max_shifts: Optional[int] = None
    hoursPerShift: Optional[float] = None
    unitsPerShift: Optional[int] = None
    status: Optional[str] = None
    skills: Optional[List[str]] = None


class StationStatusPatch(BaseModel):
    status: str = Field(..., pattern="^(active|stopped|maintenance)$")


class StationSkillsPut(BaseModel):
    skills: List[str]


class AreaItem(BaseModel):
    id: str
    name: str
    color: str = "#3b82f6"
    hourly_cost: float = 28.0
    overtime_hourly_cost: float = 42.0
    subcontract_hourly_cost: float = 38.0
    subcontract_fixed_logistics: float = 250.0
    subcontract_lead_time_weeks: int = 1


class WorkflowStepItem(BaseModel):
    step_order: int
    area_id: str
    name: str
    offset_weeks_before_delivery: int = Field(..., ge=0)
    is_optional: bool = False


# --- CAPACITY ---
class CapacityAdjustmentItem(BaseModel):
    id: Optional[int] = None
    week: str
    area: str
    station_id: Optional[str] = None
    hours_delta: float
    reason: str  # vacaciones, baja, averia, horas_extra


class CapacityAdjustmentsPut(BaseModel):
    adjustments: List[CapacityAdjustmentItem]


# --- ORDERS ---
class OrderCreate(BaseModel):
    code: str
    client: str
    quantity: int = Field(..., gt=0)
    current_week: str = "2026-W01"
    delivery_week: str
    lead_time_weeks: int = Field(default=2, ge=0)
    required_skill: str = "general"
    hours_per_unit: Dict[str, float]  # {"soldadura": 12.0, "pintura": 2.5, "montaje": 6.0}
    active_phases: Optional[List[str]] = None  # Permite omitir pintura/montaje o añadir nueva fase
    status: str = "confirmed"


class OrderUpdate(BaseModel):
    client: Optional[str] = None
    quantity: Optional[int] = None
    delivery_week: Optional[str] = None
    lead_time_weeks: Optional[int] = None
    required_skill: Optional[str] = None
    hours_per_unit: Optional[Dict[str, float]] = None
    active_phases: Optional[List[str]] = None
    status: Optional[str] = None


# --- SIMULATIONS & ENGINE ---
class ConflictItem(BaseModel):
    week: str
    area: str
    station_id: Optional[str] = None
    required_hours: float
    available_hours: float
    overload_hours: float
    occupancy_pct: float
    unit_limit_exceeded: bool = False
    overload_units: int = 0
    message: str


class ProposedAllocationItem(BaseModel):
    week: str
    area: str
    station_id: str
    allocated_hours: float
    allocated_units: float
    is_subcontracted: bool = False


class StrategySuggestion(BaseModel):
    strategy_id: str
    strategy_code: str
    title: str
    viable: bool
    proposed_delivery_week: str
    delay_weeks: int
    extra_cost_eur: float
    is_subcontracting_profitable: Optional[bool] = None
    description: str
    actions: List[str]
    allocations: List[ProposedAllocationItem]
    capacity_adjustments_to_create: List[CapacityAdjustmentItem] = []


class AIRecommendationOut(BaseModel):
    recommended_strategy_code: str
    summary: str
    profitability_reasoning: str
    risk_level: str
    generated_by: str


class SimulationEvaluateResponse(BaseModel):
    viable: bool
    lead_time_ok: bool
    earliest_allowed_start_week: str
    conflicts: List[ConflictItem]
    baseline_allocations: List[ProposedAllocationItem]
    suggestions: List[StrategySuggestion]
    ai_advisor: AIRecommendationOut


class SimulationApplyRequest(BaseModel):
    order: OrderCreate
    selected_strategy_code: str
    allocations: List[ProposedAllocationItem]
    capacity_adjustments_to_create: List[CapacityAdjustmentItem] = []
    final_delivery_week: Optional[str] = None
