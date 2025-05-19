from telegram import Update, InlineQueryResultPhoto
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import random

PAGE_URL = 'https://sexpositions.club/'
HEADERS = { "User-Agent": "Mozilla/5.0" }
cached_images = []
user_languages = {}  # idioma por usuario

# Diccionario de textos multilingües
TEXTS = {
    'start': {
        'es': "Hola! Soy tu bot de posiciones sexuales 🔥\nUsa /position <número> o /position random para una imagen hot 💦",
        'en': "Hi! I'm your sexual positions bot 🔥\nUse /position <number> or /position random to get a hot image 💦"
    },
    'help': {
        'es': "Comandos:\n/start\n/help\n/position <número|random>\n/language <es|en>",
        'en': "Commands:\n/start\n/help\n/position <number|random>\n/language <es|en>"
    },
    'no_image': {
        'es': "No se encontró una imagen válida. Intenta otro número.",
        'en': "No valid image found. Try another number."
    },
    'usage': {
        'es': "Uso correcto: /position <número|random>",
        'en': "Correct usage: /position <number|random>"
    },
    'error': {
        'es': "Ocurrió un error: ",
        'en': "An error occurred: "
    },
    'lang_set': {
        'es': "Idioma cambiado a español 🇪🇸",
        'en': "Language set to English 🇺🇸"
    },
    'invalid_lang': {
        'es': "Idioma no válido. Usa /language es o /language en",
        'en': "Invalid language. Use /language es or /language en"
    }
}

# Obtener texto traducido

def t(key, user_id):
    lang = user_languages.get(user_id, 'es')
    return TEXTS[key][lang]

# Cargar lista negra desde archivo
def cargar_blacklist():
    try:
        with open("blacklist.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    except:
        return []

BLACKLIST = cargar_blacklist()

# Extraer y filtrar imágenes

def fetch_and_cache_images():
    global cached_images
    try:
        print("🔄 Obteniendo imágenes...")
        response = requests.get(PAGE_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all('img')

        valid_images = []
        for img in images:
            src = img.get('src', '')
            if src:
                if src.lower().endswith('.gif'):
                    continue
                full_url = urljoin(PAGE_URL, src)
                if full_url not in BLACKLIST:
                    if 'pos' in src or '/positions/' in src:
                        valid_images.append(full_url)

        cached_images = valid_images
        print(f"✅ {len(valid_images)} imágenes válidas")
    except Exception as e:
        print(f"[ERROR] fetch_and_cache_images: {e}")
        cached_images = []

def get_image_url(position):
    if not cached_images:
        fetch_and_cache_images()
    if 0 < position <= len(cached_images):
        return cached_images[position - 1]
    return None

def get_random_image_url():
    if not cached_images:
        fetch_and_cache_images()
    if cached_images:
        return random.choice(cached_images)
    return None

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t('start', update.effective_user.id))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t('help', update.effective_user.id))

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lang = context.args[0].lower()
        if lang in ['es', 'en']:
            user_languages[update.effective_user.id] = lang
            await update.message.reply_text(t('lang_set', update.effective_user.id))
        else:
            await update.message.reply_text(t('invalid_lang', update.effective_user.id))
    except IndexError:
        await update.message.reply_text(t('invalid_lang', update.effective_user.id))

async def send_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        arg = context.args[0].lower()
        if arg == "random":
            image_url = get_random_image_url()
        else:
            number = int(arg)
            image_url = get_image_url(number)

        if image_url:
            await update.message.reply_photo(photo=image_url)
        else:
            await update.message.reply_text(t('no_image', update.effective_user.id))
    except (IndexError, ValueError):
        await update.message.reply_text(t('usage', update.effective_user.id))
    except Exception as e:
        await update.message.reply_text(t('error', update.effective_user.id) + str(e))

# Inline Query
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if query.lower() == "random":
        image_url = get_random_image_url()
        index = cached_images.index(image_url) + 1 if image_url in cached_images else 0
    elif query.isdigit():
        index = int(query)
        image_url = get_image_url(index)
    else:
        return

    if not image_url:
        return

    results = [
        InlineQueryResultPhoto(
            id=str(index),
            title=f"Posición {index}" if query != "random" else "Posición aleatoria",
            photo_url=image_url,
            thumbnail_url=image_url,
            caption=f"🔥 Posición sexual #{index}" if query != "random" else "🔥 Posición sexual aleatoria"
        )
    ]

    await update.inline_query.answer(results, cache_time=1)

# Detectar menciones o texto en privado
async def detectar_mencion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text or ""
    username = context.bot.username.lower()

    match = re.search(rf"@{username}\\s*(\\d+|random)", texto, re.IGNORECASE)
    if not match and update.message.chat.type == "private":
        match = re.search(rf"(\\d+|random)", texto.strip(), re.IGNORECASE)

    if match:
        arg = match.group(1).lower()
        if arg == "random":
            image_url = get_random_image_url()
        else:
            image_url = get_image_url(int(arg))

        if image_url:
            await update.message.reply_photo(photo=image_url)
        else:
            await update.message.reply_text(t('no_image', update.effective_user.id))

# Main

def main():
    TOKEN = "7764246309:AAG_lSckqmeTyj0St_Yxg4bICaNREzthj9U"
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=60.0)
    app = Application.builder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("position", send_position))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), detectar_mencion))

    print("🤖 Bot corriendo... Usa /position <número|random>, @TuBot 4 o solo 4 en privado")
    app.run_polling()

if __name__ == '__main__':
    main()
