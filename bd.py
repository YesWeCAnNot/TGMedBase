from datetime import datetime
import aiosqlite

from settings import TABLE_NAME


class UserDataManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.__TABLE_NAME = TABLE_NAME

    async def save_user_data(
            self,
            user_id: int,
            value: int,
            timestamp: str
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            table_name = f'"{user_id}"'
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            await db.execute(f"""
                INSERT INTO {table_name} (value, timestamp)
                VALUES (?, ?)
            """, (value, timestamp))
            await db.commit()

    async def get_sum_for_all_users(
            self,
            start_date: str,
            end_date: str,
            start_time="00:00:00",
            end_time="23:59:59"
    ) -> dict:
        results = {}
        start_date_obj = datetime.strptime(start_date, "%d.%m.%Y")
        end_date_obj = datetime.strptime(end_date, "%d.%m.%Y")

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()

            for (table_name,) in tables:
                if table_name == "sqlite_sequence":
                    continue
                table_name_str = f"'{table_name}'"
                cursor = await db.execute(f"""
                    SELECT SUM(value) FROM {table_name_str}
                    WHERE timestamp BETWEEN ? AND ?
                """, (start_date_obj.strftime("%Y-%m-%d") + f" {start_time}",
                      end_date_obj.strftime("%Y-%m-%d") + f" {end_time}"))
                result = await cursor.fetchone()
                results[table_name.strip('"')] = result[0] if result[0] else 0

        return results

    async def user_report(
            self,
            table_name: str,
            date: list
    ) -> str:
        results_user = {}
        async with aiosqlite.connect(self.db_path) as db:
            cursor_user = await db.execute(f"""
                    SELECT value, timestamp
                    FROM {table_name}
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC;
                """, (f"{date[0]} 00:00:00", f"{date[1]} 23:59:59"))
            response_user = await cursor_user.fetchall()
            for row in response_user:
                value, timestamp = row
                results_user[timestamp] = str(value)

            result_str_user = "\n".join([f"'{timestamp}': '{value}'" for timestamp, value in results_user.items()])
            return result_str_user

    async def admin_report(
            self,
            date: list
    ) -> str:
        response_result_admin = ''
        async with aiosqlite.connect(self.db_path) as db:
            for ID, NAME in self.__TABLE_NAME.items():
                table_name_str = f"'{ID}'"
                cursor_admin = await db.execute(f"""
                        SELECT value, timestamp
                        FROM {table_name_str}
                        WHERE timestamp BETWEEN ? AND ?
                        ORDER BY timestamp ASC;
                    """, (f"{date[0]} 00:00:00", f"{date[1]} 23:59:59"))
                response_admin = await cursor_admin.fetchall()

                results_admin = [f"'{timestamp}': '{value}'" for value, timestamp in response_admin]
                result_str_admin = "\n".join(results_admin)

                response_result_admin += f"\n{NAME}:\n{result_str_admin}\n"

        return response_result_admin
