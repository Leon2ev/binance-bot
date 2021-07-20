import os

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
    def insert_item(self, order) -> None:
        orders_list_backup.insert_one(order)

    def delete_item(self, symbol) -> None:
        orders_list_backup.find_one_and_delete({ 'symbol': symbol })

    def get_orders_list_backup(self):
        return orders_list_backup.find({})
