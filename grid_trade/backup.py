import json
from typing import Union


class Backup():
    # Simple class for write and read backup data to or from a file.

    def write_backup_data(self, orders_list: dict[str, list[dict]]) -> None:
        with open('backup.json', 'w', encoding ='utf8') as backup_file:
            json.dump(orders_list, backup_file, ensure_ascii = True)
            print('Backup updated')
    

    def read_backup_data(self) -> Union[dict[str,list[dict]], None]:
        with open('backup.json', 'r', encoding ='utf8') as backup_file:
            try:
                return json.load(backup_file)
            except:
                print('Backup is empty')