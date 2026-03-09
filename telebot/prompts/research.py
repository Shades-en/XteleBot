RESEARCH_PLANNER_PROMPT = (
    "Decide whether this generic research packet requires external web research. "
    "If research is needed, return up to 5 concrete web search queries focused on articles, "
    "docs, company websites, product pages, publications, or PDFs. "
    "Do not target social-media pages. Prefer concrete primary sources and current articles. "
    "Queries should bias toward results from the last 3 days."
)

RESEARCH_ANALYST_PROMPT = (
    "Review the tweet context, ranked reply context, and grounded evidence. "
    "Identify what the post is really about, which claims matter, and which details meaningfully expand the story."
)

EVIDENCE_SYNTHESIZER_PROMPT = (
    "Use only the provided grounded evidence. Select only sources that were actually used. "
    "Write agent_comments as a detailed advisory memo for the content creator agent. "
    "The memo must explain the post's core idea, the strongest grounded takeaways from research, "
    "and concrete content possibilities, hooks, angles, counterpoints, or follow-up directions the creator can write about."
)

RESEARCH_REVIEWER_PROMPT = (
    "Judge whether the available evidence is sufficient to form a grounded opinion and content recommendation. "
    "If it is insufficient, return retry_guidance describing what is missing so the planner can try again."
)
