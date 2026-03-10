from __future__ import annotations

from typing import TYPE_CHECKING

from telebot.costs.pricing import OPENAI_MODEL_PRICING, normalize_openai_model_id

if TYPE_CHECKING:
    from telebot.costs.tracker import WorkflowCostTracker


def record_run_output(tracker: "WorkflowCostTracker" | None, response) -> None:
    if tracker is None:
        return
    metrics = getattr(response, "metrics", None)
    details = getattr(metrics, "details", None)
    if not isinstance(details, dict):
        return
    for model_metrics_list in details.values():
        if not isinstance(model_metrics_list, list):
            continue
        for model_metrics in model_metrics_list:
            model_id = normalize_openai_model_id(getattr(model_metrics, "id", "") or "")
            if not model_id:
                continue
            tracker.record_openai_model_usage(
                model_id=model_id,
                input_tokens=int(getattr(model_metrics, "input_tokens", 0) or 0),
                cached_input_tokens=int(getattr(model_metrics, "cache_read_tokens", 0) or 0),
                output_tokens=int(getattr(model_metrics, "output_tokens", 0) or 0),
            )


def record_embedding_response(tracker: "WorkflowCostTracker" | None, response) -> None:
    if tracker is None:
        return
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    if prompt_tokens == 0:
        return
    model_id = normalize_openai_model_id(getattr(response, "model", "text-embedding-3-small"))
    if model_id not in OPENAI_MODEL_PRICING:
        model_id = "text-embedding-3-small"
    tracker.record_openai_model_usage(model_id=model_id, input_tokens=prompt_tokens)
