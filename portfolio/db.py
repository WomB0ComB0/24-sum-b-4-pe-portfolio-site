import os
import sqlite3
import json
import logging
from flask import g
from typing import Dict, List, Any, Optional, Tuple
from peewee import MySQLDatabase
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

logger = logging.getLogger(__name__)

mydb = MySQLDatabase(
    os.getenv(
        "TEST_MYSQL_DATABASE" if os.getenv("TEST") == "True" else "MYSQL_DATABASE"
    ),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=3306,
)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        try:
            if "conn" not in g:
                g.conn = sqlite3.connect(self.db_path)
                g.cursor = g.conn.cursor()
            return g.conn, g.cursor
        except sqlite3.Error as e:
            logger.error("Error connecting to database: %s", e)
            raise

    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None
        try:
            conn, cursor = self.get_connection()

            columns_dict = self.python_to_sql(columns)
            columns_dict["id"] = "INTEGER PRIMARY KEY AUTOINCREMENT"
            columns_str = ", ".join(
                [
                    f"{column_name} {column_type}"
                    for column_name, column_type in columns_dict.items()
                ]
            )
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
            cursor.execute(query)
            conn.commit()
        except sqlite3.Error as e:
            logger.error("Error creating table %s: %s", table_name, e)
            if conn:
                conn.rollback()
            raise

    def insert_data(self, table_name: str, data: Dict[str, Any]) -> None:
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None
        try:
            conn, cursor = self.get_connection()
            logger.info("Inserting data into table: %s", table_name)
            logger.debug("Data to be inserted: %s", data)

            if isinstance(data, str):
                logger.warning(
                    "Received string data instead of dictionary. Attempting to parse as JSON."
                )
                data = json.loads(data)

            if not isinstance(data, dict):
                raise ValueError(
                    f"Invalid data type. Expected dictionary, got {type(data)}"
                )

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                raise ValueError(f"Table {table_name} does not exist")

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]

            filtered_data = {k: v for k, v in data.items() if k in columns}
            if not filtered_data:
                raise ValueError(f"No valid columns found for table {table_name}")

            columns_str = ", ".join(filtered_data.keys())
            placeholders = ", ".join(["?" for _ in filtered_data])
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            cursor.execute(query, tuple(filtered_data.values()))
            conn.commit()
            logger.info("Successfully inserted data into %s", table_name)
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error("Error inserting data into %s: %s", table_name, e)
            if conn:
                conn.rollback()
            raise

    def update_data(
        self,
        table_name: str,
        where_condition: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        index: int = 1,
    ) -> None:
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None
        if where_condition is None:
            raise ValueError("where_condition is required")
        if data is None:
            raise ValueError("data is required")
        try:
            conn, cursor = self.get_connection()

            if index is not None:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                if 0 <= (index - 1) < len(rows):
                    row_id = rows[index - 1][-1]
                    where_condition = {"id": row_id}
                else:
                    logger.error(
                        "Index %s out of range for table %s", index, table_name
                    )
                    raise ValueError(
                        f"Index {index} out of range for table {table_name}. The length of the table is {len(rows)}, the index is. Rows is {rows[0][-1]}"
                    )

            if where_condition:
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                where_clause = " AND ".join(
                    [f"{k} = ?" for k in where_condition.keys()]
                )
                query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                logger.error("Query: %s", query)
                params = tuple(data.values()) + tuple(where_condition.values())
            else:
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                query = f"UPDATE {table_name} SET {set_clause}"
                params = tuple(data.values())

            cursor.execute(query, params)
            conn.commit()
        except sqlite3.Error as e:
            logger.error("Error updating data in %s: %s", table_name, e)
            if conn:
                conn.rollback()
            raise

    def read_data(
        self,
        table_name: str,
        columns: List[str],
        where_condition: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None
        if where_condition is None:
            raise ValueError("where_condition is required")
        try:
            _, cursor = self.get_connection()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                raise ValueError(f"Table {table_name} does not exist")

            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [col[1] for col in cursor.fetchall()]
            logger.debug("Existing columns in %s: %s", table_name, existing_columns)
            valid_columns = [
                col for col in columns if col in existing_columns or col == "*"
            ]

            if not valid_columns:
                raise ValueError(f"No valid columns found for {table_name}")

            columns_str = ", ".join(valid_columns) if "*" not in valid_columns else "*"
            query = f"SELECT {columns_str} FROM {table_name}"
            if "id" in existing_columns:
                query = f"SELECT id, {columns_str} FROM {table_name}"

            if where_condition:
                where_clause = " AND ".join(
                    [f"{column_name} = ?" for column_name in where_condition.keys()]
                )
                query += f" WHERE {where_clause}"
                cursor.execute(query, tuple(where_condition.values()))
            else:
                cursor.execute(query)

            column_names = [description[0] for description in cursor.description]
            return [dict(zip(column_names, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error("Error reading data from %s: %s", table_name, e)
            if conn:
                conn.rollback()
            raise

    def delete_data(self, table_name: str, where_condition: Dict[str, str]) -> None:
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None
        try:
            conn, cursor = self.get_connection()
            where_clause = " AND ".join(
                [f"{column_name} = ?" for column_name, value in where_condition.items()]
            )
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            cursor.execute(query, tuple(where_condition.values()))
            conn.commit()
        except sqlite3.Error as e:
            logger.error("Error deleting data from %s: %s", table_name, e)
            if conn:
                conn.rollback()
            raise

    def close_connection(self) -> None:
        try:
            conn: Optional[sqlite3.Connection] = getattr(g, "conn", None)
            if conn is not None:
                conn.close()
        except sqlite3.Error as e:
            logger.error("Error closing database connection: %s", e)
            raise

    @staticmethod
    def python_to_sql(columns: Dict[str, Any]) -> Dict[str, str]:
        try:
            python_to_sql_types = {
                "str": "TEXT",
                "int": "INTEGER",
                "float": "REAL",
                "bool": "INTEGER",
                "datetime": "DATETIME",
                "date": "DATE",
                "list": "TEXT",
                "dict": "TEXT",
            }

            reserved_keywords = ["limit", "order", "group"]

            result = {}
            for column_name, column_value in columns.items():
                if column_name.lower() in reserved_keywords:
                    column_name = f'"{column_name}"'
                if isinstance(column_value, dict):
                    result[column_name] = "TEXT"
                else:
                    type_name = type(column_value).__name__
                    if type_name in python_to_sql_types:
                        result[column_name] = python_to_sql_types[type_name]
                    else:
                        result[column_name] = "TEXT"
                        logger.warning(
                            "Unrecognized type %s for column %s. Using TEXT.",
                            type_name,
                            column_name,
                        )

            return result
        except Exception as e:
            logger.error("Error in python_to_sql conversion: %s", e)
            raise

    def convert_data_type(self, from_type: str, to_type: str) -> str:
        python_to_sql_types = {
            "str": "TEXT",
            "int": "INTEGER",
            "float": "REAL",
            "bool": "INTEGER",
            "datetime": "DATETIME",
            "date": "DATE",
            "list": "TEXT",
            "dict": "TEXT",
        }

        sql_to_python_types = {v: k for k, v in python_to_sql_types.items()}

        if from_type in python_to_sql_types and to_type.upper() in sql_to_python_types:
            return to_type.upper()
        elif (
            from_type.upper() in sql_to_python_types and to_type in python_to_sql_types
        ):
            return python_to_sql_types[to_type]
        else:
            raise ValueError(f"Invalid conversion: from {from_type} to {to_type}")
