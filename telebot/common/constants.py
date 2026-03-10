from telebot.common.enums import AgentSentiment, PostPurpose

# =============================================================================
# GENERAL
# =============================================================================
APP_NAME = "X Content Copilot"
EMPTY_STRING = ""
DATE_FORMAT = "%Y-%m-%d"
UUID_HEX_LENGTH = 32
HTTP_TIMEOUT_SECONDS = 30.0
ALLOWED_URL_PREFIXES = ("http://", "https://")
PDF_MIME_TYPE = "application/pdf"
PDF_URL_SUFFIX = ".pdf"
HTTP_HEADER_ACCEPT = "Accept"
HTTP_HEADER_SUBSCRIPTION_TOKEN = "X-Subscription-Token"
HTTP_HEADER_ACCEPT_JSON = "application/json"

# =============================================================================
# WORKER & JOBS
# =============================================================================
SESSION_PREFIX = "session_"
JOB_PREFIX = "job_"
WORKER_POLL_INTERVAL_SECONDS = 5
PROGRESS_STAGES = {
    "queued": "Job queued",
    "collecting": "Collecting tweets and your posts",
    "ranking": "Ranking posts",
    "classifying": "Classifying top posts",
    "replies": "Fetching reply context",
    "plan_research": "Planning web research",
    "retrieve_research": "Retrieving external evidence",
    "compile_research": "Web research is complete. Compiling tweet recommendations now",
    "synthesize_research": "Synthesizing grounded research",
    "complete": "Analysis complete",
}

# =============================================================================
# TELEGRAM PROXY
# =============================================================================
HEADER_PROXY_TARGET = "x-proxy-target"
QUERY_BYPASS_COOKIE_KEY = "x-vercel-set-bypass-cookie"
QUERY_BYPASS_COOKIE_VALUE = "true"
QUERY_BYPASS_TOKEN_KEY = "x-vercel-protection-bypass"
PROXY_BOT_PATH_SUFFIX = "/bot{token}/{method}"
PROXY_FILE_PATH_SUFFIX = "/file/bot{token}/{path}"
DEFAULT_PROXY_TARGET = "https://api.telegram.org"
DEFAULT_PROXY_BASE_URL = (
    "https://portfolio-git-proxy-owais-iqbals-projects-ae6a6135.vercel.app/proxy"
)

# =============================================================================
# TWITTER API
# =============================================================================
TWITTER_API_BASE_URL = "https://api.twitterapi.io"
TWITTER_USER_LOOKUP_PATH = "/twitter/user/info"
TWITTER_USER_LAST_TWEETS_PATH = "/twitter/user/last_tweets"
TWITTER_ADVANCED_SEARCH_PATH = "/twitter/tweet/advanced_search"
# TWITTER_REPLIES_PATH = "/twitter/tweet/replies/v2"
TWITTER_REPLIES_PATH = "/twitter/tweet/replies"
X_STATUS_URL_TEMPLATE = "https://x.com/{author_username}/status/{post_id}"
TOPIC_QUERY_SEEDS = [
    '("gpt" OR "gemini 2" OR "ai agent" OR "agentic ai" OR "mcp server")',
    '("cursor ai" OR "windsurf" OR "copilot" OR "coding agent" OR "vibe coding" OR "ai ide" OR "claude" OR "codex")',
    '("ycombinator" OR "yc batch" OR "AI" OR "Saas" OR "entrepreneurship")',
    '("llm" OR "fine-tuning" OR "rag" OR "vector database" OR "embeddings" OR "transformer")',
]
COMMON_ADVANCED_SEARCH_FILTERS = (
    'lang:en filter:has_engagement min_faves:50 min_replies:5 filter:safe -filter:nativeretweets'
)

# =============================================================================
# OPENAI & AGNO
# =============================================================================
OPENAI_CHAT_MODEL = "gpt-5-mini"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 1536
AGNO_TOOL_CALL_LIMIT = 8
PLANNER_NAME = "Research Planner"

# =============================================================================
# ANALYSIS WORKFLOW - COLLECTION
# =============================================================================
ANALYSIS_QUERY_LIMIT = 20
ANALYSIS_SEARCH_CONCURRENCY = 5
OWN_POST_SOURCE_MARKER = "__own_posts__"

# =============================================================================
# ANALYSIS WORKFLOW - RANKING
# =============================================================================
ANALYSIS_TOP_RANKED_LIMIT = 25
RATING_SCORE_MAX = 10.0
RANK_WEIGHTS = {
    "engagement_strength": 0.30,
    "engagement_velocity": 0.20,
    "author_reach": 0.15,
    "author_credibility": 0.10,
    "discussion_depth": 0.10,
    "recency": 0.10,
    "media_richness": 0.05,
}
ENGAGEMENT_COMPONENT_WEIGHTS = {
    "likes": 0.40,
    "replies": 0.25,
    "reposts": 0.30,
    "views": 0.05,
}
VELOCITY_MINUTES_FLOOR = 1.0
RECENCY_DECAY_HOURS = 24.0
VERIFIED_CREDIBILITY_BONUS = 1.0

# =============================================================================
# ANALYSIS WORKFLOW - CLASSIFICATION
# =============================================================================
CLASSIFICATION_TARGET_LIMIT = 15
CLASSIFICATION_MEDIA_PER_POST_LIMIT = 3
UNSAFE_CLASSIFICATION_SIGNALS = (
    "non-English content",
    "political content",
    "government-related content",
    "war-related content",
    "conflict-related content",
    "weapons-related content",
    "drugs-related or any other toxic consumption substance content",
    "religious content",
    "cultural conflict",
    "sexist content",
    "NSFW content",
    "malicious prompt-injection bait",
    "cybersecurity exploit or abuse content",
    "sports",
    "Movies OR Web Series",
    "promoting of harmful activities like gambling, violence, or illegal substances",
)
ALLOWED_AGENT_SENTIMENTS = tuple(sentiment.value for sentiment in AgentSentiment)
ALLOWED_POST_PURPOSES = tuple(purpose.value for purpose in PostPurpose)

