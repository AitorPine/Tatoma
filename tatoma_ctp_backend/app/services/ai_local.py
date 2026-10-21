import json
import httpx
from typing import List
from app.schemas import AIRecommendationOut, ConflictItem, OrderCreate, StrategySuggestion

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b-instruct"


async def evaluate_with_local_ai(
    order: OrderCreate,
    conflicts: List[ConflictItem],
    suggestions: List[StrategySuggestion],
) -> AIRecommendationOut:
    if not conflicts:
        return AIRecommendationOut(
            recommended_strategy_code="DIRECT_ACCEPT",
            summary=f"El pedido {order.code} encaja al 100% en capacidad ordinaria cumpliendo el plazo de entrega ({order.delivery_week}).",
            profitability_reasoning="Sobrecoste 0 EUR. No requiere horas extra ni subcontratación externa.",
            risk_level="BAJO",
            generated_by="Motor Determinista",
        )

    viable_suggestions = [s for s in suggestions if s.viable]
    best_fallback = sorted(viable_suggestions, key=lambda x: (x.delay_weeks, x.extra_cost_eur))[0] if viable_suggestions else suggestions[0]

    prompt_payload = {
        "order": order.model_dump(),
        "conflicts": [c.model_dump() for c in conflicts],
        "viable_strategies": [
            {
                "code": s.strategy_code,
                "title": s.title,
                "delay_weeks": s.delay_weeks,
                "extra_cost_eur": s.extra_cost_eur,
                "is_subcontracting_profitable": s.is_subcontracting_profitable,
                "description": s.description,
            }
            for s in viable_suggestions
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres un Director de Operaciones Industriales. Recibes conflictos de capacidad "
                                "y las 5 estrategias calculadas por el motor matemático. Responde SOLO en JSON con las claves: "
                                "recommended_strategy_code, summary, profitability_reasoning, risk_level."
                            ),
                        },
                        {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["message"]["content"])
            return AIRecommendationOut(
                recommended_strategy_code=data.get("recommended_strategy_code", best_fallback.strategy_code),
                summary=data.get("summary", best_fallback.description),
                profitability_reasoning=data.get("profitability_reasoning", "Análisis económico validado por IA local."),
                risk_level=data.get("risk_level", "MEDIO"),
                generated_by=f"Ollama Local ({OLLAMA_MODEL})",
            )
    except Exception:
        # Fallback determinista instantáneo si Ollama no está ejecutándose en la máquina local
        sub_sugg = next((s for s in viable_suggestions if s.strategy_code == "PHASE_SUBCONTRACTING"), None)
        ot_sugg = next((s for s in viable_suggestions if s.strategy_code == "OVERTIME_AND_EXTRA_SHIFTS"), None)

        if sub_sugg and ot_sugg:
            if sub_sugg.extra_cost_eur < ot_sugg.extra_cost_eur:
                reasoning = (
                    f"Subcontratar el cuello de botella cuesta {sub_sugg.extra_cost_eur:.2f} EUR frente a "
                    f"{ot_sugg.extra_cost_eur:.2f} EUR en horas extra internas. Sale rentable externalizar."
                )
            else:
                reasoning = (
                    f"Cubrir con horas extra internas ({ot_sugg.extra_cost_eur:.2f} EUR) es más económico "
                    f"que subcontratar ({sub_sugg.extra_cost_eur:.2f} EUR)."
                )
        else:
            reasoning = f"Opción óptima seleccionada por menor impacto en plazo (+{best_fallback.delay_weeks} sem) y coste ({best_fallback.extra_cost_eur:.2f} EUR)."

        return AIRecommendationOut(
            recommended_strategy_code=best_fallback.strategy_code,
            summary=f"Recomendación: {best_fallback.title} -> {best_fallback.description}",
            profitability_reasoning=reasoning,
            risk_level="BAJO" if best_fallback.extra_cost_eur == 0 else "MEDIO",
            generated_by="Motor Heurístico Local (Fallback Instantáneo)",
        )
