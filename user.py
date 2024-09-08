import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command
from aiogram import F

from settings import ID_USER, ID_ADMINISTRATOR, API_TOKEN
from bd import UserDataManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a'
)

logger = logging.getLogger(__name__)


class BotMedBase:
    """
    """

    def __init__(self, api_token: str, db_path: str):
        self.__bot = Bot(api_token)
        self.__db = Dispatcher()
        self.__router = Router()

        self.__router.message(F.text & ~F.text.startswith('/'))(self.message_handler)
        self.__router.message(Command(commands=['report']))(self.report)
        # self.__router.message(Command(commands=['help']))(self.help_command)

        self.__db.include_router(self.__router)
        self.user_data_manager = UserDataManager(db_path)

        logger.info("Bot initialized with token and database path.")

    @staticmethod
    async def __is_user(user_id: int) -> bool:
        return user_id in ID_USER

    @staticmethod
    async def __is_admin(user_id: int) -> bool:
        return user_id in ID_ADMINISTRATOR

    @staticmethod
    async def __is_number(text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    @staticmethod
    async def __get_current_month_date_range() -> tuple:
        date = datetime.now()

        date_of_the_first_of_the_month = f"{date.year}-{date.strftime('%m')}-01"
        date_now = date.strftime("%Y-%m-%d")

        return date_of_the_first_of_the_month, date_now

    # router.message(F.text & ~F.text.startswith('/'))
    async def message_handler(self, message: Message) -> None:
        user_id = message.from_user.id
        logger.info(f"Handling message from user {user_id}: {message.text}")

        if await self.__is_user(user_id=user_id):
            if await self.__is_number(text=message.text):
                await self.user_data_manager.save_user_data(
                    user_id=user_id,
                    value=int(message.text),
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                logger.info(f"Data saved for user {user_id}")
                await message.answer(f"Вы ввели число: {message.text}. Оно сохранено")
            else:
                logger.warning(f"User {user_id} inputted an invalid number.")
                await message.answer(
                    f"Пожалуйста, введите корректное число.\nБез специальных знаков и букв\nПример: 12"
                )
        elif await self.__is_admin(user_id=user_id):
            try:
                start_date, end_date = message.text.split("-")  # String format 01.01.2024-31.01.2024
                results = await self.user_data_manager.get_sum_for_all_users(start_date=start_date, end_date=end_date)
                response = "\n".join([f"{user_name} сумма за отчетный период: {sum_value}"
                                      for user_name, sum_value in results.items()])
                logger.info(f"Admin {user_id} requested report from {start_date} to {end_date}")
                await message.answer(response)
            except Exception as ex:
                logger.error(f"Error processing admin report: {ex}")
                await message.answer(f"Error {ex}")
        else:
            logger.info(f"User {user_id} is neither a user nor an admin.")

    async def report(self, message: Message):
        user_id = message.from_user.id
        user_id_str = f"'{user_id}'"
        date = [*await self.__get_current_month_date_range()]
        try:
            if await self.__is_user(user_id=user_id):
                response_user_results = await self.user_data_manager.user_report(table_name=user_id_str, date=date)
                logger.info(f"Report generated for user {user_id}")
                await message.answer(f"{response_user_results}")
            elif await self.__is_admin(user_id=user_id):
                response_admin_results = await self.user_data_manager.admin_report(date=date)
                logger.info(f"Admin {user_id} requested a report.")
                await message.answer(f'{response_admin_results}')
            else:
                logger.warning(f"User {user_id} attempted to use /report command without permission.")
                await message.answer("Sorry! /report command is not available!")
        except Exception as ex:
            logger.error(f"Error in report generation: {ex}")

    async def run(self):
        await self.__bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting polling...")
        await self.__db.start_polling(self.__bot)


async def main():
    api_token = API_TOKEN
    db_path = "user_data.db"
    my_bot = BotMedBase(api_token=api_token, db_path=db_path)
    await my_bot.run()


if __name__ == '__main__':
    asyncio.run(main())
