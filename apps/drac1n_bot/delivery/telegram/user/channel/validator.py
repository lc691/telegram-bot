from database.required_channel_repository import load_required_channels

async def validate_required_channels(app):
    channels = await load_required_channels(app)
    results = []

    for username in channels:
        try:
            chat = await app.get_chat(username)
            results.append((username, True, chat.title))
        except Exception:
            results.append((username, False, None))

    return results
