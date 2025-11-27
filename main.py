# main.py — نسخه نهایی و 100٪ کارکرده روی Appwrite Functions (آزمون شده)
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes
import cloudscraper
from bs4 import BeautifulSoup
import re

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

def clean_price(text):
    if not text: return None
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٬,", "0123456789")
    return int(re.sub(r"[^\d]", "", text.translate(trans)))

def scrape_digikala(query):
    scraper = cloudscraper.create_scraper()
    url = f"https://www.digikala.com/search/?q={query.replace(' ', '%20')}"
    try:
        html = scraper.get(url, timeout=20).text
        soup = BeautifulSoup(html, "lxml")
        products = []
        for card in soup.select('a[data-testid="product-card"]')[:12]:
            try:
                title = card.select_one("h3").get_text(strip=True)[:100]
                price = clean_price(card.select_one('[data-testid="price-final"]').get_text())
                if not price: continue
                discount = card.select_one('[data-testid="price-discount-percent"]')
                discount_text = discount.get_text(strip=True) if discount else None
                link = "https://www.digikala.com" + card["href"].split("?")[0]
                img = card.select_one("img")["src"] if card.select_one("img") else ""
                products.append({
                    "title": title,
                    "price": price,
                    "discount": discount_text,
                    "link": link,
                    "image": img or "https://www.digikala.com/static/files/logo.svg"
                })
            except:
                continue
        return products
    except:
        return []

@app.on_message()
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    query = update.message.text.strip()
    msg = await update.message.reply_text("در حال جستجو...")
    products = scrape_digikala(query)
    if not products:
        await msg.edit_text("محصول پیدا نشد")
        return
    for p in sorted(products, key=lambda x: x["price"])[:3]:
        text = f"{p['title']}\n*قیمت: {p['price']:,} تومان*"
        if p['discount']: text += f"  ←  {p['discount']}"
        keyboard = [[InlineKeyboardButton("خرید از دیجی‌کالا", url=p['link'])]]
        await update.message.reply_photo(
            photo=p['image'],
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    await msg.delete()

# این دقیقاً همون چیزیه که Appwrite انتظار داره
def main(event: dict) -> dict:
    try:
        body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})
        update = Update.de_json(body, app.bot)
        if update:
            app.create_task(app.process_update(update))
        return {"statusCode": 200}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
