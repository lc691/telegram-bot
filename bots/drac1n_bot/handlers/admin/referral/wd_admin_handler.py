# ============================================
# withdraw_admin_handler.py — CALLBACK VERSION
# ============================================

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from common.utils.admin_cache import admin_cache
from configs.logging_setup import log
from db.affiliate_admin_audit import log_admin_action
from db.connect import get_db_cursor


def is_admin(user_id):
    return user_id in admin_cache.admin_ids


# =========================
# CALLBACK ROUTER
# =========================
@Client.on_callback_query(filters.regex(r"^wd:(approve|reject):(\d+)$"))
async def wd_callback_handler(client: Client, cq):
    admin_id = cq.from_user.id

    if not is_admin(admin_id):
        return await cq.answer("🚫 Akses ditolak.", show_alert=True)

    action = cq.matches[0].group(1)
    wd_id = int(cq.matches[0].group(2))

    if action == "approve":
        await process_wd_approve(client, cq, admin_id, wd_id)

    elif action == "reject":
        await process_wd_reject(client, cq, admin_id, wd_id)


# =========================
# PROCESS APPROVE
# =========================
async def process_wd_approve(bot, cq, admin_id, wd_id):
    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("""
                SELECT user_id, amount, status
                FROM affiliate_withdraw_requests
                WHERE id=%s
                FOR UPDATE
            """, (wd_id,))
            row = cursor.fetchone()

            if not row:
                return await cq.answer("❌ WD tidak ditemukan.", show_alert=True)

            user_id, amount, status = row

            if status != "pending":
                return await cq.answer("⚠️ WD sudah diproses.", show_alert=True)

            cursor.execute("""
                UPDATE affiliate_withdraw_requests
                SET status='approved',
                    admin_id=%s,
                    reviewed_at=NOW()
                WHERE id=%s AND status='pending'
            """, (admin_id, wd_id))

        await cq.message.edit_text(
            f"✅ <b>WD APPROVED</b>\n\n"
            f"ID: <code>{wd_id}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Amount: Rp {amount:,}\n\n"
            f"By admin: <code>{admin_id}</code>",
            parse_mode=ParseMode.HTML
        )

        await bot.send_message(
            user_id,
            f"🎉 <b>Withdraw disetujui!</b>\n\n"
            f"ID: <code>{wd_id}</code>\n"
            f"Jumlah: Rp {amount:,}\n",
            parse_mode=ParseMode.HTML
        )

        await cq.answer("✅ Approved")

        log_admin_action(
            admin_id=admin_id,
            action="withdraw_approve",
            target_type="affiliate_withdraw",
            target_id=wd_id,
            notes=f"amount={amount}"
        )

        log.info(f"[WD_APPROVE] admin={admin_id} id={wd_id} user={user_id} amount={amount}")

    except Exception as e:
        log.error(f"[WD_APPROVE] ERROR: {e}", exc_info=True)
        await cq.answer("❌ Error server", show_alert=True)


# =========================
# PROCESS REJECT
# =========================
async def process_wd_reject(bot, cq, admin_id, wd_id):
    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("""
                SELECT user_id, amount, status
                FROM affiliate_withdraw_requests
                WHERE id=%s
                FOR UPDATE
            """, (wd_id,))
            row = cursor.fetchone()

            if not row:
                return await cq.answer("❌ WD tidak ditemukan.", show_alert=True)

            user_id, amount, status = row

            if status != "pending":
                return await cq.answer("⚠️ WD sudah diproses.", show_alert=True)

            # Refund
            cursor.execute("""
                UPDATE users
                SET affiliate_balance = affiliate_balance + %s
                WHERE user_id = %s
            """, (amount, user_id))

            cursor.execute("""
                UPDATE affiliate_withdraw_requests
                SET status='rejected',
                    admin_id=%s,
                    reviewed_at=NOW(),
                    notes='Rejected by admin'
                WHERE id=%s AND status='pending'
            """, (admin_id, wd_id))

        await cq.message.edit_text(
            f"❌ <b>WD REJECTED</b>\n\n"
            f"ID: <code>{wd_id}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Refund: Rp {amount:,}\n\n"
            f"By admin: <code>{admin_id}</code>",
            parse_mode=ParseMode.HTML
        )

        await bot.send_message(
            user_id,
            f"❌ <b>Withdraw ditolak.</b>\n\n"
            f"ID: <code>{wd_id}</code>\n"
            f"Saldo telah dikembalikan.",
            parse_mode=ParseMode.HTML
        )

        await cq.answer("❌ Rejected")

        log_admin_action(
            admin_id=admin_id,
            action="withdraw_reject",
            target_type="affiliate_withdraw",
            target_id=wd_id,
            notes="Rejected by admin"
        )


        log.info(f"[WD_REJECT] admin={admin_id} id={wd_id} user={user_id} refund={amount}")

    except Exception as e:
        log.error(f"[WD_REJECT] ERROR: {e}", exc_info=True)
        await cq.answer("❌ Error server", show_alert=True)


# =========================
# ADMIN MESSAGE BUILDER
# =========================
def build_admin_withdraw_message(wd_id, user_id, amount, method, target):
    return (
        f"📢 <b>Withdraw Request</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"ID: <code>{wd_id}</code>\n"
        f"User: <code>{user_id}</code>\n"
        f"Method: <b>{method}</b>\n"
        f"Amount: Rp {amount:,}\n"
        f"Target: <code>{target}</code>\n\n"
        f"Pilih aksi:"
    )


def build_admin_buttons(wd_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"wd:approve:{wd_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"wd:reject:{wd_id}")
        ]
    ])
