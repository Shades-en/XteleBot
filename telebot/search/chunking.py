from langchain_text_splitters import RecursiveCharacterTextSplitter

from telebot.common.constants import WEB_RESEARCH_CHUNK_OVERLAP, WEB_RESEARCH_CHUNK_SIZE


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=WEB_RESEARCH_CHUNK_SIZE,
        chunk_overlap=WEB_RESEARCH_CHUNK_OVERLAP,
        add_start_index=False,
    )


def chunk_text(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    return [chunk for chunk in _splitter().split_text(normalized) if chunk]
