import os
from typing import Any

from pymongo import MongoClient

db_url = os.getenv("MONGO_DB")
client: MongoClient
if db_url:
    client = MongoClient(db_url)
else:
    client = MongoClient('localhost', 27017)

db = client['grid-trade']
orders_list_backup = db['orders_list_backup']

class OrderListBackup():

    '''
    Create orders_list_backup using Mongo DB. Backup is used in case of server restert.
    When server will get back to work it will fetch backup and continue to work.
    '''

    def insert_item(self, order: dict[str,Any]) -> None:
        # Insert single instance of Order to backup list
        orders_list_backup.insert_one(order)

    def delete_item(self, symbol: str) -> None:
        # Remove single instance of Order from backup list
        orders_list_backup.find_one_and_delete({ 'symbol': symbol })

    def get_orders_list_backup(self):
        # Return all Order instances from backup list
        return orders_list_backup.find({})
