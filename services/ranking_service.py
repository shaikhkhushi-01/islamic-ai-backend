from difflib import SequenceMatcher


def keyword_score(query: str, topic: str):

    query = query.lower()
    topic = topic.lower()

    if topic in query:
        return 100

    return int(
        SequenceMatcher(
            None,
            query,
            topic
        ).ratio() * 100
    )


def rank_results(query, results):

    ranked = []

    for item in results:

        score = keyword_score(
            query,
            item["topic"]
        )

        ranked.append(
            (
                score,
                item
            )
        )

    ranked.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    return [
        x[1]
        for x in ranked
    ]
