import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import init_db, get_conn
from lead_generator import fetch_tokens, filter_tokens, generate_pitch, save_lead
from config import TELEGRAM_TOKEN

init_db()

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /generate 20")
        return

    amount = int(context.args[0])
    await update.message.reply_text("Generating leads...")

    pairs = fetch_tokens()
    filtered = filter_tokens(pairs)

    count = 0
    for token in filtered[:amount]:
        pitch = generate_pitch(token)
        save_lead(token, pitch)
        count += 1

    await update.message.reply_text(f"{count} leads generated.")

async def lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT active_lead_id FROM reps WHERE telegram_id=%s", (telegram_id,))
    rep = cur.fetchone()

    if rep and rep[0]:
        await update.message.reply_text("You have an active lead.")
        return

    cur.execute("SELECT id, token_name, pitch FROM leads WHERE status='available' LIMIT 1")
    lead = cur.fetchone()

    if not lead:
        await update.message.reply_text("No leads available.")
        return

    lead_id, token_name, pitch = lead

    cur.execute("UPDATE leads SET status='assigned' WHERE id=%s", (lead_id,))
    cur.execute("""
        INSERT INTO reps (telegram_id, active_lead_id)
        VALUES (%s, %s)
        ON CONFLICT (telegram_id)
        DO UPDATE SET active_lead_id=%s
    """, (telegram_id, lead_id, lead_id))

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(f"Token: {token_name}\n\nPitch:\n{pitch}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("generate", generate))
app.add_handler(CommandHandler("lead", lead))

app.run_polling()
