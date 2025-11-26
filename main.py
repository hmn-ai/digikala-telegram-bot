import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cloudscraper
from bs4 import BeautifulSoup
import re

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
app = Application.builder().token(TOKEN).build()

def clean_price(text):
    if not text: return None
    return int(re.sub(r"[^\d]", "", text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹, "0123456789"))))

def scrape_digikala(query):
    scraper = cloudscraper.create_scraper()
    url = f"https://www.digikala.com/search/?q={query.replace(' ', '%20')}"
    try:
        html = scraper.get(url, timeout=15).text
        soup = BeautifulSoup(html, "lxml")
        products = []
        for item in soup.select('a[data-testid="product-card"]')[:15]:
            try:
                title = item.select_one('h3').get_text(strip=True)[:100]
                price = clean_price(item.select_one('[data-testid="price-final"]') .get_text())
                if not price: continue
                discount = item.select_one('[data-testid="price-discount-percent"]')
                discount = discount.get_text(strip=True) if discount else None
                link = "https://www.digikala.com + item['href'].split('?')[0]
                img = item.select_one('img').get('src', '') or https://www.digikala.com/static/files/logo.svg
                products.append({"title": title, "price": price, "discount": discount, "link": link, "image": img})
            except: continue
        return products
    except: return []

@app.on_message(filters.Command("start"))
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! اسم محصول رو بفرست تا بهترین‌ها رو برات پیدا کنم")

@app.on_message(filters.TEXT & ~filters.COMMAND)
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f"در حال جستجو برای «{query}»...")
    products = scrape_digikala(query)
    if not products:
        await update.message.reply_text("محصول پیدا نشد")
        return
    cheapest = sorted(products, key=lambda x: x["price"])[:3]
    for p in cheapest:
        text = f"{p['title']}\n*قیمت: {p['price']:,} تومان*"
        if p['discount']: text += f"  ←  {p['discount']}"
        keyboard = [[InlineKeyboardButton("خرید از دیجی‌کالا", url=p['link'])]]
        await update.message.reply_photo(p['image'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def handle(event):
    try:
        body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})
        update = Update.de_json(body, app.bot)
        if update.message.reply_text = update.message.reply_text  # fix
        asyncio.create_task(app.process_update(update))
        return {"statusCode": 200, "body": "ok"}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}

# این خط حتماً باید باشه برای Appwrite
export async def main(event):
    return handle(event)
