import re


def extract_references(text: str):

    references = []

    quran = re.findall(
        r"Quran\s*\d+:\d+",
        text,
        re.IGNORECASE
    )

    hadith = re.findall(
        r"(Sahih Bukhari|Sahih Muslim|Abu Dawood|Tirmidhi)\s*\d+",
        text,
        re.IGNORECASE
    )

    references.extend(quran)
    references.extend(hadith)

    return list(set(references))
