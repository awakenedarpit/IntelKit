from telegram.ext import Application, CommandHandler, MessageHandler, filters
from .handlers import start, help_cmd, status, photo, video, text

def build_application(settings, manager, extractor=None):
    if not settings.telegram_bot_token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is required to start the bot')
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data['manager'] = manager
    if extractor is not None:
        app.bot_data['extractor'] = extractor
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(MessageHandler(filters.VIDEO, video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    return app
