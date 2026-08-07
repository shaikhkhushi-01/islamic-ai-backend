import re


def validate_response(reply: str):

    forbidden = [
        "I think",
        "Maybe Allah",
        "Probably Allah",
        "I guess"
    ]

    for text in forbidden:
        if text.lower() in reply.lower():
            return False

    fake_quran = re.findall(
        r"Quran\s+\d+:\d+",
        reply
    )

    # Future me Quran DB se verify karenge

    return True
