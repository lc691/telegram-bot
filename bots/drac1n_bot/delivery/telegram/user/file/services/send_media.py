# from pyrogram.enums import ParseMode
# from pyrogram.types import (
#     InputMediaVideo,
#     InputMediaDocument,
# )
# from pyrogram.errors import MessageNotModified, BadRequest
# from configs.logging_setup import log


# def build_media(file: dict, caption: str):
#     """
#     Build InputMedia sesuai tipe file.

#     Catatan:
#     - Aman untuk edit_media SELAMA tipe media konsisten
#     - Fallback ke reply ditangani di send_media
#     """
#     file_type = file.get("file_type")

#     if file_type == "video":
#         return InputMediaVideo(
#             media=file["file_id"],
#             caption=caption,
#             parse_mode=ParseMode.HTML,
#         )

#     # default: document
#     return InputMediaDocument(
#         media=file["file_id"],
#         caption=caption,
#         parse_mode=ParseMode.HTML,
#     )


# async def send_media(
#     message,
#     *,
#     file: dict,
#     caption: str,
#     keyboard,
#     edit: bool,
# ):
#     """
#     Kirim atau edit media dengan caption & keyboard.

#     Rules:
#     - edit=True  → TRY edit_media
#     - edit=False → reply_* sesuai tipe file
#     - Jika edit gagal → fallback ke reply
#     """

#     reply_markup = keyboard or None

#     # ==================================================
#     # 1️⃣ TRY EDIT (SAFE)
#     # ==================================================
#     if edit:
#         try:
#             media = build_media(file, caption)
#             return await message.edit_media(
#                 media=media,
#                 reply_markup=reply_markup,
#             )

#         except MessageNotModified:
#             return

#         except BadRequest as e:
#             log.warning(
#                 "[SEND_MEDIA] edit failed, fallback to reply: %s",
#                 e,
#             )

#         except Exception:
#             log.exception("[SEND_MEDIA] unexpected edit error")

#         # FALLBACK → kirim pesan baru
#         edit = False

#     # ==================================================
#     # 2️⃣ SEND NEW MESSAGE
#     # ==================================================
#     if file.get("file_type") == "video":
#         sender = message.reply_video
#     else:
#         sender = message.reply_document

#     return await sender(
#         file["file_id"],
#         caption=caption,
#         parse_mode=ParseMode.HTML,
#         reply_markup=reply_markup,
#     )


from pyrogram.enums import ParseMode
from pyrogram.types import (
    InputMediaVideo,
    InputMediaDocument,
)
from pyrogram.errors import MessageNotModified, BadRequest
from configs.logging_setup import log


def build_media(file: dict, caption: str):
    file_type = file.get("file_type")

    if file_type == "video":
        return InputMediaVideo(
            media=file["file_id"],
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

    return InputMediaDocument(
        media=file["file_id"],
        caption=caption,
        parse_mode=ParseMode.HTML,
    )


async def send_media(
    message,
    *,
    file: dict,
    caption: str,
    keyboard,
    edit: bool,
):
    """
    Anti forward + anti save + anti copy
    menggunakan protect_content=True
    """

    reply_markup = keyboard or None
    chat_id = message.chat.id

    # =====================================
    # 1. TRY EDIT MEDIA
    # =====================================
    if edit:
        try:
            media = build_media(file, caption)

            return await message.edit_media(
                media=media,
                reply_markup=reply_markup,
            )

        except MessageNotModified:
            return

        except BadRequest as e:
            log.warning(
                "[SEND_MEDIA] edit failed → fallback reply: %s",
                e,
            )

        except Exception:
            log.exception("[SEND_MEDIA] unexpected edit_media error")

        edit = False

    # =====================================
    # 2. SEND NEW MESSAGE (SAFE)
    # =====================================
    client = message._client

    if file.get("file_type") == "video":
        return await client.send_video(
            chat_id=chat_id,
            video=file["file_id"],
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            # anti forward/save/copy
            protect_content=True,
            # reply ke message sebelumnya
            reply_to_message_id=message.id,
        )

    return await client.send_document(
        chat_id=chat_id,
        document=file["file_id"],
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        # anti forward/save/copy
        protect_content=True,
        reply_to_message_id=message.id,
    )
