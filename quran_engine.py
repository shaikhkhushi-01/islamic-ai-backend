import json
from rapidfuzz import fuzz

with open("data/quran.json", encoding="utf-8") as f:
    quran = json.load(f)


def search_quran(query):

    query = query.lower()

    results = []

    for verse in quran:

        score = max(

            fuzz.partial_ratio(
                query,
                verse["topic"].lower()
            ),

            fuzz.partial_ratio(
                query,
                verse["surah"].lower()
            ),

            fuzz.partial_ratio(
                query,
                verse["text"].lower()
            )

        )

        if score > 70:

            results.append({

                "surah": verse["surah"],

                "ayah": verse["ayah"],

                "text": verse["text"]

            })

    return results[:5]
