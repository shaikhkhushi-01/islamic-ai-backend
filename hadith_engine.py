import json
from rapidfuzz import fuzz

with open("data/hadith.json", encoding="utf-8") as f:
    hadiths = json.load(f)


def search_hadith(query):

    query = query.lower()

    results = []

    for hadith in hadiths:

        score = max(
            fuzz.partial_ratio(query, hadith["topic"].lower()),
            fuzz.partial_ratio(query, hadith["text"].lower())
        )

        if score > 70:
            results.append(hadith)

    return results[:5]
