import os
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

def clean_price(text):
    if not text: return None
    return int(re.sub(r"[^\d]", "", text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))))

def scrape_digikala(query):
    scraper = cloudscraper.create_scraper()
    url = f"https://www.digikala.com/search/?q={query.replace(' ', '%20')}"
    html = scraper.get(url).text
    soup = BeautifulSoup(html, "lxml")

    products = []
    for item in soup.select('a[data-testid="product-card"]')[:20]:
        try:
            title = item.select_one('h3').get_text(strip=True)
            price_text = item.select_one('[data-testid="price-final"]')
            price = clean_price(price_text.get_text()) if price_text else None
            if not price: continue

            discount = item.select_one('[data-testid="price-discount-percent"]')
            discount = discount.get_text(strip=True) if discount else None

            link = "https://www.digikala.com" + item['href'].split('?')[0]
            img = item.select_one('img').get('src', '')

            products.append({
                "title": title[:100],
                "price": price,
                "discount": discount,
                "link": link,
                "image": img or "https://www.digikala.com/static/files/logo.svg"
            })
        except:
            continue
    return products

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! اسم محصول رو بفرست تا بهترین‌ها رو برات پیدا کنم")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    msg = await update.message.reply_text(f"در حال جستجو برای «{query}»...")
    
    try:
        products = scrape_digikala(query)
        if not products:
            await msg.edit_text("محصول پیدا نشد")
            return

        cheapest = sorted(products, key=lambda x: x["price"])[:3]
        for p in cheapest:
            text = f"{p['title']}\n*قیمت: {p['price']:,} تومان*"
            if p['discount']: text += f"  ←  {p['discount']}"
            keyboard = [[InlineKeyboardButton("خرید از دیجی‌کالا", url=p['link'])]]
            await update.message.reply_photo(p['image'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        await msg.delete()
    except:
        await msg.edit_text("خطایی پیش آمد، دوباره امتحان کن")

def main(event):
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main({}))
