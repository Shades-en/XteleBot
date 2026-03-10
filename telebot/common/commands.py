from telebot.common.enums import CommandName

COMMAND_PREFIX = "/"
CALLBACK_PREFIX = "cmd:"
COMMAND_SEPARATOR = " "
BOT_COMMAND_SEPARATOR = "@"

COMMAND_DESCRIPTIONS = {
    CommandName.START: "Start onboarding",
    CommandName.HELP: "Show command panel",
    CommandName.PING: "Ping bot",
    CommandName.PING_WORKER: "Ping background worker",
    CommandName.CURRENT_USER: "Show current user details",
    CommandName.JOB_STATUS: "Show latest analysis job status",
    CommandName.RESET_SCHEMA: "Reset DB schema (development only)",
    CommandName.ANALYZE_TODAY: "Analyze today's X landscape",
    CommandName.REANALYZE_FOR_TODAY: "Delete today's analysis and run it again",
    CommandName.POST_BY_INSPIRATION: "Draft a fresh post",
    CommandName.QUOTE: "Draft a quote post",
    CommandName.COMMENT: "Draft a reply/comment",
    CommandName.SCHEDULE: "Show weekly action plan",
}

BUTTON_LABELS = {
    CommandName.START: "/start",
    CommandName.HELP: "/help",
    CommandName.PING: "/ping",
    CommandName.PING_WORKER: "/pingworker",
    CommandName.CURRENT_USER: "/currentuser",
    CommandName.JOB_STATUS: "/jobstatus",
    CommandName.ANALYZE_TODAY: "/analysetoday",
    CommandName.REANALYZE_FOR_TODAY: "/reanalysefortoday",
    CommandName.POST_BY_INSPIRATION: "/postbyinspiration",
    CommandName.QUOTE: "/quote",
    CommandName.COMMENT: "/comment",
    CommandName.SCHEDULE: "/schedule",
}

MENU_COMMANDS = [
    CommandName.START,
    CommandName.HELP,
    CommandName.PING,
    CommandName.PING_WORKER,
    CommandName.CURRENT_USER,
    CommandName.JOB_STATUS,
    CommandName.RESET_SCHEMA,
    CommandName.ANALYZE_TODAY,
    CommandName.REANALYZE_FOR_TODAY,
    CommandName.POST_BY_INSPIRATION,
    CommandName.QUOTE,
    CommandName.COMMENT,
    CommandName.SCHEDULE,
]

ACTION_COMMANDS = [
    CommandName.ANALYZE_TODAY,
    CommandName.REANALYZE_FOR_TODAY,
    CommandName.POST_BY_INSPIRATION,
    CommandName.QUOTE,
    CommandName.COMMENT,
    CommandName.SCHEDULE,
    CommandName.PING,
    CommandName.PING_WORKER,
    CommandName.CURRENT_USER,
    CommandName.JOB_STATUS,
]
