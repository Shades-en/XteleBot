from telebot.common.enums import CommandName

TEXT_PONG = "pong"
TEXT_UNRECOGNIZED_COMMAND = "Unrecognized command. Use /help."
TEXT_COMMAND_PANEL = "Choose a command:"
TEXT_HELP_INTRO = (
    "Use the menu below. Start with /start to connect your X account, then use "
    "/analysetoday before asking for a post, quote, or comment."
)
TEXT_START_PROMPT = "Send your X username prefixed with @ so I can verify it."
TEXT_X_USERNAME_RETRY = (
    "I couldn't verify that X username. Send a valid username prefixed with @."
)
TEXT_X_USERNAME_CONFIRMED = (
    "Your X account is verified. Use /help to see the available commands."
)
TEXT_SETUP_REQUIRED = (
    "You need to connect your X username first. Use /start and send your @username."
)
TEXT_CURRENT_USER_REQUIRED = (
    "No current user details are stored yet. Use /start to set up your account."
)
TEXT_JOB_STATUS_REQUIRED = "No workflow job exists yet. Run /analysetoday first."
TEXT_RESET_SCHEMA_DENIED = "Schema reset is allowed only in development mode."
TEXT_RESET_SCHEMA_DONE = "Postgres schema was reset for development."
TEXT_CURRENT_USER_TEMPLATE = (
    "Current user details\n\n"
    "Telegram user id: {telegram_user_id}\n"
    "Telegram display name: {telegram_display_name}\n"
    "Current session id: {session_id}\n"
    "Session status: {status}\n"
    "Last command: {last_command}\n"
    "X username: {x_username}\n"
    "X display name: {x_display_name}\n"
    "X id: {x_id}"
)
TEXT_ANALYSIS_ALREADY_EXISTS = (
    "Today's analysis already exists. You can now use /postbyinspiration, /quote, or /comment."
)
TEXT_ANALYSIS_QUEUED = "Today's analysis has started. I will send progress updates here."
TEXT_REANALYSIS_QUEUED = (
    "Today's analysis for your account was cleared and has started again. "
    "I will send progress updates here."
)
TEXT_ANALYSIS_RATE_LIMITED = (
    "Twitter API is rate limiting analysis right now. Wait a bit and run /analysetoday again."
)
TEXT_ANALYSIS_EMPTY_RESULT = (
    "Analysis finished without collecting usable posts. Run /analysetoday again later."
)
TEXT_ANALYSIS_REQUIRED = (
    "You need today's analysis first. Run /analysetoday before generating content."
)
TEXT_CREATOR_SOURCE_REQUIRED = {
    CommandName.POST_BY_INSPIRATION: (
        "Today's analysis does not yet have a grounded post candidate. "
        "Run /analysetoday again later."
    ),
    CommandName.QUOTE: (
        "Today's analysis does not yet have a grounded quote candidate. "
        "Run /analysetoday again later or use /postbyinspiration."
    ),
    CommandName.COMMENT: (
        "Today's analysis does not yet have a grounded comment candidate. "
        "Run /analysetoday again later or use /postbyinspiration."
    ),
}
TEXT_CREATOR_ACK = {
    CommandName.POST_BY_INSPIRATION: (
        "Choose the grounded source post for the standalone draft first. I will write it once you pick one."
    ),
    CommandName.QUOTE: (
        "Choose the grounded source post for the quote draft first. I will write it once you pick one."
    ),
    CommandName.COMMENT: (
        "Choose the grounded source post for the comment first. I will write it once you pick one."
    ),
}
TEXT_CREATOR_PROGRESS = {
    CommandName.POST_BY_INSPIRATION: (
        "Grounded context is ready. Writing a concise, high-signal post now."
    ),
    CommandName.QUOTE: (
        "Grounded context is ready. Writing a tight quote draft now."
    ),
    CommandName.COMMENT: (
        "Grounded context is ready. Writing a short, pointed comment now."
    ),
}
TEXT_CREATOR_REFINEMENT_ACK = {
    CommandName.POST_BY_INSPIRATION: (
        "Refining the post now. I am tightening the angle and voice."
    ),
    CommandName.QUOTE: (
        "Refining the quote now. I am tightening the framing and reaction."
    ),
    CommandName.COMMENT: (
        "Refining the comment now. I am making it sharper and cleaner."
    ),
}
TEXT_CREATOR_COST_TEMPLATE = "Draft generation cost\n\n{summary}"
TEXT_CREATOR_JOB_COMPLETED = "Creator draft generated."
TEXT_JOB_STATUS_TEMPLATE = (
    "Latest job status\n\n"
    "Job id: {job_id}\n"
    "Command: {command}\n"
    "Status: {status}\n"
    "Stage: {stage}\n"
    "Progress: {progress}\n"
    "Error: {error}"
)
TEXT_SCHEDULE_TEMPLATE = "Weekly schedule\n\n{lines}\n\nToday's action: {today_action}"
TEXT_GENERIC_WORKFLOW_FAILURE = "The workflow failed. Check logs and try again."
TEXT_UNSUPPORTED_ACTION = "Unsupported action. Use /help."
TEXT_JOB_PROGRESS_TEMPLATE = "[{stage}] {message}"
TEXT_SOURCE_POST_LINK_TEMPLATE = "Source post: {source_url}"
TEXT_RELATED_SOURCES_HEADER = "Related sources:"
TEXT_CREATOR_DIFFERENT_POST_BUTTON = "Different post"
TEXT_CREATOR_MORE_OPTIONS_BUTTON = "More options"
TEXT_CREATOR_PICK_OPTION_TEMPLATE = "Use option {index}"
TEXT_CREATOR_SELECTION_HEADER_TEMPLATE = (
    "Choose a grounded {purpose} candidate for today.\n\n{options}"
)
TEXT_CREATOR_ALTERNATIVES_HEADER_TEMPLATE = (
    "Here are other grounded {purpose} candidates for today.\n\n{options}"
)
TEXT_CREATOR_ALTERNATIVE_ITEM_TEMPLATE = (
    "{index}. Rank #{rank}\n"
    "{text}\n"
    "Source: {source_url}"
)
TEXT_CREATOR_NO_ALTERNATIVES_TEMPLATE = (
    "There are no other grounded {purpose} candidates for today. "
    "I can keep refining the current draft."
)
TEXT_CREATOR_STALE_SELECTION = (
    "That candidate is no longer available. Tap Different post again."
)
TEXT_GENERATOR_PREFIX = {
    CommandName.POST_BY_INSPIRATION: "Draft post",
    CommandName.QUOTE: "Draft quote",
    CommandName.COMMENT: "Draft comment",
}
TEXT_RANDOM_FALLBACK = "Use /help to see available commands."
