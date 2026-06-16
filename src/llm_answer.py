"""Optional OpenAI answer generation for the AIP query workspace."""

import json


DEFAULT_MODEL = "gpt-5.5"


def _source_context(sources):
    compact_sources = []
    for index, source in enumerate(sources, start=1):
        compact_sources.append(
            {
                "citation_id": f"SOURCE-{index}",
                "source": source.get("source", ""),
                "record_id": str(source.get("record_id", "")),
                "title": str(source.get("title", "")),
                "summary": str(source.get("summary", "")),
            }
        )
    return compact_sources


def generate_grounded_answer(question, draft_answer, insights, sources, api_key, model=None):
    """Use OpenAI to turn retrieved rows into a better grounded answer."""
    if not api_key:
        return None
    if "your-openai-api-key" in api_key.lower() or api_key.strip().startswith("your-"):
        return {
            "error": "OpenAI API key is still set to the placeholder value. Replace it in Streamlit secrets with a real key from the OpenAI platform.",
            "answer": draft_answer,
            "insights": insights,
        }

    try:
        from openai import OpenAI
    except ImportError as exc:
        return {
            "error": f"OpenAI package is not installed: {exc}",
            "answer": draft_answer,
            "insights": insights,
        }

    client = OpenAI(api_key=api_key)
    selected_model = model or DEFAULT_MODEL
    source_context = _source_context(sources)

    instructions = """
You are an asset investment planning assistant for a highways asset management prototype.
Answer only from the provided source rows and draft deterministic analysis.
Do not use outside knowledge.
If the source rows are not enough, say what is missing.
Use British English.
Keep the answer concise and practical.
Mention citation ids such as SOURCE-1 when making a claim.
Return valid JSON with these keys:
- answer: a concise answer in plain English
- insights: an array of exactly three practical insight strings
"""

    payload = {
        "question": question,
        "draft_answer": draft_answer,
        "draft_insights": insights,
        "source_rows": source_context,
    }

    try:
        response = client.responses.create(
            model=selected_model,
            instructions=instructions,
            input=json.dumps(payload, indent=2),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "aip_answer",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "answer": {"type": "string"},
                            "insights": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 3,
                            },
                        },
                        "required": ["answer", "insights"],
                    },
                    "strict": True,
                }
            },
        )
        parsed = json.loads(response.output_text)
        return {
            "answer": parsed["answer"],
            "insights": parsed["insights"],
            "model": selected_model,
        }
    except Exception as exc:
        message = str(exc)
        if "invalid_api_key" in message or "Incorrect API key" in message or "401" in message:
            message = (
                "OpenAI rejected the API key. Check Streamlit secrets and replace "
                "OPENAI_API_KEY with a valid key from the OpenAI platform."
            )
        elif (
            "insufficient_quota" in message
            or "exceeded your current quota" in message
            or "billing details" in message
        ):
            message = (
                "OpenAI API quota is unavailable for this key. Check the OpenAI platform "
                "usage, billing, project budget and monthly limits. The app is showing "
                "the local prototype answer instead."
            )
        elif "rate limit" in message.lower() or "429" in message:
            message = (
                "OpenAI rate limiting is active. Wait briefly or reduce repeated requests. "
                "The app is showing the local prototype answer instead."
            )
        return {
            "error": message,
            "answer": draft_answer,
            "insights": insights,
        }
