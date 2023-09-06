from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
from bs4 import BeautifulSoup

TOKEN = "6671093894:AAGksrgUpFWMUkYhPEbofhW3nhUlYOfRWsQ"
TARGET_CUR = ["USD", "EUR", "CHF", "JPY", "GBP"]

currency_rates = {}
user_states = {}

SELECTING_ACTION, SELECTING_CURRENCY, SELECTING_AMOUNT = range(3)

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id not in user_states or user_states[user_id] == SELECTING_ACTION:
        if not currency_rates:  
            load_currency_rates()
        actcurr = KeyboardButton('Актуальний курс')
        exchange = KeyboardButton('Конвертація валют')
    
        keyboard = ReplyKeyboardMarkup([[actcurr, exchange]], resize_keyboard=True)
    
        update.message.reply_text("Оберіть дію, будь ласка", reply_markup=keyboard)
    
        user_states[user_id] = SELECTING_ACTION

def load_currency_rates():
    url = 'https://bank.gov.ua/ua/markets/exchangerates'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            exchange_rates = {}
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 5:
                    numeric_code, alphabetic_code, units, value_name, exchange_rate = [cell.text.strip() for cell in cells]
                    if alphabetic_code in TARGET_CUR:
                        exchange_rate = float(exchange_rate.replace(',', '.'))
                        exchange_rates[alphabetic_code] = exchange_rate

            currency_rates.update(exchange_rates)

def actual_currency(update: Update, context: CallbackContext) -> None:
    if not currency_rates:
        update.message.reply_text("Йде завантаження актуальної інформації...")
        load_currency_rates()
    
    response_text = "Актуальний курс:\n"
    for currency, rate in currency_rates.items():
        if currency == "JPY":
            rate = rate / 10
        response_text += f'{currency}: {rate} UAH\n'
    
    update.message.reply_text(response_text.strip())

def exchange(update: Update, context: CallbackContext) -> None:
    user_states[update.message.chat_id] = SELECTING_CURRENCY

    currencyboard = [["USD", "EUR", "JPY", "GBP", "CHF"]]
    keyboard2 = ReplyKeyboardMarkup(currencyboard, resize_keyboard=True)

    update.message.reply_text(f"Оберіть валюту", reply_markup=keyboard2)

def handle_text(update: Update, context: CallbackContext) -> None:
    user_state = user_states.get(update.message.chat_id, None)

    if user_state == SELECTING_CURRENCY:
        selected_currency = update.message.text

        if selected_currency in TARGET_CUR:
            rate = currency_rates[selected_currency]
            context.user_data['selected_currency'] = selected_currency
            user_states[update.message.chat_id] = SELECTING_AMOUNT
            update.message.reply_text(f'Введіть кількість {selected_currency} для конвертації:')
        else:
            update.message.reply_text('Обрана валюта не знайдена')
            start(update, context)  

    elif user_state == SELECTING_AMOUNT:
        try:
            amount = float(update.message.text)
            selected_currency = context.user_data.get('selected_currency')
            if selected_currency in TARGET_CUR:
                rate = currency_rates[selected_currency]
                converted_amount = amount * rate
                if selected_currency == "JPY":
                    rate = currency_rates[selected_currency]
                    converted_amount = (amount * rate)/10
                    update.message.reply_text(f'{amount} {selected_currency} дорівнює {converted_amount} UAH')
                    start(update, context)  

                else:
                    update.message.reply_text(f'{amount} {selected_currency} дорівнює {converted_amount} UAH')
                    user_states[update.message.chat_id] = SELECTING_ACTION
                    start(update, context)  
            else:
                update.message.reply_text('Обрана валюта не знайдена.')
        except ValueError:
            update.message.reply_text('Будь ласка, введіть числове значення для кількості.')
            

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^Актуальний курс$'), actual_currency))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^Конвертація валют$'), exchange))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
 
