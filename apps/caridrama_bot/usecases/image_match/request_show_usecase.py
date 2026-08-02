from ..request.save_show_request import save_show_request


def request_show_usecase(user_id: int, ref: str):
    save_show_request(user_id, ref)
