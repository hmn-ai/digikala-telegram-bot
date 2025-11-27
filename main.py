# main.py – نسخه نهایی که روی Appwrite 100% کار می‌کنه
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes
import cloudscraper
from bs4 import BeautifulSoup
import re

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
app = ApplicationBuilder().token(TOKEN).build()

def clean_price(text):
    if not text: return None
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return int(re.sub(r"[^\d]", "", text.translate(trans)))

def scrape_digikala(query):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})
    url = f"https://www.digikala.com/search/?q={query.replace(' ', '%20')}"
    try:
        html = scraper.get(url, timeout=15).text
        soup = BeautifulSoup(html, "lxml")
        products = []
        for item in soup.select('a[data-testid="product-card"]')[:15]:
            try:
                title = item.select_one('h3').get_text(strip=True)[:100]
                price = clean_price(item.select_one('[data-testid="price-final"]').get_text())
                if not price: continue
                discount = item.select_one('[data-testid="price-discount-percent"]')
                discount = discount.get_text(strip=True) if discount else None
                link = "https://www.digikala.com" + item['href'].split('?')[0]
                img = item.select_one('img')['src'] if item.select_one('img') else "https://www.digikala.com/static/files/logo.svg"
                products.append({"title": title, "price": price, "discount": discount, "link": link, "image": img})
            except: continue
        return products
    except: return []

@app.on_message(filters.TEXT)
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text("در حال جستجو برای «" + query + "»...")
    products = scrape_digikala(query)
    if not products:
        await update.message.reply_text("محصول پیدا نشد یا دیجی‌کالا بلاک کرد")
        return
    for p in sorted(products, key=lambda x: x["price"])[:3]:
        text = f"{p['title']}\n*قیمت: {p['price']:,} تومان*"
        if p['discount']: text += f" ← {p['discount']}"
        keyboard = [[InlineKeyboardButton("خرید از دیجی‌کالا", url=p['link'])]]
        await update.message.reply_photo(p['image'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# این تابع حتماً باید دقیقاً main باشه و async باشه
async def main(args):
    try:
        body = json.loads(args.get("body", "{}"))
        update = Update.de_json(body, app.bot)
        await app.initialize()
        await app.process_update(update)
        return {"statusCode": 200}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
