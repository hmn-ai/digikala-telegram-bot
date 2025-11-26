import os
import asyncio
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise Exception("TELEGRAM_BOT_TOKEN not set!")

def clean_price(text):
    if not text: return None
    trans = str.maketrans('۰۱۲۳۴۵۶۷۸۹٬,', '0123456789')
    cleaned = text.translate(trans).replace(',', '').strip()
    return int(cleaned) if cleaned.isdigit() else None

async def search_digikala(query: str):
    url = f"https://www.digikala.com/search/?q={query.replace(' ', '%20')}"
    products = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        for _ in range(12):
            await page.evaluate("window.scrollBy(0, 1200)")
            await asyncio.sleep(1.8)
        cards = await page.locator('a[data-testid="product-card"]').all()
        for card in cards[:25]:
            try:
                title = await card.locator('h3').inner_text(timeout=4000)
                price = clean_price(await card.locator('[data-testid="price-final"]').inner_text())
                if not price: continue
                discount = None
                if await card.locator('[data-testid="price-discount-percent"]').count() > 0:
                    discount = await card.locator('[data-testid="price-discount-percent"]').inner_text()
                old_price = None
                if await card.locator('[data-testid="price-no-discount"]').count() > 0:
                    old_price = clean_price(await card.locator('[data-testid="price-no-discount"]').inner_text())
                href = await card.get_attribute("href")
                link = "https://www.digikala.com" + href.split("?")[0]
                img = await card.locator("img").first.get_attribute("src") or "https://www.digikala.com/static/files/logo.svg"
                products.append({"title": title.strip()[:100], "price": price, "old_price": old_price, "discount": discount, "link": link, "image": img})
            except: continue
        await browser.close()
    return products

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! اسم محصول رو بفرست تا بهترین‌ها رو برات پیدا کنم")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f"در حال جستجو برای «{query}»...")
    try:
        products = await search_digikala(query)
        if not products:
            await update.message.reply_text("محصول پیدا نشد")
            return
        cheapest = sorted(products, key=lambda x: x["price"])[:3]
        for p in cheapest:
            text = f"{p['title']}\n*قیمت: {p['price']:,} تومان*"
            if p['discount']: text += f" ← {p['discount']}"
            keyboard = [[InlineKeyboardButton("خرید", url=p['link'])]]
            await update.message.reply_photo(p['image'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("خطایی رخ داد، دوباره امتحان کن")

async def main(request):
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize()
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=8080,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ['APPWRITE_FUNCTION_ENDPOINT']}/{TOKEN}"
    )
    await app.process_update(Update.de_json(request, app.bot))
    return {"status": "ok"}

def handle(event):
    return asyncio.run(main(event))
