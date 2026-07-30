import base64
import io
import uuid
from pathlib import Path

from openai import OpenAI
from PIL import Image

from ..core.config import OPENAI_API_KEY, OPENAI_IMAGE_MODEL, PUBLIC_BASE_URL

STATIC_DIR = Path(__file__).resolve().parents[1] / "static" / "generated"

# gpt-image-1's native portrait size, cropped down to Instagram's 4:5 feed ratio
# and upscaled to Instagram's own recommended feed resolution.
GENERATION_SIZE = "1024x1536"
FEED_SIZE = (1080, 1350)  # 4:5

PROMPT_SUFFIX = (
    " Style: clean, premium medical-aesthetic illustration; abstract or editorial, not "
    "generic stock-photo style. No patient photographs, no real identifiable people, no "
    "before-and-after comparison imagery, no fabricated statistics or clinical claims "
    "rendered as text in the image. Minimal or no embedded text. Vertical 4:5 composition."
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _crop_to_feed_ratio(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_ratio = FEED_SIZE[0] / FEED_SIZE[1]
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = round(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        new_height = round(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    image = image.resize(FEED_SIZE, Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_illustration(prompt: str, draft_id: uuid.UUID) -> tuple[str, str]:
    client = _get_client()
    response = client.images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=f"{prompt}{PROMPT_SUFFIX}",
        size=GENERATION_SIZE,
    )
    raw_bytes = base64.b64decode(response.data[0].b64_json)
    image_bytes = _crop_to_feed_ratio(raw_bytes)

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{draft_id}.png"
    image_path = STATIC_DIR / filename
    image_path.write_bytes(image_bytes)

    image_url = f"{PUBLIC_BASE_URL.rstrip('/')}/static/generated/{filename}"
    return str(image_path), image_url
