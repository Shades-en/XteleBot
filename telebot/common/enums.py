from enum import Enum


class BotEnv(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class SessionStatus(str, Enum):
    IDLE = "idle"
    AWAITING_X_USERNAME = "awaiting_x_username"
    ANALYSIS_RUNNING = "analysis_running"
    GENERATING_POST = "generating_post"
    GENERATING_QUOTE = "generating_quote"
    GENERATING_COMMENT = "generating_comment"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CommandName(str, Enum):
    START = "start"
    HELP = "help"
    PING = "ping"
    CURRENT_USER = "currentuser"
    JOB_STATUS = "jobstatus"
    RESET_SCHEMA = "reset_schema"
    ANALYZE_TODAY = "analysetoday"
    REANALYZE_FOR_TODAY = "reanalysefortoday"
    POST_BY_INSPIRATION = "postbyinspiration"
    QUOTE = "quote"
    COMMENT = "comment"
    SCHEDULE = "schedule"


class PostPurpose(str, Enum):
    POST = "Post"
    QUOTE = "Quote"
    COMMENT = "Comment"


class AgentSentiment(str, Enum):
    AGREE = "Agree"
    DISAGREE = "Disagree"
    CURIOUS = "Curious"
    CONCERNED = "Concerned"
    DOUBTFUL = "Doubtful"
    DELIGHTED = "Delighted"
    SAD = "Sad"
    NEUTRAL = "Neutral"
    OTHER = "Other"


class PostCategory(str, Enum):
    AI = "AI"
    LLMS = "LLMs"
    CODING_AGENTS = "Coding Agents"
    SOFTWARE_ENGINEERING = "Software Engineering"
    PYTHON = "Python"
    MACHINE_LEARNING = "Machine Learning"
    DEEP_LEARNING = "Deep Learning"
    RESEARCH = "Research"
    ROBOTICS = "Robotics"
    VISION = "Vision"
    NLP = "NLP"
    APIS = "APIs"
    SAAS = "SaaS"
    STARTUPS = "Startups"
    FUNDING = "Funding"
    BUSINESS = "Business"
    FINANCE = "Finance"
    INVESTING = "Investing"
    PRODUCTIVITY = "Productivity"
    EDUCATION = "Education"
    NEWS = "News"
    INFORMATIONAL = "Informational"
    MOTIVATIONAL = "Motivational"
    OTHER = "Other"
