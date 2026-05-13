def build_repost_caption(*, title: str, subtitle: str, link: str) -> str:
    return (
        f"<b>{title}</b>\n"
        f"{subtitle}\n"
        f'<b>Link:</b> <a href="{link}">{link}</a>'
    )
