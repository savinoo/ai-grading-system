"""
Parser robusto para saídas do DSPy em múltiplos formatos.

O DSPy pode retornar a correção como:
  - AgentCorrection já parseada (caso ideal)
  - String JSON (com ou sem blocos markdown)
  - String texto livre (fallback com regex)
  - Dict Python ou objeto com model_dump/to_dict

Este módulo centraliza toda a lógica de normalização para evitar
código duplicado em examiner_agent e arbiter_agent.

Independente do formato de entrada, a saída é sempre um AgentCorrection
válido com agent_id garantido.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from src.domain.ai.agent_schemas import AgentCorrection, AgentID
from src.core.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _sanitize_data_dict(data: dict, agent_id: AgentID) -> dict:
    """
    Sanitiza um dict bruto antes de passar para model_validate.

    Ajustes aplicados:
    - reasoning_chain: lista → string única
    - criteria_scores: lista de dicts com chaves variadas → formato padrão
    - agent_id: injeta se ausente
    """
    # 1. reasoning_chain (lista → string)
    if "reasoning_chain" in data and isinstance(data["reasoning_chain"], list):
        data["reasoning_chain"] = "\n".join(str(s) for s in data["reasoning_chain"])

    # 2. criteria_scores: normaliza itens com chaves inesperadas
    if "criteria_scores" in data and isinstance(data["criteria_scores"], list):
        normalized = []
        for item in data["criteria_scores"]:
            if isinstance(item, dict):
                # Aceita 'criterion', 'criterion_name' ou primeira chave disponível como nome
                name = (
                    item.get("criterion")
                    or item.get("criterion_name")
                    or item.get("name")
                    or (next(iter(item.keys()), "Unknown") if item else "Unknown")
                )
                score = item.get("score") or item.get("value") or 0.0
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    score = 0.0
                normalized.append({
                    "criterion": str(name),
                    "score": score,
                    "max_score": item.get("max_score"),
                    "feedback": item.get("feedback"),
                })
            else:
                logger.warning(
                    "[DspyParser] Item inesperado em criteria_scores (ignorado): %s", item
                )
        data["criteria_scores"] = normalized

    # 3. Injeta agent_id se ausente
    if not data.get("agent_id"):
        data["agent_id"] = agent_id

    return data


def _fallback_correction(
    agent_id: AgentID,
    reasoning: str,
    total_score: float,
    feedback: str,
) -> AgentCorrection:
    """Cria um AgentCorrection de fallback mínimo mas válido."""
    return AgentCorrection(
        agent_id=agent_id,
        reasoning_chain=reasoning if len(reasoning) >= 50 else reasoning.ljust(50),
        criteria_scores=[],
        total_score=total_score,
        feedback_text=feedback,
    )


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def parse_dspy_correction_output(
    raw_result: Any,
    agent_id: AgentID,
    fallback_score: float = 0.0,
    prediction: Any = None,
) -> AgentCorrection:
    """
    Converte a saída bruta do DSPy em um AgentCorrection estruturado.

    Tenta os seguintes casos na ordem:

    **CASO 1 – Already parsed:** ``raw_result`` já é um AgentCorrection → retorna direto.

    **CASO 2 – String:** limpa blocos markdown, tenta ``json.loads`` e, se falhar,
    usa regex para extrair nota e cria objeto mínimo.

    **CASO 3 – Dict / objeto:** chama ``model_dump()`` / ``to_dict()`` / cast para
    dict, sanitiza tipos e valida via ``model_validate``.

    Após o parse, ``result.agent_id`` é sempre sobrescrito com o ``agent_id``
    fornecido e ``calculate_total_if_missing`` é chamado via model_validator
    (já integrado no schema Pydantic).

    Args:
        raw_result: Saída bruta do campo DSPy (``prediction.correction``,
            ``prediction.reasoning_chain``, etc.).
        agent_id: ID do agente responsável pela correção.
        fallback_score: Nota de fallback quando não é possível extrair nenhuma.
        prediction: Objeto de predição DSPy completo. Se fornecido e
            ``result.reasoning_chain`` estiver vazio, usa ``prediction.rationale``.

    Returns:
        AgentCorrection sempre válido, nunca None.
    """
    result: Optional[AgentCorrection] = None

    # ── CASO 1: já é um AgentCorrection ──────────────────────────────────────
    if isinstance(raw_result, AgentCorrection):
        logger.debug("[DspyParser] CASO 1: raw_result já é AgentCorrection.")
        result = raw_result

    # ── CASO 2: string ────────────────────────────────────────────────────────
    elif isinstance(raw_result, str):
        # Remove blocos markdown (```json ... ``` ou ``` ... ```)
        clean = re.sub(r"```(?:json)?", "", raw_result).replace("```", "").strip()
        logger.debug("[DspyParser] CASO 2: string. Primeiros 200 chars: %s", clean[:200])

        if clean and clean.startswith("{"):
            # Tenta parsear JSON
            try:
                data = json.loads(clean)
                data = _sanitize_data_dict(data, agent_id)
                result = AgentCorrection.model_validate(data)
                logger.debug("[DspyParser] CASO 2a: JSON parseado com sucesso.")
            except json.JSONDecodeError as exc:
                logger.warning(
                    "[DspyParser] CASO 2b: JSONDecodeError ('%s'). Aplicando regex fallback.", exc
                )
                # Regex fallback: tenta extrair nota de texto como "Nota: 7.5" ou "Total: 8"
                match = re.search(
                    r"(?:nota|total|score)[:\s]*(\d+[\.,]?\d*)",
                    clean,
                    re.IGNORECASE,
                )
                score = float(match.group(1).replace(",", ".")) if match else fallback_score
                result = _fallback_correction(
                    agent_id=agent_id,
                    reasoning=clean or "[Sistema] Resposta vazia do LLM",
                    total_score=score,
                    feedback="[Sistema] Correção em formato texto (fallback JSON aplicado).",
                )
        else:
            # Texto livre ou vazio
            logger.warning(
                "[DspyParser] CASO 2c: string não é JSON válido ('%s...'). "
                "Tentando extração via regex.",
                clean[:80],
            )
            match = re.search(
                r"(?:nota|total|score)[:\s]*(\d+[\.,]?\d*)",
                clean,
                re.IGNORECASE,
            )
            score = float(match.group(1).replace(",", ".")) if match else fallback_score
            result = _fallback_correction(
                agent_id=agent_id,
                reasoning=clean if clean else "[Sistema] Resposta vazia do LLM",
                total_score=score,
                feedback="[Sistema] Correção gerada em formato texto livre (fallback aplicado).",
            )

    # ── CASO 3: dict / objeto com dump ───────────────────────────────────────
    else:
        logger.debug("[DspyParser] CASO 3: tipo=%s. Convertendo para dict.", type(raw_result))
        try:
            if hasattr(raw_result, "model_dump"):
                data = raw_result.model_dump()
            elif hasattr(raw_result, "to_dict"):
                data = raw_result.to_dict()
            elif isinstance(raw_result, dict):
                data = dict(raw_result)
            else:
                data = dict(raw_result)  # tentativa de cast genérico

            data = _sanitize_data_dict(data, agent_id)
            logger.debug("[DspyParser] CASO 3: data sanitizado: %s", data)
            result = AgentCorrection.model_validate(data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                "[DspyParser] CASO 3 falhou ('%s'). Usando fallback score=%.2f.",
                exc,
                fallback_score,
            )
            result = _fallback_correction(
                agent_id=agent_id,
                reasoning=f"[Sistema] Erro ao converter saída DSPy: {exc}",
                total_score=fallback_score,
                feedback="[Sistema] Correção substituída por fallback (erro de parsing).",
            )

    # ── Pós-processamento garantido ───────────────────────────────────────────
    # 1. Resgata reasoning do ChainOfThought se o campo estiver vazio
    if prediction is not None and hasattr(prediction, "rationale"):
        if not result.reasoning_chain or len(result.reasoning_chain.strip()) < 10:
            result.reasoning_chain = str(prediction.rationale)
            logger.debug("[DspyParser] reasoning_chain preenchido a partir de prediction.rationale.")

    # 2. Sempre sobrescreve agent_id para garantir consistência
    result.agent_id = agent_id

    return result