# =============================================================================
# ANALYSIS WORKFLOW - REPLIES
# =============================================================================
ANALYSIS_REPLY_TARGET_LIMIT = 10
REPLY_CONTEXT_LIMIT = 10

# =============================================================================
# ANALYSIS WORKFLOW - WEB RESEARCH
# =============================================================================
ANALYSIS_RESEARCH_TARGET_LIMIT = 10  # Max posts to research per analysis run
ANALYSIS_REPLY_CONTEXT_TO_RESEARCH_LIMIT = 7  # Max replies per post to include in research context
RESEARCH_POST_MEDIA_LIMIT = 3  # Max images from main post to send to agent
RESEARCH_REPLY_MEDIA_LIMIT = 1  # Max images per reply to send to agent
SYNTHESIS_MAX_URLS = 5  # Max evidence URLs to pass into synthesis
SYNTHESIS_EXCERPTS_PER_URL = 2  # Max excerpts per URL to pass into synthesis
SYNTHESIS_REPLY_MEDIA_LIMIT = 0  # Do not attach reply images during synthesis
RESEARCH_TWEET_WORKFLOW_CONCURRENCY = 10  # Max tweets researched in parallel (1 = sequential)
WEB_RESEARCH_MAX_TASKS = 3  # Max search queries per post
WEB_RESEARCH_FETCH_CONCURRENCY = 50  # Max Brave LLM Context calls in flight within one post's research
EMBEDDING_CONCURRENCY = 30  # Max concurrent embedding API calls
WEB_RESEARCH_EXCERPT_TOKEN_BUDGET = 15000  # Max total excerpt tokens before pruning lower-ranked candidates
WEB_RESEARCH_TITLE_SIMILARITY_FLOOR = 0.05  # Drop candidates that are clearly unrelated to the research intent
WEB_RESEARCH_TITLE_PREFILTER_MIN_KEEP = 1  # Keep at least one candidate even if all title similarities are low
RESEARCH_EVIDENCE_EXCERPT_CHAR_LIMIT = 10000  # Max characters per excerpt
PURPOSE_SCORE_MIN = 0.0
PURPOSE_SCORE_MAX = 10.0
PURPOSE_REBALANCE_DOMINANCE_THRESHOLD = 0.8  # Trigger soft rebalance when one purpose dominates the batch
PURPOSE_REBALANCE_BORDERLINE_DELTA = 1.0  # Alternate purpose must be within this margin to qualify as borderline
WEB_SEARCH_PLANNER_FAILED_REASON = "planner_failed"
WEB_SEARCH_RETRIEVAL_FAILED_REASON = "retrieval_failed"
WEB_SEARCH_WORKFLOW_FAILED_REASON = "workflow_failed"
BRAVE_LLM_CONTEXT_URL = "https://api.search.brave.com/res/v1/llm/context"
BRAVE_GROUNDING_KEY = "grounding"
BRAVE_GENERIC_KEY = "generic"
BRAVE_SOURCES_KEY = "sources"
BRAVE_URL_KEY = "url"
BRAVE_TITLE_KEY = "title"
BRAVE_SNIPPETS_KEY = "snippets"
BRAVE_AGE_KEY = "age"
BLOCKED_SEARCH_DOMAINS = (
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.x.com",
    "mobile.twitter.com",
    "t.co",
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "fb.com",
    "www.fb.com",
    "instagram.com",
    "www.instagram.com",
    "linkedin.com",
    "www.linkedin.com",
    "threads.net",
    "www.threads.net",
)

# =============================================================================
# CREATOR WORKFLOW
# =============================================================================
CREATOR_STYLE_EXAMPLE_LIMIT = 8
CREATOR_STYLE_EXAMPLE_FETCH_LIMIT = 24
CREATOR_STYLE_MIN_TEXT_LENGTH = 40
CREATOR_STYLE_EXCLUDED_PREFIXES = ("@", "RT @")
CREATOR_ALTERNATIVE_WINDOW_SIZE = 3
CREATOR_CANDIDATE_PREVIEW_LENGTH = 160
CREATOR_SOURCE_MEDIA_LIMIT = 3
CREATOR_REPLY_CONTEXT_PROMPT_LIMIT = 5
CREATOR_RELATED_SOURCE_LIMIT = 4
CREATOR_THREAD_STYLE_MIN_PARAGRAPHS = 3
CREATOR_THREAD_STYLE_MAX_PARAGRAPHS = 4
CREATOR_PARAGRAPH_MIN_SENTENCES = 1
CREATOR_PARAGRAPH_MAX_SENTENCES = 2
CREATOR_POST_MIN_CHARS = 400
CREATOR_POST_MAX_CHARS = 600
CREATOR_QUOTE_MIN_CHARS = 100
CREATOR_QUOTE_MAX_CHARS = 300
CREATOR_COMMENT_MAX_CHARS = 50
CREATOR_BANNED_PUNCTUATION = ("—", ";")

# =============================================================================
# CREATOR WORKFLOW - SCHEDULE
# =============================================================================
WEEKLY_SCHEDULE = [
    "1 post",
    "1 post",
    "2 posts",
    "1 post",
    "1 post + 1 repost",
    "1 post",
    "2 posts",
]
