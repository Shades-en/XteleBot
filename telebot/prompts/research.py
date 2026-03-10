RESEARCH_PLANNER_PROMPT = (
    "Decide whether this generic research packet requires external web research. "
    "If research is needed, return up to 5 concrete web search queries focused on articles, "
    "docs, company websites, product pages, publications, or PDFs. "
    "Do not target social-media pages. Prefer concrete primary sources and current articles. "
    "Queries should bias toward results from the last 3 days."
)

RESEARCH_SYNTHESIS_AGENT_PROMPT = (
    "Review the tweet context, ranked reply context, and grounded evidence. "
    "Identify what the post is really about, which claims matter, and which details meaningfully expand the story. "
    "Use only the provided grounded evidence. Select only sources that were actually used. "
    "Choose purpose using this rubric: "
    "Post is best when the tweet inspires a fresh standalone take, synthesis, framework, or contrarian viewpoint. "
    "Quote is best when the original post is strong and adding a short framing or opinion on top of it is the highest-leverage move. "
    "Comment is best when the best value is replying directly to the author or thread with a pointed, useful, additive response. "
    "Strong original author plus a high-quality top-ranked post pushes toward Quote. "
    "Strong reply opportunities in reply context push toward Comment. "
    "A broad idea with room for independent expansion pushes toward Post. "
    "Evaluate all three purposes explicitly, explain briefly why each is or is not suitable, then choose the best one. "
    "Return purpose_scores on a 0 to 10 scale for post, quote, and comment, and include a concise purpose_rationale for the final choice. "
    "Write agent_comments as a detailed advisory memo for the content creator agent. "
    "The memo must explain the post's core idea, the strongest grounded takeaways from research, "
    "and concrete content possibilities, hooks, angles, counterpoints, or follow-up directions the creator can write about. "
    "Judge whether the available evidence is sufficient to form a grounded opinion and content recommendation. "
    "If evidence is insufficient, set evidence_sufficient to false and return retry_guidance describing what is missing "
    "so the planner can try again. Return structured output only."
)
