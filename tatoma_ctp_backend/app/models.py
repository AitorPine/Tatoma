from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from app.database import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="planner")  # admin, planner, viewer


class PlantModel(Base):
    __tablename__ = "plants"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cols = Column(Integer, default=12)
    rows = Column(Integer, default=8)


class AreaModel(Base):
    __tablename__ = "areas"
    id = Column(String, primary_key=True, index=True)  # ej: soldadura, pintura, montaje
    name = Column(String, nullable=False)
    color = Column(String, default="#3b82f6")
    hourly_cost = Column(Float, default=28.0)
    overtime_hourly_cost = Column(Float, default=42.0)
    subcontract_hourly_cost = Column(Float, default=38.0)
    subcontract_fixed_logistics = Column(Float, default=250.0)
    subcontract_lead_time_weeks = Column(Integer, default=1)


class WorkflowStepModel(Base):
    __tablename__ = "workflow_steps"
    id = Column(Integer, primary_key=True, index=True)
    step_order = Column(Integer, nullable=False)
    area_id = Column(String, ForeignKey("areas.id"), nullable=False)
    name = Column(String, nullable=False)
    offset_weeks_before_delivery = Column(Integer, nullable=False)
    is_optional = Column(Boolean, default=False)


class StationModel(Base):
    __tablename__ = "stations"
    id = Column(String, primary_key=True, index=True)  # P1..P7, PINT-1, M1, M2
    plant_id = Column(String, ForeignKey("plants.id"), default="armentera")
    name = Column(String, nullable=False)
    area = Column(String, ForeignKey("areas.id"), nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    w = Column(Integer, default=2)
    h = Column(Integer, default=2)
    workers = Column(Integer, default=2)
    shifts = Column(Integer, default=1)
    max_shifts = Column(Integer, default=2)
    hours_per_shift = Column(Float, default=8.0)
    units_per_shift = Column(Integer, nullable=True)  # ej: 32 en pintura
    status = Column(String, default="active")  # active, stopped, maintenance
    skills_json = Column(Text, default='["general"]')


class WorkerModel(Base):
    __tablename__ = "workers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    station_id = Column(String, ForeignKey("stations.id"), nullable=True)
    skills_json = Column(Text, default='["general"]')
    absences_json = Column(Text, default="[]")  # [{"week": "2026-W08", "hours": 16, "reason": "vacaciones"}]


class CapacityAdjustmentModel(Base):
    __tablename__ = "capacity_adjustments"
    id = Column(Integer, primary_key=True, index=True)
    week = Column(String, index=True, nullable=False)  # "2026-W08"
    area = Column(String, nullable=False)
    station_id = Column(String, nullable=True)
    hours_delta = Column(Float, nullable=False)  # negativo resta capacidad, positivo suma horas extra
    reason = Column(String, nullable=False)  # vacaciones, baja, averia, horas_extra


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    client = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    current_week = Column(String, default="2026-W01")
    delivery_week = Column(String, nullable=False)
    lead_time_weeks = Column(Integer, default=2)
    required_skill = Column(String, default="general")
    hours_per_unit_json = Column(Text, nullable=False)  # {"soldadura": 10.0, "pintura": 2.0, "montaje": 5.0}
    active_phases_json = Column(Text, nullable=False)   # ["soldadura", "pintura", "montaje"]
    status = Column(String, default="confirmed")        # draft, confirmed


class OrderAllocationModel(Base):
    __tablename__ = "order_allocations"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    order_code = Column(String, nullable=False)
    client = Column(String, nullable=False)
    week = Column(String, index=True, nullable=False)
    area = Column(String, nullable=False)
    station_id = Column(String, nullable=False)
    allocated_hours = Column(Float, nullable=False)
    allocated_units = Column(Float, nullable=False)
    is_subcontracted = Column(Boolean, default=False)
