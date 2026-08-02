def normalize_show_row(row) -> dict | None:
    """
    Normalisasi row hasil search_exact / search_prefix / search_fuzzy
    ke kontrak domain ShowRow.

    Expected row layout:
    0: show_id
    1: title
    2: thumbnail_url
    3: channel_username
    4: message_id
    5: (optional) similarity score -> diabaikan
    """
    if not row or len(row) < 5:
        return None

    try:
        show_id = row[0]
        title = row[1]
        thumbnail_url = row[2]
        channel_username = row[3]
        message_id = row[4]

        # =============================
        # HARD GUARD DATA MINIMAL
        # =============================
        if not show_id or not title:
            return None

        return {
            "show_id": show_id,
            "title": title,
            "thumbnail_url": thumbnail_url,
            # Data Telegram (divalidasi di presenter)
            "channel_username": channel_username,
            "message_id": message_id,
            # Placeholder untuk private channel / future
            "channel_id": None,
        }

    except Exception:
        return None
