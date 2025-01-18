import sqlite3
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        print('tables created or exist...')

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = self.row_to_dict
        self.cursor = self.conn.cursor()
        # Enable foreign key support
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS RssFeed(
            server_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            channel_name String NOT NULL,
            channel_id INTEGER NOT NULL,
            enabled BOOLEAN DEFAULT TRUE NOT NULL,
            PRIMARY KEY (server_id, url)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS RssHistory(
            server_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (server_id, url) REFERENCES RssFeed(server_id, url) ON DELETE CASCADE,
            PRIMARY KEY (server_id, url, title)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS MainChannel(
            server_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            PRIMARY KEY (server_id),
            UNIQUE(server_id)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS AcceptedRole(
            server_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (server_id),
            UNIQUE(server_id)
        )
        ''')
        self.conn.commit()

    def row_to_dict(self, cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
        data = {}
        for idx, col in enumerate(cursor.description):
            data[col[0]] = row[idx]
        return data

    def insert(self, table: str, data: Dict[str, Any]):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        # print(query)
        self.cursor.execute(query, tuple(data.values()))
        self.conn.commit()

    def update(self, table: str, data: Dict[str, Any], condition: str):
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        # print(query)
        self.cursor.execute(query, tuple(data.values()))
        self.conn.commit()

    def delete(self, table: str, condition: str):
        query = f"DELETE FROM {table} WHERE {condition}"
        # print(query)
        self.cursor.execute(query)
        self.conn.commit()

    def select(self,
               tables: List[str],
               columns: List[str] = None,
               join_conditions: List[str] = None,
               where_condition: str = None,
               order_by: List[str] = None,
               group_by: List[str] = None,
               limit: int = None) -> List[Tuple]:
        columns_str = '*' if columns is None else ', '.join(columns)
        query = f"SELECT {columns_str} FROM {tables[0]}"

        # Handle JOINs
        if join_conditions and len(tables) > 1:
            for i, join_condition in enumerate(join_conditions):
                query += f" JOIN {tables[i + 1]} ON {join_condition}"

        # Handle WHERE clause
        if where_condition:
            query += f" WHERE {where_condition}"

        # Handle GROUP BY clause
        if group_by:
            query += f" GROUP BY {', '.join(group_by)}"

        # Handle ORDER BY clause
        if order_by:
            query += f" ORDER BY {', '.join(order_by)}"

        # Handle LIMIT clause
        if limit:
            query += f" LIMIT {limit}"

        # print(query)
        self.cursor.execute(query)
        return self.cursor.fetchall()

    # ADD HANDLERS
    def add_rss_feed(self, server_id: int, name: str, url: str, channel_name: str, channel_id: int, enabled: bool = True):
        data = {
            'server_id': server_id,
            'name': name,
            'url': url,
            'channel_name': channel_name,
            'channel_id': channel_id,
            'enabled': enabled
        }
        self.insert('RssFeed', data)

    def add_rss_history(self, server_id: int, url: str, title: str, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
        data = {
            'server_id': server_id,
            'url': url,
            'title': title,
            'timestamp': timestamp.isoformat()
        }
        self.insert('RssHistory', data)

    def add_main_channel(self, server_id: int, channel_id: int):
        data = {
            'server_id': server_id,
            'channel_id': channel_id
        }
        self.insert('MainChannel', data)

    def add_accepted_role(self, server_id: int, role_id: int):
        data = {
            'server_id': server_id,
            'role_id': role_id
        }
        self.insert('AcceptedRole', data)

    # UPDATE HANDLERS
    def update_rss_feed(self, server_id: int, url: str, data: Dict[str, Any]):
        condition = f"server_id = {server_id} AND url = '{url}'"
        self.update('RssFeed', data, condition)

    def update_rss_history(self, server_id: int, url: str, title: str, data: Dict[str, Any]):
        condition = f"server_id = {server_id} AND url = '{url}' AND title = '{title}'"
        self.update('RssHistory', data, condition)

    def update_main_channel(self, server_id: int, data: Dict[str, Any]):
        condition = f"server_id = {server_id}"
        self.update('MainChannel', data, condition)

    def update_accepted_role(self, server_id: int, data: Dict[str, Any]):
        condition = f"server_id = {server_id}"
        self.update('AcceptedRole', data, condition)

    # DELETE HANDLERS
    def delete_rss_feed(self, server_id: int, url: str):
        condition = f"server_id = {server_id} AND url = '{url}'"
        self.delete('RssFeed', condition)

    def delete_rss_history(self, server_id: int, url: str, title: str):
        condition = f"server_id = {server_id} AND url = '{url}' AND title = '{title}'"
        self.delete('RssHistory', condition)

    def scheduled_delete_rss_history(self):
        # delete history records older than 1 month
        condition = f'timestamp < datetime(\'now\', \'-1 month\')'
        self.delete('RssHistory', condition)

    def delete_main_channel(self, server_id: int):
        condition = f"server = {server_id}"
        self.delete('MainChannel', condition)

    def delete_accepted_role(self, server_id: int):
        condition = f"server_id = {server_id}"
        self.delete('AcceptedRole', condition)

    # GET HANDLERS
    def get_rss_feeds(self, server_id: int = None) -> List[Tuple]:
        where_condition = f"RssFeed.server_id = {server_id}" if server_id else None
        return self.select(['RssFeed'], where_condition=where_condition)

    def get_rss_history(self, server_id: int, url: str) -> List[Tuple]:
        where_condition = f"RssHistory.server_id = '{server_id}' AND RssHistory.url = '{url}'"
        return self.select(['RssHistory'], where_condition=where_condition)

    def get_main_channel(self, server_id: int) -> List[Tuple]:
        where_condition = f"MainChannel.server_id = {server_id}"
        return self.select(['MainChannel'], where_condition=where_condition)

    def get_accepted_role(self, server_id: int) -> List[Tuple]:
        where_condition = f"AcceptedRole.server_id = {server_id}"
        return self.select(['AcceptedRole'], where_condition=where_condition)

    def get_rss_feeds_with_history(self, server_id: Optional[int] = None, limit: Optional[int] = None) -> List[Tuple]:
        tables = ['RssFeed', 'RssHistory']
        columns = [
            'RssFeed.server_id', 'RssFeed.name', 'RssFeed.url', 'RssFeed.channel_name', 'RssFeed.channel_id', 'RssFeed.enabled',
            'RssHistory.title', 'RssHistory.timestamp'
        ]
        join_conditions = ['RssFeed.server_id = RssHistory.server_id AND RssFeed.url = RssHistory.url']
        where_condition = f"RssFeed.server_id = {server_id}" if server_id else None
        order_by = ['RssHistory.timestamp DESC']

        return self.select(tables,
                           columns=columns,
                           join_conditions=join_conditions,
                           where_condition=where_condition,
                           order_by=order_by,
                           limit=limit)
