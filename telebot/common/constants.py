from telebot.common.enums import AgentSentiment, PostPurpose

APP_NAME = "X Content Copilot"
EMPTY_STRING = ""
SESSION_PREFIX = "session_"
JOB_PREFIX = "job_"
DATE_FORMAT = "%Y-%m-%d"
UUID_HEX_LENGTH = 32
HTTP_TIMEOUT_SECONDS = 30.0
WORKER_POLL_INTERVAL_SECONDS = 5
PROGRESS_STAGES = {
    "queued": "Job queued",
    "collecting": "Collecting tweets and your posts",
    "ranking": "Ranking posts",
    "classifying": "Classifying top posts",
    "replies": "Fetching reply context",
    "plan_research": "Planning web research",
    "retrieve_research": "Retrieving external evidence",
    "synthesize_research": "Synthesizing grounded research",
    "complete": "Analysis complete",
}
ANALYSIS_QUERY_LIMIT = 20
ANALYSIS_SEARCH_CONCURRENCY = 5
ANALYSIS_TOP_RANKED_LIMIT = 25
ANALYSIS_REPLY_TARGET_LIMIT = 10
ANALYSIS_RESEARCH_TARGET_LIMIT = 10
ANALYSIS_REPLY_CONTEXT_TO_RESEARCH_LIMIT = 7
CLASSIFICATION_MEDIA_PER_POST_LIMIT = 3
RESEARCH_POST_MEDIA_LIMIT = 3
RESEARCH_REPLY_MEDIA_LIMIT = 1
WEB_RESEARCH_MAX_TASKS = 5
WEB_RESEARCH_MAX_URLS_PER_TASK = 5
WEB_RESEARCH_MAX_FETCHED_PAGES = 12
WEB_RESEARCH_MAX_EVIDENCE = 8
RESEARCH_TWEET_WORKFLOW_CONCURRENCY = 1
WEB_RESEARCH_FETCH_CONCURRENCY = 8
WEB_RESEARCH_CHUNK_SIZE = 5000
WEB_RESEARCH_CHUNK_OVERLAP = 1000
WEB_RESEARCH_RERANK_LIMIT = 8
WEB_RESEARCH_RETRY_LIMIT = 1
WEB_RESEARCH_LOOP_MAX_ITERATIONS = 3
CLASSIFICATION_TARGET_LIMIT = 25
SEARCH_PLAN_PROMPT_TEMPLATE = (
    "Plan up to 5 web searches for this post. Category: {category}. Post: {post_text}"
)
SERPER_ORGANIC_KEY = "organic"
SERPER_LINK_KEY = "link"
SERPER_TITLE_KEY = "title"
SERPER_SNIPPET_KEY = "snippet"
SEARCH_EXTRACTION_ERROR_PREFIX = "Error:"
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
    "promoting of harmful activities like gambling, violence, or illegal substances",
)
WEEKLY_SCHEDULE = [
    "1 post",
    "1 post",
    "2 posts",
    "1 post",
    "1 post + 1 repost",
    "1 post",
    "2 posts",
]
TWITTER_API_BASE_URL = "https://api.twitterapi.io"
TWITTER_USER_LOOKUP_PATH = "/twitter/user/info"
TWITTER_USER_LAST_TWEETS_PATH = "/twitter/user/last_tweets"
TWITTER_ADVANCED_SEARCH_PATH = "/twitter/tweet/advanced_search"
TWITTER_REPLIES_PATH = "/twitter/tweet/replies/v2"
OPENAI_CHAT_MODEL = "gpt-5-mini"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 1536
RESEARCH_EVIDENCE_EXCERPTS_PER_SOURCE = 2
RESEARCH_EVIDENCE_EXCERPT_CHAR_LIMIT = 1200
AGNO_MAX_ITERATIONS = 8
AGNO_TOOL_CALL_LIMIT = 8
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
X_STATUS_URL_TEMPLATE = "https://x.com/{author_username}/status/{post_id}"
ALLOWED_URL_PREFIXES = ("http://", "https://")
TOPIC_QUERY_SEEDS = [
    '("gpt-5" OR "gemini 2" OR "ai agent" OR "agentic ai" OR "mcp server")',
    '("cursor ai" OR "windsurf" OR "copilot" OR "coding agent" OR "vibe coding" OR "ai ide" OR "claude" OR "codex")',
    '("ycombinator" OR "yc batch" OR "series a" OR "seed round" OR "techstars" OR "indie hacker")',
    '("llm" OR "fine-tuning" OR "rag" OR "vector database" OR "embeddings" OR "transformer")',
    '("product hunt" OR "launch" OR "side project" OR "shipped" OR "built with" OR "open source")',
]
COMMON_ADVANCED_SEARCH_FILTERS = (
    'lang:en filter:has_engagement min_faves:50 min_replies:5 filter:safe -filter:nativeretweets'
)
RANK_WEIGHTS = {
    "engagement_strength": 0.30,
    "engagement_velocity": 0.20,
    "author_reach": 0.15,
    "author_credibility": 0.10,
    "discussion_depth": 0.10,
    "recency": 0.10,
    "media_richness": 0.05,
}
RATING_SCORE_MAX = 10.0
ENGAGEMENT_COMPONENT_WEIGHTS = {
    "likes": 0.40,
    "replies": 0.25,
    "reposts": 0.30,
    "views": 0.05,
}
VELOCITY_MINUTES_FLOOR = 1.0
RECENCY_DECAY_HOURS = 24.0
VERIFIED_CREDIBILITY_BONUS = 1.0
OWN_POST_SOURCE_MARKER = "__own_posts__"
REPLY_CONTEXT_LIMIT = 10
PDF_MIME_TYPE = "application/pdf"
PDF_URL_SUFFIX = ".pdf"
PLANNER_NAME = "Research Planner"
SYNTHESIS_TEAM_NAME = "Research Synthesis Team"
RESEARCH_ANALYST_NAME = "Research Analyst"
EVIDENCE_SYNTHESIZER_NAME = "Evidence Synthesizer"
RESEARCH_REVIEWER_NAME = "Research Reviewer"
ALLOWED_AGENT_SENTIMENTS = tuple(sentiment.value for sentiment in AgentSentiment)
ALLOWED_POST_PURPOSES = tuple(purpose.value for purpose in PostPurpose)
