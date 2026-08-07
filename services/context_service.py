def has_enough_context(context):

    if not context:
        return False

    if len(context.strip()) < 100:
        return False

    return True
