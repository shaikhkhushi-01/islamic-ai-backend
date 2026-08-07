def calculate_confidence(context: str):

    if not context:
        return "25%"

    length = len(context)

    if length > 2000:
        return "99%"

    elif length > 1000:
        return "95%"

    elif length > 500:
        return "90%"

    elif length > 200:
        return "80%"

    return "65%"
