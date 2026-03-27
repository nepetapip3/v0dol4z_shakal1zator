import logging
import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

BOT_TOKEN = "token here"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAITING_FOR_IMAGE = 1
WAITING_FOR_LEVEL = 2


def shakalize(image_bytes: bytes, level: int) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    level_params = {
        1:  (85, 1.00, 1),
        2:  (70, 0.95, 1),
        3:  (55, 0.85, 2),
        4:  (40, 0.75, 2),
        5:  (30, 0.65, 3),
        6:  (20, 0.55, 3),
        7:  (12, 0.45, 4),
        8:  (6,  0.35, 5),
        9:  (3,  0.25, 6),
        10: (1,  0.15, 8),
    }

    quality, scale, passes = level_params[level]

    for _ in range(passes):
        w = max(16, int(img.width * scale))
        h = max(16, int(img.height * scale))
        img = img.resize((w, h), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=False)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")

        if _ < passes - 1:
            orig_w = Image.open(io.BytesIO(image_bytes)).width
            orig_h = Image.open(io.BytesIO(image_bytes)).height
            img = img.resize((orig_w, orig_h), Image.NEAREST)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=quality)
    output.seek(0)
    return output.read()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "это v0dol4z shakal1zator\n\n"
        "автора этого бота доебал другой популярный бот для шакала картинок поэтому он навайбкодил своего :)\n"
        "автор @nepetapip3\n\n"
        "кинь картинку — и я доведу её до нужной степени шакальности.\n"
        "пришли мне фото:\n"
    )
    return WAITING_FOR_IMAGE


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "немного предыстории\n\n"
        "изначально это должен быть .sh скрипт но т.к он вышел пипец каким скучным я забросил это дело, и решил вернуться переделав идею под сайт\n"
        "сайт оказался тоже хренью, я не мог добиться того чего я хотел, но тут я решил так сказать вернуться к истокам и переделать все под телеграм бота\n"
        "как то так :-)"
    )


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo
    document = update.message.document

    if photo:
        file_id = photo[-1].file_id
    elif document and document.mime_type and document.mime_type.startswith("image/"):
        file_id = document.file_id
    else:
        await update.message.reply_text("это не картинка. пришли фото или изображение как файл.")
        return WAITING_FOR_IMAGE

    context.user_data["file_id"] = file_id

    keyboard = [
        [
            InlineKeyboardButton("1 🙂", callback_data="1"),
            InlineKeyboardButton("2 😐", callback_data="2"),
            InlineKeyboardButton("3 😑", callback_data="3"),
            InlineKeyboardButton("4 😬", callback_data="4"),
            InlineKeyboardButton("5 🤢", callback_data="5"),
        ],
        [
            InlineKeyboardButton("6 💀", callback_data="6"),
            InlineKeyboardButton("7 ☠️", callback_data="7"),
            InlineKeyboardButton("8 🗑️", callback_data="8"),
            InlineKeyboardButton("9 🧟", callback_data="9"),
            InlineKeyboardButton("10 👹", callback_data="10"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "до какого уровня зашакалить?\n\n"
        "1 — лёгкий жир | 10 — абсолютная бурмалда",
        reply_markup=reply_markup,
    )
    return WAITING_FOR_LEVEL


async def receive_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    level = int(query.data)
    file_id = context.user_data.get("file_id")

    if not file_id:
        await query.message.reply_text("что-то пошло не так. пришли картинку заново.")
        return WAITING_FOR_IMAGE

    await query.message.reply_text(f"шакализирую до уровня {level}... подожди немного.")

    try:
        tg_file = await context.bot.get_file(file_id)
        image_bytes = await tg_file.download_as_bytearray()

        result_bytes = shakalize(bytes(image_bytes), level)

        captions = {
            1:  "Уровень 1: почти незаметно 🙂",
            2:  "Уровень 2: немного хуева 😐",
            3:  "Уровень 3: артефакты пошли 😑",
            4:  "Уровень 4: уже заметно 😬",
            5:  "Уровень 5: среднестатистический шакал 🤢",
            6:  "Уровень 6: мама, я боюсь 💀",
            7:  "Уровень 7: пиксели плачут ☠️",
            8:  "Уровень 8: это уже не картинка 🗑️",
            9:  "Уровень 9: артефакт из ада 🧟",
            10: "Уровень 10: шакал уровня 999 👹",
        }

        await query.message.reply_document(
            document=io.BytesIO(result_bytes),
            filename=f"shakal_level_{level}.jpg",
            caption=captions[level],
        )

    except Exception as e:
        logger.error(f"Ошибка шакализации: {e}")
        await query.message.reply_text("ошибка при обработке. попробуй другую картинку.")

    await query.message.reply_text("хочешь ещё? кидай следующую картинку 📎")
    return WAITING_FOR_IMAGE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("отменено. напиши /start чтобы начать заново.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_IMAGE: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_image)
            ],
            WAITING_FOR_LEVEL: [
                CallbackQueryHandler(receive_level)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("info", info))

    print("🤖 Бот запущен. Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()