"""Builds the per-category batch prompt sent to the LLM."""

# Local imports
from ..models import Item


def build_prompt(category: str, items: list[Item]) -> str:
    """One prompt for the whole category batch -> one JSON object back."""
    lines = [
        f"Summarize the following {len(items)} {category} stories.",
        "",
        'Return ONLY a JSON object of the form {"summaries": [ ... ]}, where '
        "each array element is an object with these string keys: "
        '"title", "url", "summary", "why".',
        "- title: echo the story's title.",
        "- url: echo the story's url EXACTLY as given.",
        "- summary: exactly two factual sentences, based on the provided info.",
        "- why: one short line stating the significance directly; do NOT begin "
        "it with 'It matters' or 'This matters'.",
        "Every value must be a JSON string in double quotes. Keep the array in "
        "the same order as the stories. No markdown fences, no prose outside "
        "the JSON.",
        "",
        "Stories:",
    ]
    for index, item in enumerate(items, 1):
        lines.append(f"[{index}] {item.title}")
        lines.append(f"    url: {item.url}")
        if item.content:
            lines.append(f"    content: {item.content}")
    return "\n".join(lines)
