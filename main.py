import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import executor


import os

admin_id = os.environ.get('394926357')


class Employee(StatesGroup):
    waiting_for_last_name = State()
    waiting_for_first_name = State()
    waiting_for_patronymic = State()
    waiting_for_birth_date = State()
    waiting_for_position = State()
    waiting_for_status = State()
    waiting_for_id = State()
    update_field = State()
    update_value = State()


conn = sqlite3.connect('employees.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  last_name TEXT,
                  first_name TEXT,
                  patronymic TEXT,
                  birth_date TEXT,
                  position TEXT,
                  status TEXT)""")
conn.commit()

bot = Bot(token='6072626475:AAFsEMqhI6-16gZhy45O-QEw0XOjSV4fT3s')
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(Command('add'))
async def add_employee_last_name(message: types.Message):
    await message.reply("Введите фамилию сотрудника:")
    await Employee.waiting_for_last_name.set()


@dp.message_handler(state=Employee.waiting_for_last_name)
async def add_employee_first_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['last_name'] = message.text
    await message.reply("Введите имя сотрудника:")
    await Employee.waiting_for_first_name.set()


@dp.message_handler(state=Employee.waiting_for_first_name)
async def add_employee_patronymic(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['first_name'] = message.text
    await message.reply("Введите отчество сотрудника:")
    await Employee.waiting_for_patronymic.set()


@dp.message_handler(state=Employee.waiting_for_patronymic)
async def add_employee_birth_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['patronymic'] = message.text
    await message.reply("Введите дату рождения сотрудника (в формате ДД.ММ.ГГГГ):")
    await Employee.waiting_for_birth_date.set()


@dp.message_handler(state=Employee.waiting_for_birth_date)
async def add_employee_position(message: types.Message, state: FSMContext):
    birth_date = message.text
    if not birth_date:
        await message.reply("Дата рождения введена неверно. Попробуйте еще раз.")
        await Employee.waiting_for_birth_date.set()
        return
    async with state.proxy() as data:
        data['birth_date'] = birth_date
    await message.reply("Введите должность сотрудника:")
    await Employee.waiting_for_position.set()


@dp.message_handler(state=Employee.waiting_for_position)
async def add_employee_status(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['position'] = message.text
    await message.reply("Введите статус сотрудника:")
    await Employee.waiting_for_status.set()


@dp.message_handler(state=Employee.waiting_for_status)
async def add_employee_confirm(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        cursor.execute("INSERT INTO employees (last_name, first_name, patronymic, birth_date, position, status) "
                       "VALUES (?, ?, ?, ?, ?, ?)",
        data['last_name'], data['first_name'], data['patronymic'], data['birth_date'], data['position'], data['status'])
        conn.commit()
        await message.reply(f"Сотрудник {data['last_name']} {data['first_name']} {data['patronymic']} "
                            f"добавлен в базу данных.")
    await state.finish()

    @dp.message_handler(Command('delete'))
    async def delete_employee(message: types.Message):
        await message.reply("Введите id сотрудника, которого нужно удалить:")
        await Employee.waiting_for_id.set()

    @dp.message_handler(state=Employee.waiting_for_id)
    async def delete_employee_confirm(message: types.Message, state: FSMContext):
        employee_id = message.text
        if not employee_id.isdigit():
            await message.reply("Некорректный id. Попробуйте еще раз.")
            await Employee.waiting_for_id.set()
            return
        cursor.execute("DELETE FROM employees WHERE id=?", (employee_id,))
        conn.commit()
        await message.reply(f"Сотрудник с id {employee_id} удален из базы данных.")
        await state.finish()

    @dp.message_handler(Command('view'))
    async def view_employees(message: types.Message):
        cursor.execute("SELECT * FROM employees")
        rows = cursor.fetchall()
        employees_text = ''
        for row in rows:
            employee_text = f"{row[0]}. {row[1]} {row[2]} {row[3]}, дата рождения: {row[4]}, должность: {row[5]}, статус: {row[6]}\n"
            employees_text += employee_text
        await message.reply(employees_text)

    @dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('update'))
    async def update_employee_field(callback_query: types.CallbackQuery):
        field = callback_query.data.split(':')[1]
        await bot.send_message(callback_query.from_user.id, f"Введите новое значение для поля '{field}':")
        await Employee.update_field.set()

    @dp.message_handler(state=Employee.update_field)
    async def update_employee_value(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['field'] = message.text
        await message.reply("Введите новое значение:")
        await Employee.update_value.set()

    @dp.message_handler(state=Employee.update_value)
    async def update_employee_confirm(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            cursor.execute(f"UPDATE employees SET {data['field']}=? WHERE id=?", (message.text, data['employee_id']))
            conn.commit()
            await message.reply(f"Данные сотрудника с id {data['employee_id']} обновлены.")
        await state.finish()

    @dp.message_handler(Command('update'))
    async def update_employee(message: types.Message):
        await message.reply("Введите id сотрудника, данные которого нужно изменить:")
        await Employee.waiting_for_id.set()

    @dp.message_handler(state=Employee.waiting_for_id)
    async def update_employee_field_select(message: types.Message, state: FSMContext):
        employee_id = message.text

        try:
            employee = Employee.get_by_id(employee_id)
            await state.update_data(id=employee_id)
        except Employee.DoesNotExist:
            await message.reply("Сотрудник не найден")
            await state.finish()
            return

        markup = types.InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(types.InlineKeyboardButton("Фамилия", callback_data="update:last_name"),
                   types.InlineKeyboardButton("Имя", callback_data="update:first_name"),
                   types.InlineKeyboardButton("Отчество", callback_data="update:patronymic"),
                   types.InlineKeyboardButton("Дата рождения", callback_data="update:birth_date"),
                   types.InlineKeyboardButton("Должность", callback_data="update:position"),
                   types.InlineKeyboardButton("Статус", callback_data="update:status"))
        await message.reply("Какое поле вы хотите изменить?", reply_markup=markup)
        await state.finish()
async def on_startup(dp):
    await bot.send_message(chat_id=admin_id, text="Бот запущен")


async def on_shutdown(dp):
    await bot.send_message(chat_id=admin_id, text="Бот остановлен")
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)

