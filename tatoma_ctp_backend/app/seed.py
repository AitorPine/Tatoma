import json
from sqlalchemy.orm import Session
from app.auth import hash_password
from app.models import (
    AreaModel,
    OrderAllocationModel,
    OrderModel,
    PlantModel,
    StationModel,
    UserModel,
    WorkerModel,
    WorkflowStepModel,
)


def seed_initial_data(db: Session):
    if db.query(UserModel).first():
        return

    # 1. Usuarios con roles: admin, planner, viewer
    users = [
        UserModel(username="admin", password_hash=hash_password("admin123"), full_name="Administrador Planta", role="admin"),
        UserModel(username="planner", password_hash=hash_password("planner123"), full_name="Planificador Producción", role="planner"),
        UserModel(username="viewer", password_hash=hash_password("viewer123"), full_name="Consultor Nave", role="viewer"),
    ]
    db.add_all(users)

    # 2. Planta principal
    plant = PlantModel(id="armentera", name="Planta Armentera - Monzón", cols=14, rows=8)
    db.add(plant)

    # 3. Áreas configurables con tarifas para rentabilidad de subcontratación vs horas extra
    areas = [
        AreaModel(
            id="soldadura",
            name="Soldadura",
            color="#f59e0b",
            hourly_cost=28.0,
            overtime_hourly_cost=44.0,
            subcontract_hourly_cost=39.0,
            subcontract_fixed_logistics=200.0,
            subcontract_lead_time_weeks=1,
        ),
        AreaModel(
            id="pintura",
            name="Pintura",
            color="#10b981",
            hourly_cost=30.0,
            overtime_hourly_cost=48.0,
            subcontract_hourly_cost=34.0,  # Ejemplo donde subcontratar pintura es muy competitivo
            subcontract_fixed_logistics=180.0,
            subcontract_lead_time_weeks=1,
        ),
        AreaModel(
            id="montaje",
            name="Montaje Final",
            color="#3b82f6",
            hourly_cost=27.0,
            overtime_hourly_cost=42.0,
            subcontract_hourly_cost=45.0,
            subcontract_fixed_logistics=300.0,
            subcontract_lead_time_weeks=1,
        ),
    ]
    db.add_all(areas)

    # 4. Flujo de trabajo (Workflow) editable
    workflow_steps = [
        WorkflowStepModel(step_order=1, area_id="soldadura", name="Fase Soldadura", offset_weeks_before_delivery=2, is_optional=False),
        WorkflowStepModel(step_order=2, area_id="pintura", name="Fase Pintura", offset_weeks_before_delivery=1, is_optional=True),
        WorkflowStepModel(step_order=3, area_id="montaje", name="Fase Montaje", offset_weeks_before_delivery=0, is_optional=True),
    ]
    db.add_all(workflow_steps)

    # 5. Puestos (7 líneas soldadura P1-P7, 1 Pintura con 32 uds/turno, 2 Montaje M1-M2)
    stations = [
        StationModel(id="P1", name="Soldadura P1", area="soldadura", x=1, y=1, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general", "unifeed", "estructura_pesada"]'),
        StationModel(id="P2", name="Soldadura P2", area="soldadura", x=3, y=1, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general", "unifeed"]'),
        StationModel(id="P3", name="Soldadura P3", area="soldadura", x=5, y=1, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general", "estructura_pesada"]'),
        StationModel(id="P4", name="Soldadura P4", area="soldadura", x=7, y=1, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general", "tolva"]'),
        StationModel(id="P5", name="Soldadura P5", area="soldadura", x=1, y=4, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general", "tolva"]'),
        StationModel(id="P6", name="Soldadura P6", area="soldadura", x=3, y=4, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general", "unifeed"]'),
        StationModel(id="P7", name="Soldadura P7", area="soldadura", x=5, y=4, w=2, h=2, workers=2, shifts=1, hours_per_shift=8.0, status="maintenance", skills_json='["general", "especial"]'),
        StationModel(id="PINT-1", name="Cabina Pintura", area="pintura", x=8, y=3, w=3, h=3, workers=2, shifts=1, hours_per_shift=8.0, units_per_shift=32, status="active", skills_json='["general"]'),
        StationModel(id="M1", name="Montaje Principal M1", area="montaje", x=11, y=1, w=3, h=3, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general"]'),
        StationModel(id="M2", name="Montaje Auxiliar M2", area="montaje", x=11, y=4, w=3, h=3, workers=2, shifts=1, hours_per_shift=8.0, status="active", skills_json='["general"]'),
    ]
    db.add_all(stations)

    # 6. Trabajadores de ejemplo con vacaciones individuales
    workers = [
        WorkerModel(name="Carlos Bosque", station_id="P1", skills_json='["general", "unifeed", "estructura_pesada"]', absences_json='[{"week": "2026-W08", "hours": 16, "reason": "vacaciones"}]'),
        WorkerModel(name="Javier Pueyo", station_id="P1", skills_json='["general", "unifeed"]', absences_json="[]"),
        WorkerModel(name="Miguel Castan", station_id="PINT-1", skills_json='["general"]', absences_json="[]"),
        WorkerModel(name="David Ferrer", station_id="M1", skills_json='["general"]', absences_json="[]"),
    ]
    db.add_all(workers)

    # 7. Pedidos iniciales para que el plano muestre barras segmentadas en 2026-W08
    order1 = OrderModel(
        code="PED-2026-001",
        client="AgroGanadera Huesca",
        quantity=4,
        current_week="2026-W05",
        delivery_week="2026-W10",
        lead_time_weeks=2,
        required_skill="unifeed",
        hours_per_unit_json=json.dumps({"soldadura": 15.0, "pintura": 12.0, "montaje": 15.0}),
        active_phases_json=json.dumps(["soldadura", "pintura", "montaje"]),
        status="confirmed",
    )
    order2 = OrderModel(
        code="PED-2026-002",
        client="Cooperativa Cinca",
        quantity=5,
        current_week="2026-W05",
        delivery_week="2026-W09",
        lead_time_weeks=2,
        required_skill="general",
        hours_per_unit_json=json.dumps({"soldadura": 12.0, "pintura": 10.0, "montaje": 12.0}),
        active_phases_json=json.dumps(["soldadura", "pintura", "montaje"]),
        status="confirmed",
    )
    db.add_all([order1, order2])
    db.flush()

    allocs = [
        OrderAllocationModel(order_id=order1.id, order_code=order1.code, client=order1.client, week="2026-W08", area="soldadura", station_id="P1", allocated_hours=60.0, allocated_units=4.0),
        OrderAllocationModel(order_id=order1.id, order_code=order1.code, client=order1.client, week="2026-W09", area="pintura", station_id="PINT-1", allocated_hours=48.0, allocated_units=4.0),
        OrderAllocationModel(order_id=order1.id, order_code=order1.code, client=order1.client, week="2026-W10", area="montaje", station_id="M1", allocated_hours=60.0, allocated_units=4.0),
        OrderAllocationModel(order_id=order2.id, order_code=order2.code, client=order2.client, week="2026-W07", area="soldadura", station_id="P2", allocated_hours=60.0, allocated_units=5.0),
        OrderAllocationModel(order_id=order2.id, order_code=order2.code, client=order2.client, week="2026-W08", area="pintura", station_id="PINT-1", allocated_hours=50.0, allocated_units=5.0),
        OrderAllocationModel(order_id=order2.id, order_code=order2.code, client=order2.client, week="2026-W09", area="montaje", station_id="M1", allocated_hours=60.0, allocated_units=5.0),
    ]
    db.add_all(allocs)
    db.commit()
