from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_feedback_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text, callback_data=cb) for text, cb in row]
            for row in FEEDBACK_MENU
        ]
    )


FEEDBACK_MENU = [
    [
        ("🎬 Request Drama", "feedback:request_drama"),
        ("🐞 Lapor Masalah", "feedback:report"),
    ],
    [
        ("💡 Saran Fitur", "feedback:feature"),
        ("⭐ Rating Layanan", "feedback:rating"),
    ],
    [
        ("📊 Status Permintaan Saya", "feedback:my_ticket"),
    ],
]

