from io import BytesIO

import httpx

from telebot.common.constants import HTTP_TIMEOUT_SECONDS


async def extract_pdf_text(url: str) -> str | None:
    from pypdf import PdfReader

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
    reader = PdfReader(BytesIO(response.content))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    content = "\n\n".join(pages).strip()
    return content or None
