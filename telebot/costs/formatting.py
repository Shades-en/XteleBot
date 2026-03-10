from telebot.costs.schemas import WorkflowCostSummary


def format_cost_summary(summary: WorkflowCostSummary, partial: bool = False) -> str:
    lines = [
        "API cost summary",
        f"Total: ${summary.total_cost_usd:.6f}" + (" (partial)" if partial else ""),
        _format_openai(summary),
        f"Brave: ${summary.brave.total_cost_usd:.6f} ({summary.brave.request_count} requests)",
        f"TwitterAPI: ${summary.twitter.total_cost_usd:.6f} ({summary.twitter.total_credits} credits)",
    ]
    if summary.warnings:
        lines.append("Warnings: " + "; ".join(summary.warnings))
    return "\n".join(lines)


def format_job_cost_section(cost_breakdown: dict | None, total_cost_usd: float | None) -> str:
    if not cost_breakdown:
        return "Cost: not recorded"
    summary = WorkflowCostSummary.model_validate(
        {
            "total_cost_usd": float(total_cost_usd or 0.0),
            **cost_breakdown,
        }
    )
    return format_cost_summary(summary, partial=bool(summary.warnings))


def _format_openai(summary: WorkflowCostSummary) -> str:
    parts = [f"OpenAI: ${summary.openai.total_cost_usd:.6f}"]
    model_parts = [
        f"{usage.model_id}=${usage.total_cost_usd:.6f}"
        for usage in summary.openai.models.values()
    ]
    if model_parts:
        parts.append(f"({', '.join(model_parts)})")
    if summary.openai.unknown_models:
        unknown = ", ".join(summary.openai.unknown_models)
        parts.append(f"[unknown pricing: {unknown}]")
    return " ".join(parts)
