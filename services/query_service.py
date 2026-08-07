import re


def rewrite_query(query: str):

    query = query.lower().strip()

    replacements = {

        "namaz": "prayer",
        "roza": "fasting",
        "dua": "supplication",
        "allah": "allah",
        "gunah": "sin",
        "jannat": "jannah",
        "jahannum": "jahannam",
        "makkah": "mecca",
        "madina": "medina",
        "rasool": "prophet muhammad",

        # Urdu
        "namaz ka tareeqa": "how to pray",
        "wazu": "wudu",
        "roza kaise rakhe": "how to fast",

        # Hindi
        "prarthana": "prayer"
    }

    for old, new in replacements.items():

        query = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            query
        )

    return query
