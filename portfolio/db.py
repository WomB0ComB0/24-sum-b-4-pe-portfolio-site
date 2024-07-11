from flask import g
import os
import sqlite3
from typing import Dict, List
from peewee import MySQLDatabase
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

mydb = MySQLDatabase(
    os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=3306,
)
class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        if "conn" not in g:
            g.conn = sqlite3.connect(self.db_path)
            g.cursor = g.conn.cursor()
        return g.conn, g.cursor

    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        conn, cursor = self.get_connection()
        columns_str = ", ".join(
            [
                f"{column_name} {column_type}"
                for column_name, column_type in self.python_to_sql(columns).items()
            ]
        )
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")
        conn.commit()

    def insert_data(self, table_name: str, data: Dict[str, str]) -> None:
        conn, cursor = self.get_connection()
        columns = ", ".join(data.keys())
        values = ", ".join([f"'{value}'" for value in data.values()])
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        conn.commit()

    def update_data(
        self, table_name: str, data: Dict[str, str], where_condition: Dict[str, str]
    ) -> None:
        conn, cursor = self.get_connection()
        set_clause = ", ".join(
            [f"{column_name} = '{value}'" for column_name, value in data.items()]
        )
        where_clause = " AND ".join(
            [
                f"{column_name} = '{value}'"
                for column_name, value in where_condition.items()
            ]
        )
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}")
        conn.commit()

    def read_data(
        self,
        table_name: str,
        columns: List[str],
        where_condition: Dict[str, str] = None,
    ) -> List[Dict[str, str]]:
        _, cursor = self.get_connection()
        columns_str = ", ".join(columns)
        query = f"SELECT {columns_str} FROM {table_name}"
        if where_condition:
            where_clause = " AND ".join(
                [
                    f"{column_name} = '{value}'"
                    for column_name, value in where_condition.items()
                ]
            )
            query += f" WHERE {where_clause}"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def delete_data(self, table_name: str, where_condition: Dict[str, str]) -> None:
        conn, cursor = self.get_connection()
        where_clause = " AND ".join(
            [
                f"{column_name} = '{value}'"
                for column_name, value in where_condition.items()
            ]
        )
        cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
        conn.commit()

    def close_connection(self) -> None:
        conn = getattr(g, "conn", None)
        if conn is not None:
            conn.close()

    @staticmethod
    def python_to_sql(data: Dict[str, str]) -> Dict[str, str]:
        python_to_sql_types: Dict[str, str] = {
            "str": "VARCHAR",
            "int": "INTEGER",
            "float": "FLOAT",
            "bool": "BOOLEAN",
            "bytes": "BLOB",
            "datetime": "DATETIME",
        }
        return {
            column_name: python_to_sql_types[type(column_type).__name__]
            for column_name, column_type in data.items()
        }
