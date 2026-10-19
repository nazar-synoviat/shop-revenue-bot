"""Telegram handlers: type an amount to record a sale, buttons for reports."""

from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, KeyboardButton, Message, ReplyKeyboardMarkup

from .db import SalesDB
from .report import build_excel, day_summary, money, parse_sale, week_summary

BTN_TODAY = "📊 Сьогодні"
BTN_WEEK = "📅 Тиждень"
BTN_EXCEL = "📥 Excel"
BTN_UNDO = "↩️ Скасувати останнє"

KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_WEEK)],
        [KeyboardButton(text=BTN_EXCEL), KeyboardButton(text=BTN_UNDO)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Сума продажу, напр. 350 або 1200 кава",
)

HELP = (
    "Я рахую виручку магазину.\n\n"
    "• Надішліть суму продажу: <code>350</code>\n"
    "• Можна з коментарем: <code>1200 кава + десерт</code>\n"
    "• Кнопки внизу: звіт за сьогодні, за тиждень, вивантаження в Excel."
)


def make_router(db: SalesDB) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message):
        await message.answer(f"Вітаю, {message.from_user.first_name}! 👋\n\n{HELP}", reply_markup=KEYBOARD)

    @router.message(Command("help"))
    async def help_(message: Message):
        await message.answer(HELP, reply_markup=KEYBOARD)

    @router.message(F.text == BTN_TODAY)
    @router.message(Command("today"))
    async def today(message: Message):
        day = db.now().date()
        sales = db.between(message.chat.id, day, day)
        await message.answer(f"<b>Сьогодні, {day:%d.%m}</b>\n{day_summary(sales)}")

    @router.message(F.text == BTN_WEEK)
    @router.message(Command("week"))
    async def week(message: Message):
        end = db.now().date()
        days = [end - timedelta(days=i) for i in range(6, -1, -1)]
        sales = db.between(message.chat.id, days[0], end)
        await message.answer(f"<b>Останні 7 днів</b>\n{week_summary(sales, days)}")

    @router.message(F.text == BTN_EXCEL)
    @router.message(Command("excel"))
    async def excel(message: Message):
        sales = db.all(message.chat.id)
        if not sales:
            await message.answer("Ще немає продажів для звіту.")
            return
        name = f"vyruchka_{db.now():%Y-%m-%d}.xlsx"
        await message.answer_document(
            BufferedInputFile(build_excel(sales), filename=name),
            caption=f"Усі продажі: {len(sales)} шт., {money(sum(s.amount for s in sales))}",
        )

    @router.message(F.text == BTN_UNDO)
    @router.message(Command("undo"))
    async def undo(message: Message):
        sale = db.undo_last(message.chat.id)
        if sale is None:
            await message.answer("Немає що скасовувати.")
        else:
            await message.answer(f"↩️ Видалено: {money(sale.amount)} ({sale.created_at:%d.%m %H:%M})")

    @router.message(F.text)
    async def record(message: Message):
        parsed = parse_sale(message.text)
        if parsed is None:
            await message.answer("Не зрозумів суму 🤔 Надішліть число, напр. <code>350</code>")
            return
        amount, note = parsed
        db.add(message.chat.id, amount, note)
        day = db.now().date()
        total = sum(s.amount for s in db.between(message.chat.id, day, day))
        note_part = f" — {note}" if note else ""
        await message.answer(f"✅ {money(amount)}{note_part}\nЗа сьогодні: <b>{money(total)}</b>")

    return router
