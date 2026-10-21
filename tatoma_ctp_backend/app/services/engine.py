import json
import math
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import (
    AreaModel,
    CapacityAdjustmentModel,
    OrderAllocationModel,
    StationModel,
    WorkerModel,
    WorkflowStepModel,
)
from app.schemas import (
    CapacityAdjustmentItem,
    ConflictItem,
    OrderCreate,
    ProposedAllocationItem,
    SimulationEvaluateResponse,
    StrategySuggestion,
)
from app.utils_weeks import compare_weeks, parse_week, shift_week


class IndustrialPlanningEngine:
    def __init__(self, db: Session):
        self.db = db
        self.areas: Dict[str, AreaModel] = {a.id: a for a in db.query(AreaModel).all()}
        self.workflow: List[WorkflowStepModel] = (
            db.query(WorkflowStepModel).order_by(WorkflowStepModel.step_order.asc()).all()
        )
        self.stations: List[StationModel] = db.query(StationModel).all()
        self.workers: List[WorkerModel] = db.query(WorkerModel).all()
        self.adjustments: List[CapacityAdjustmentModel] = db.query(CapacityAdjustmentModel).all()
        self.allocations: List[OrderAllocationModel] = db.query(OrderAllocationModel).all()

    def get_station_skills(self, station: StationModel) -> List[str]:
        try:
            return json.loads(station.skills_json or '["general"]')
        except Exception:
            return ["general"]

    def get_station_net_capacity(self, station: StationModel, week: str) -> Tuple[float, Optional[int]]:
        """
        Devuelve (horas_netas_disponibles, max_unidades_semana) para un puesto y semana.
        Descuenta paradas, ausencias individuales de trabajadores y ajustes por avería/baja/vacaciones.
        """
        if station.status != "active":
            return 0.0, 0 if station.units_per_shift else None

        working_days = 5
        base_hours = station.workers * station.shifts * station.hours_per_shift * working_days

        # 1. Ausencias individuales de trabajadores asignados a este puesto
        worker_absence_hours = 0.0
        for w in self.workers:
            if w.station_id == station.id:
                try:
                    abs_list = json.loads(w.absences_json or "[]")
                    for a in abs_list:
                        if parse_week(a.get("week", "")) == parse_week(week):
                            worker_absence_hours += float(a.get("hours", 0.0))
                except Exception:
                    pass

        # 2. Ajustes de capacidad directos al puesto o repartidos en el área
        station_adj_hours = 0.0
        area_stations = [s for s in self.stations if s.area == station.area and s.status == "active"]
        area_count = max(1, len(area_stations))

        for adj in self.adjustments:
            if parse_week(adj.week) == parse_week(week):
                if adj.station_id == station.id:
                    station_adj_hours += adj.hours_delta
                elif not adj.station_id and adj.area == station.area:
                    station_adj_hours += adj.hours_delta / area_count

        net_hours = max(0.0, round(base_hours - worker_absence_hours + station_adj_hours, 2))
        max_units = None
        if station.units_per_shift is not None and station.units_per_shift > 0:
            # Si hay horas extra autorizadas, ampliamos proporcionalmente la capacidad de unidades
            effective_shifts = net_hours / max(1.0, (station.workers * station.hours_per_shift))
            max_units = int(round(effective_shifts * station.units_per_shift))

        return net_hours, max_units

    def get_station_committed_load(self, station_id: str, week: str) -> Tuple[float, float]:
        """Devuelve (horas_comprometidas, unidades_comprometidas) en una estación y semana."""
        hrs = 0.0
        units = 0.0
        target_yw = parse_week(week)
        for alloc in self.allocations:
            if not alloc.is_subcontracted and alloc.station_id == station_id and parse_week(alloc.week) == target_yw:
                hrs += alloc.allocated_hours
                units += alloc.allocated_units
        return round(hrs, 2), round(units, 2)

    def get_compatible_stations(self, area_id: str, required_skill: str) -> List[StationModel]:
        compat = []
        for s in self.stations:
            if s.area == area_id and s.status == "active":
                skills = self.get_station_skills(s)
                if "general" in skills or required_skill in skills or required_skill == "general":
                    compat.append(s)
        return compat

    def get_active_workflow_steps(self, order: OrderCreate) -> List[WorkflowStepModel]:
        active_set = set(order.active_phases) if order.active_phases else set(order.hours_per_unit.keys())
        steps = [
            step for step in self.workflow
            if step.area_id in active_set and order.hours_per_unit.get(step.area_id, 0.0) > 0
        ]
        # Si el usuario envió un área nueva que aún no estaba en workflow_steps, la incluimos al vuelo
        existing_areas = {s.area_id for s in steps}
        for idx, (area_id, hpu) in enumerate(order.hours_per_unit.items()):
            if hpu > 0 and area_id in active_set and area_id not in existing_areas:
                steps.append(
                    WorkflowStepModel(
                        step_order=100 + idx,
                        area_id=area_id,
                        name=area_id.capitalize(),
                        offset_weeks_before_delivery=0,
                        is_optional=False,
                    )
                )
        return sorted(steps, key=lambda x: x.step_order)

    def evaluate_baseline(
        self, order: OrderCreate, target_delivery_week: Optional[str] = None
    ) -> Tuple[bool, str, List[ConflictItem], List[ProposedAllocationItem]]:
        delivery_w = target_delivery_week or order.delivery_week
        earliest_start_w = shift_week(order.current_week, order.lead_time_weeks)
        steps = self.get_active_workflow_steps(order)

        conflicts: List[ConflictItem] = []
        allocations: List[ProposedAllocationItem] = []
        lead_time_ok = True

        for step in steps:
            phase_week = shift_week(delivery_w, -step.offset_weeks_before_delivery)
            req_hours = round(order.quantity * order.hours_per_unit.get(step.area_id, 0.0), 2)

            if compare_weeks(phase_week, earliest_start_w) < 0:
                lead_time_ok = False
                conflicts.append(
                    ConflictItem(
                        week=phase_week,
                        area=step.area_id,
                        station_id=None,
                        required_hours=req_hours,
                        available_hours=0.0,
                        overload_hours=req_hours,
                        occupancy_pct=999.0,
                        message=(
                            f"Incumplimiento de Plazo Previo (Lead Time): La fase '{step.name}' debería iniciar en "
                            f"{phase_week}, pero el material/diseño no está listo hasta {earliest_start_w}."
                        ),
                    )
                )

            compat_stations = self.get_compatible_stations(step.area_id, order.required_skill)
            if not compat_stations:
                conflicts.append(
                    ConflictItem(
                        week=phase_week,
                        area=step.area_id,
                        station_id=None,
                        required_hours=req_hours,
                        available_hours=0.0,
                        overload_hours=req_hours,
                        occupancy_pct=999.0,
                        message=f"No existen estaciones activas en '{step.area_id}' con la habilidad '{order.required_skill}'.",
                    )
                )
                continue

            # Calcular holgura disponible en las estaciones compatibles en phase_week
            station_slacks = []
            total_avail_hrs = 0.0
            total_comm_hrs = 0.0
            total_max_units = 0
            total_comm_units = 0
            has_unit_limit = False

            for st in compat_stations:
                net_h, max_u = self.get_station_net_capacity(st, phase_week)
                comm_h, comm_u = self.get_station_committed_load(st.id, phase_week)
                slack_h = max(0.0, net_h - comm_h)
                station_slacks.append((st, slack_h, net_h, comm_h, max_u, comm_u))
                total_avail_hrs += net_h
                total_comm_hrs += comm_h
                if max_u is not None:
                    has_unit_limit = True
                    total_max_units += max_u
                    total_comm_units += int(comm_u)

            total_free_hrs = round(sum(x[1] for x in station_slacks), 2)
            unit_exceeded = has_unit_limit and ((total_comm_units + order.quantity) > total_max_units)
            overload_u = max(0, (total_comm_units + order.quantity) - total_max_units) if has_unit_limit else 0

            if req_hours > total_free_hrs or unit_exceeded:
                overload_h = round(max(0.0, req_hours - total_free_hrs), 2)
                occ_pct = (
                    round(((total_comm_hrs + req_hours) / total_avail_hrs) * 100.0, 1)
                    if total_avail_hrs > 0
                    else 999.0
                )
                if unit_exceeded and total_max_units > 0:
                    occ_pct = max(occ_pct, round(((total_comm_units + order.quantity) / total_max_units) * 100.0, 1))

                conflicts.append(
                    ConflictItem(
                        week=phase_week,
                        area=step.area_id,
                        station_id=compat_stations[0].id if len(compat_stations) == 1 else None,
                        required_hours=req_hours,
                        available_hours=total_free_hrs,
                        overload_hours=overload_h,
                        occupancy_pct=occ_pct,
                        unit_limit_exceeded=unit_exceeded,
                        overload_units=overload_u,
                        message=(
                            f"Cuello de botella en {step.name} ({phase_week}): faltan {overload_h}h "
                            + (f"y se supera el límite en {overload_u} uds/turno." if unit_exceeded else "disponibles.")
                        ),
                    )
                )
            else:
                # Reparto inteligente proporcional a la holgura real de las líneas habilitadas
                rem = req_hours
                hpu = order.hours_per_unit.get(step.area_id, 1.0)
                for st, slack_h, _, _, _, _ in sorted(station_slacks, key=lambda x: x[1], reverse=True):
                    if rem <= 0 or slack_h <= 0:
                        break
                    take = round(min(rem, slack_h), 2)
                    rem = round(rem - take, 2)
                    allocations.append(
                        ProposedAllocationItem(
                            week=phase_week,
                            area=step.area_id,
                            station_id=st.id,
                            allocated_hours=take,
                            allocated_units=round(take / hpu, 2),
                            is_subcontracted=False,
                        )
                    )

        return lead_time_ok, earliest_start_w, conflicts, allocations

    def generate_5_strategies(
        self, order: OrderCreate, conflicts: List[ConflictItem], earliest_start_w: str
    ) -> List[StrategySuggestion]:
        suggestions: List[StrategySuggestion] = []
        steps = self.get_active_workflow_steps(order)

        # -------------------------------------------------------------------------
        # ESTRATEGIA 1: Rebalanceo Multi-Línea por Habilidades (SKILL_REALLOCATION)
        # -------------------------------------------------------------------------
        lead_ok, _, base_conflicts, base_allocs = self.evaluate_baseline(order)
        s1_viable = lead_ok and len(base_conflicts) == 0
        suggestions.append(
            StrategySuggestion(
                strategy_id="S1",
                strategy_code="SKILL_REALLOCATION",
                title="1. Rebalanceo entre Puestos Habilitados (Skills)",
                viable=s1_viable,
                proposed_delivery_week=order.delivery_week,
                delay_weeks=0,
                extra_cost_eur=0.0,
                description=(
                    "Reparte la carga en la misma semana exclusivamente entre las líneas activas que "
                    f"poseen la habilitación técnica '{order.required_skill}'."
                ),
                actions=["Redistribuir lote entre líneas compatibles con holgura sin coste adicional."],
                allocations=base_allocs if s1_viable else [],
            )
        )

        # -------------------------------------------------------------------------
        # ESTRATEGIA 2: Partición de Lote y Nivelado hacia Atrás (BATCH_SPLITTING_AND_LEVELING)
        # -------------------------------------------------------------------------
        s2_allocs: List[ProposedAllocationItem] = []
        s2_viable = True
        for step in steps:
            target_w = shift_week(order.delivery_week, -step.offset_weeks_before_delivery)
            if compare_weeks(target_w, earliest_start_w) < 0:
                s2_viable = False
                break

            req_hours = round(order.quantity * order.hours_per_unit.get(step.area_id, 0.0), 2)
            hpu = order.hours_per_unit.get(step.area_id, 1.0)
            compat_stations = self.get_compatible_stations(step.area_id, order.required_skill)

            rem = req_hours
            curr_w = target_w
            # Retrocede desde la semana objetivo de la fase hasta earliest_start_w
            while compare_weeks(curr_w, earliest_start_w) >= 0 and rem > 0:
                for st in compat_stations:
                    net_h, max_u = self.get_station_net_capacity(st, curr_w)
                    comm_h, comm_u = self.get_station_committed_load(st.id, curr_w)
                    slack_h = max(0.0, net_h - comm_h)
                    if max_u is not None:
                        free_u = max(0, max_u - int(comm_u))
                        slack_h = min(slack_h, free_u * hpu)
                    if slack_h > 0 and rem > 0:
                        take = round(min(slack_h, rem), 2)
                        rem = round(rem - take, 2)
                        s2_allocs.append(
                            ProposedAllocationItem(
                                week=curr_w,
                                area=step.area_id,
                                station_id=st.id,
                                allocated_hours=take,
                                allocated_units=round(take / hpu, 2),
                                is_subcontracted=False,
                            )
                        )
                curr_w = shift_week(curr_w, -1)

            if rem > 0:
                s2_viable = False
                break

        suggestions.append(
            StrategySuggestion(
                strategy_id="S2",
                strategy_code="BATCH_SPLITTING_AND_LEVELING",
                title="2. Partir Lote y Adelantar a Semanas Previas (Buffer)",
                viable=s2_viable,
                proposed_delivery_week=order.delivery_week,
                delay_weeks=0,
                extra_cost_eur=0.0,
                description=(
                    f"Divide el pedido en sub-lotes aprovechando huecos libres desde {earliest_start_w} "
                    f"hasta {order.delivery_week}, respetando el plazo de aprovisionamiento."
                ),
                actions=["Partir el lote en semanas previas con baja ocupación y almacenar en pulmón intermedio."],
                allocations=s2_allocs if s2_viable else [],
            )
        )

        # -------------------------------------------------------------------------
        # ESTRATEGIA 3: Cobertura con Horas Extra / Turnos Adicionales (OVERTIME_AND_EXTRA_SHIFTS)
        # -------------------------------------------------------------------------
        s3_viable = compare_weeks(
            shift_week(order.delivery_week, -(steps[0].offset_weeks_before_delivery if steps else 0)),
            earliest_start_w,
        ) >= 0
        s3_extra_cost = 0.0
        s3_adjustments: List[CapacityAdjustmentItem] = []
        s3_actions: List[str] = []
        s3_allocs: List[ProposedAllocationItem] = []

        if s3_viable:
            for step in steps:
                phase_w = shift_week(order.delivery_week, -step.offset_weeks_before_delivery)
                compat = self.get_compatible_stations(step.area_id, order.required_skill)
                if not compat:
                    s3_viable = False
                    break
                req_h = round(order.quantity * order.hours_per_unit.get(step.area_id, 0.0), 2)
                hpu = order.hours_per_unit.get(step.area_id, 1.0)
                area_cfg = self.areas.get(step.area_id)
                ot_rate = area_cfg.overtime_hourly_cost if area_cfg else 42.0

                free_h = sum(
                    max(0.0, self.get_station_net_capacity(st, phase_w)[0] - self.get_station_committed_load(st.id, phase_w)[0])
                    for st in compat
                )
                deficit_h = round(max(0.0, req_h - free_h), 2)

                # Si la limitación viene por unitsPerShift (ej. Pintura), traducimos las unidades extra a horas de turno
                for st in compat:
                    _, max_u = self.get_station_net_capacity(st, phase_w)
                    _, comm_u = self.get_station_committed_load(st.id, phase_w)
                    if max_u is not None and (comm_u + order.quantity) > max_u:
                        extra_u = (comm_u + order.quantity) - max_u
                        shifts_needed = math.ceil(extra_u / (st.units_per_shift or 32))
                        hours_for_unit_shifts = shifts_needed * st.workers * st.hours_per_shift
                        deficit_h = max(deficit_h, hours_for_unit_shifts)

                if deficit_h > 0:
                    target_st = compat[0]
                    s3_extra_cost += round(deficit_h * ot_rate, 2)
                    s3_adjustments.append(
                        CapacityAdjustmentItem(
                            week=phase_w,
                            area=step.area_id,
                            station_id=target_st.id,
                            hours_delta=deficit_h,
                            reason="horas_extra",
                        )
                    )
                    s3_actions.append(
                        f"Habilitar +{deficit_h}h extra / turno adicional en {target_st.id} ({step.name}) en {phase_w} (+{deficit_h * ot_rate:.2f} EUR)."
                    )

                s3_allocs.append(
                    ProposedAllocationItem(
                        week=phase_w,
                        area=step.area_id,
                        station_id=compat[0].id,
                        allocated_hours=req_h,
                        allocated_units=order.quantity,
                        is_subcontracted=False,
                    )
                )

        suggestions.append(
            StrategySuggestion(
                strategy_id="S3",
                strategy_code="OVERTIME_AND_EXTRA_SHIFTS",
                title="3. Cubrir con Horas Extra o Turnos Adicionales",
                viable=s3_viable and len(s3_actions) > 0,
                proposed_delivery_week=order.delivery_week,
                delay_weeks=0,
                extra_cost_eur=round(s3_extra_cost, 2),
                description=f"Amplía la capacidad interna en las semanas críticas con un coste extra de {s3_extra_cost:.2f} EUR.",
                actions=s3_actions or ["No requiere horas extra o viola el plazo previo de materiales."],
                allocations=s3_allocs if s3_viable else [],
                capacity_adjustments_to_create=s3_adjustments,
            )
        )

        # -------------------------------------------------------------------------
        # ESTRATEGIA 4: Subcontratación Selectiva de la Fase Cuello de Botella (PHASE_SUBCONTRACTING)
        # -------------------------------------------------------------------------
        s4_viable = compare_weeks(
            shift_week(order.delivery_week, -(steps[0].offset_weeks_before_delivery if steps else 0)),
            earliest_start_w,
        ) >= 0
        s4_cost = 0.0
        s4_actions: List[str] = []
        s4_allocs: List[ProposedAllocationItem] = []

        if s4_viable:
            for step in steps:
                phase_w = shift_week(order.delivery_week, -step.offset_weeks_before_delivery)
                compat = self.get_compatible_stations(step.area_id, order.required_skill)
                req_h = round(order.quantity * order.hours_per_unit.get(step.area_id, 0.0), 2)
                hpu = order.hours_per_unit.get(step.area_id, 1.0)
                area_cfg = self.areas.get(step.area_id)

                free_h = sum(
                    max(0.0, self.get_station_net_capacity(st, phase_w)[0] - self.get_station_committed_load(st.id, phase_w)[0])
                    for st in compat
                )
                # Comprobar también límite de unidades en pintura
                free_units_h = req_h
                for st in compat:
                    _, max_u = self.get_station_net_capacity(st, phase_w)
                    _, comm_u = self.get_station_committed_load(st.id, phase_w)
                    if max_u is not None:
                        avail_u = max(0, max_u - int(comm_u))
                        free_units_h = min(free_units_h, avail_u * hpu)

                usable_internal_h = round(min(req_h, free_h, free_units_h), 2)
                subcontract_h = round(max(0.0, req_h - usable_internal_h), 2)

                if usable_internal_h > 0 and compat:
                    s4_allocs.append(
                        ProposedAllocationItem(
                            week=phase_w,
                            area=step.area_id,
                            station_id=compat[0].id,
                            allocated_hours=usable_internal_h,
                            allocated_units=round(usable_internal_h / hpu, 2),
                            is_subcontracted=False,
                        )
                    )

                if subcontract_h > 0:
                    sub_rate = area_cfg.subcontract_hourly_cost if area_cfg else 38.0
                    sub_logistics = area_cfg.subcontract_fixed_logistics if area_cfg else 250.0
                    phase_sub_cost = round(subcontract_h * sub_rate + sub_logistics, 2)
                    s4_cost += phase_sub_cost
                    sub_units = round(subcontract_h / hpu, 2)

                    s4_allocs.append(
                        ProposedAllocationItem(
                            week=phase_w,
                            area=step.area_id,
                            station_id="EXT-" + step.area_id.upper(),
                            allocated_hours=subcontract_h,
                            allocated_units=sub_units,
                            is_subcontracted=True,
                        )
                    )
                    s4_actions.append(
                        f"Subcontratar externamente {sub_units} uds ({subcontract_h}h) de '{step.name}' en {phase_w} "
                        f"(Coste proveedor + logística: {phase_sub_cost:.2f} EUR)."
                    )

        is_sub_profitable = (s4_cost < s3_extra_cost) if (s3_extra_cost > 0 and s4_cost > 0) else True
        suggestions.append(
            StrategySuggestion(
                strategy_id="S4",
                strategy_code="PHASE_SUBCONTRACTING",
                title="4. Subcontratar Fase Cuello de Botella a Proveedor Externo",
                viable=s4_viable and len(s4_actions) > 0,
                proposed_delivery_week=order.delivery_week,
                delay_weeks=0,
                extra_cost_eur=round(s4_cost, 2),
                is_subcontracting_profitable=is_sub_profitable,
                description=(
                    f"Externaliza únicamente el excedente de la fase saturada por {s4_cost:.2f} EUR "
                    f"({'MÁS RENTABLE que horas extra' if is_sub_profitable else 'Más caro que horas extra, pero libera la planta'})."
                ),
                actions=s4_actions or ["No se requiere subcontratación externa."],
                allocations=s4_allocs if s4_viable else [],
            )
        )

        # -------------------------------------------------------------------------
        # ESTRATEGIA 5: Reprogramar Entrega a Fecha Mínima Viable (EARLIEST_FEASIBLE_DELIVERY)
        # -------------------------------------------------------------------------
        s5_viable = False
        s5_week = order.delivery_week
        s5_delay = 0
        s5_allocs: List[ProposedAllocationItem] = []

        for delta in range(1, 25):
            cand_w = shift_week(order.delivery_week, delta)
            l_ok, _, cand_conflicts, cand_allocs = self.evaluate_baseline(order, target_delivery_week=cand_w)
            if l_ok and len(cand_conflicts) == 0:
                s5_viable = True
                s5_week = cand_w
                s5_delay = delta
                s5_allocs = cand_allocs
                break

        suggestions.append(
            StrategySuggestion(
                strategy_id="S5",
                strategy_code="EARLIEST_FEASIBLE_DELIVERY",
                title=f"5. Retrasar Entrega a Fecha Mínima Viable ({s5_week})",
                viable=s5_viable,
                proposed_delivery_week=s5_week,
                delay_weeks=s5_delay,
                extra_cost_eur=0.0,
                description=(
                    f"Desplazar la entrega +{s5_delay} semana(s) hasta {s5_week} permite fabricar el 100% "
                    "del pedido en planta sin horas extra ni subcontratación (0 EUR de sobrecoste)."
                ),
                actions=[f"Acordar con el cliente nueva semana de entrega en {s5_week}."],
                allocations=s5_allocs,
            )
        )

        return suggestions
