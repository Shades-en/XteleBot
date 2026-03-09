from telebot.common.constants import COMMON_ADVANCED_SEARCH_FILTERS, TOPIC_QUERY_SEEDS


def build_seed_queries(current_username: str | None) -> list[str]:
    exclude = f" -from:{current_username}" if current_username else ""
    return [f"{seed} {COMMON_ADVANCED_SEARCH_FILTERS}{exclude}" for seed in TOPIC_QUERY_SEEDS]


def build_own_posts_query(username: str) -> str:
    return f"from:{username} {COMMON_ADVANCED_SEARCH_FILTERS}"
