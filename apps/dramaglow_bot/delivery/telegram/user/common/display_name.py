def get_user_display(row: dict) -> str:
    """
    Prioritas tampilan user:
    1. username (valid & bukan '-')
    2. first_name
    3. User <id>
    """
    username = (row.get("username") or "").strip()
    if username and username != "-" and not username.startswith("@"):
        return f"@{username}"

    first_name = (row.get("first_name") or "").strip()
    if first_name:
        return first_name

    return f"User {row.get('user_id', '?')}"


from pyrogram.types import User


def get_display_name(user: User, fallback: str | None = None) -> str:
    return (
        f"@{user.username}"
        if user.username
        else user.first_name or fallback or f"user{user.id}"
    )
