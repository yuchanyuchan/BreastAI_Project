from openai import OpenAI

from ..core.config import OPENAI_API_KEY, OPENAI_MODEL
from ..models.sns import GeneratedContent
from .style_service import load_style

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _format_papers(papers: list[dict]) -> str:
    lines = []
    for paper in papers:
        lines.append(
            f"- {paper['title']} ({paper.get('published_date', 'n.d.')}) {paper['url']}"
        )
    return "\n".join(lines)


PROMPT_TEMPLATE = """\
{context_label}:

{content_brief}

Using the above, produce:
- summary_ja: a clear, accessible summary in Japanese (for a general audience, not clinicians)
- x_post: a concise post for X (formerly Twitter), in Japanese, under 280 characters
- instagram_caption: an engaging Instagram caption in Japanese
- threads_post: a short Threads post in Japanese
- illustration_prompt: an English-language prompt for an image-generation model, describing a \
hopeful, respectful illustration suitable to accompany this content (no medical imagery that \
could be distressing)
"""


def generate_sns_content(
    account: str,
    papers: list[dict] | None = None,
    topic: str | None = None,
) -> GeneratedContent:
    client = _get_client()
    style = load_style(account)

    if papers:
        context_label = "Recent PubMed papers about breast cancer"
        content_brief = _format_papers(papers)
    else:
        context_label = "Topic"
        content_brief = topic or ""

    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=style,
        input=PROMPT_TEMPLATE.format(
            context_label=context_label, content_brief=content_brief
        ),
        text_format=GeneratedContent,
    )
    return response.output_parsed
