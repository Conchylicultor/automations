"""Text processing utils."""

from auto_notion.typing import Json


def json_to_str(json: Json) -> str:
    # TODO: This will lose all annotations & type
    parts = [elem["plain_text"] for elem in json]
    return "".join(parts)


def str_to_json(text: str) -> Json:
    return [
        {
            "text": {
                "content": text,
            },
        },
    ]
