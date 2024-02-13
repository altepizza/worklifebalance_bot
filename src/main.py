from datetime import timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import settings
import database as database
from zoneinfo import ZoneInfo
from loguru import logger
from telegram.ext import CallbackContext
import requests

local_tz = ZoneInfo(settings.timezone)


def is_chat_id_allowed(chat_id: int) -> bool:
    return chat_id == int(settings.chat_id_whitelist)


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text="Go home!\n/clock_out")


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def clock_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_chat_id_allowed(update.effective_chat.id):
        local_datetime = update.message.date.astimezone(local_tz)
        database.clock_in(date_time=local_datetime)
        chat_id = update.effective_message.chat_id
        due = (
            settings.worktime_in_hours * 3600
            - database.calculate_overtime_undertime_in_h() * 3600
        )
        context.job_queue.run_once(
            alarm, due, chat_id=chat_id, name=str(chat_id), data=due
        )
        supposed_clock_out = local_datetime + timedelta(seconds=due)
        await update.effective_message.reply_text(
            f"""Clocked in at {local_datetime.strftime('%Y-%m-%d %H:%M:%S')}.\n
            You should clock out at {supposed_clock_out.strftime('%H:%M:%S')}.\n
            Your regular work end time is {(local_datetime + timedelta(seconds=settings.worktime_in_hours * 3600)).strftime('%H:%M:%S')} hours after clock in."""
        )


async def clock_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    if is_chat_id_allowed(update.effective_chat.id):
        local_datetime = update.message.date.astimezone(local_tz)

        database.clock_out(local_datetime)
        chat_id = update.message.chat_id
        remove_job_if_exists(str(chat_id), context)
        await update.message.reply_text(
            f"Clocked out at {local_datetime}. Your current time budget is {database.calculate_overtime_undertime_in_h()}."
        )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_chat_id_allowed(update.effective_chat.id):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            "/clock_in - Clock in\n/clock_out - Clock out\n/time_budget - Get time budget\n/help - Get help\n /get_entries - Get all entries\n"
        )


async def get_time_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_chat_id_allowed(update.effective_chat.id):
        """Send a message when the command /time_budget is issued."""
        await update.message.reply_text(
            f"Your time budget is {database.calculate_overtime_undertime_in_h()} hours"
        )


async def get_entries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_chat_id_allowed(update.effective_chat.id):
        df_string = "```" + database.get_work_times_as_df().to_markdown() + "```"
        await update.message.reply_text(text=df_string, parse_mode="MarkdownV2")


async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Exception while handling an update: {context.error}")

    error_message = f"An error occurred: {context.error}"

    webhook_url = settings.uptime_kuma_url
    data = {"msg": error_message}
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 200:
            logger.info("Error message successfully sent to Uptime Kuma")
        else:
            logger.error("Failed to send error message to Uptime Kuma")
    except Exception as e:
        logger.error(f"Failed to notify Uptime Kuma about the error: {e}")


def main() -> None:
    logger.info("""Run bot.""")
    logger.info(f"""Chat ID whitelist: {settings.chat_id_whitelist}""")
    logger.info(f"""Timezone: {settings.timezone}""")

    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("clock_in", clock_in))
    application.add_handler(CommandHandler("clock_out", clock_out))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("get_entries", get_entries))
    application.add_handler(CommandHandler("time_budget", get_time_budget))

    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
