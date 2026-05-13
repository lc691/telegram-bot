from typing import TypedDict


class GroupShowResult(TypedDict):
    show_id: int
    title: str
    channel_id: int | None
    channel_username: str | None
    message_id: int
