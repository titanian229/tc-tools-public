"""Works with the database"""
import sqlite3
from pathlib import Path
import g_sheets.g_sheets as g_sheets

DIR_NAME = Path(__file__).parent
# PATH_TO_DB = '/'.join((str(DIR_NAME), 'resources', 'tire_tools_db.db'))
PATH_TO_DB = '/'.join((str(DIR_NAME), 'tire_tools_db.db'))
DUPLICATE_MANUFAC_LIST = ['11663', '1173', '11782', '13210', '13737', '1443', '15692', '158', '16168', '1928500',
                          '19647',
                          '2009', '20236', '220', '22114', '2313600', '2359', '2359000', '25373', '2722300', '2863600',
                          '3233', '3241', '33791', '3642', '3772', '3794', '3863', '40', '4262', '42696', '4301', '434',
                          '4493', '4743', '4801', '4853', '5970', '6189', '65187', '65289', '69369', '79824', '87971',
                          '893', '9453', '958', '9623']


class PersistenceManager:
    """Manages persistence, saving to db and retrieving from db"""

    def __init__(self, table_name, cls):
        """Creates a persistence manager, init sets the table name and class being worked with"""

        self.table_name = table_name
        self.cls = cls
        self.objects = []

    def insert(self, objects):
        """Given a list of objects, inserts it into the db using the object's insert_db method"""
        conn = sqlite3.connect(PATH_TO_DB)
        cur = conn.cursor()

        for an_obj in objects:
            insert_columns, insert_vals = an_obj.insert_db()
            insert_command = f"INSERT INTO {self.table_name} {insert_columns} VALUES {insert_vals}"
            print(insert_command)
            cur.execute(insert_command)

        conn.commit()
        conn.close()

    def insert_deprecated(self, objects):
        """Given a list of objects, inserts it into the db using it's own insert command"""
        conn = sqlite3.connect(PATH_TO_DB)
        cur = conn.cursor()

        for an_obj in objects:
            column_names = []
            column_values = []

            for k, v in an_obj.__dict__.items():
                if str(k)[0] != '_' and str(k) != 'db_id' and v is not None:  # It is not a hidden value
                    column_names.append(str(k))
                    column_values.append("'" + str(v) + "'")

            insert_columns = ', '.join(column_names)
            insert_vals = ', '.join(column_values)

            # insert_columns =  ', '.join([str(x) for x in an_obj.__dict__.keys() if str(x)[0] != '_'])
            # insert_vals = ', '.join([str(x) for x in an_obj.__dict__.values() if str(x)[0] != '_'])

            insert_command = f"INSERT INTO {self.table_name} ({insert_columns}) VALUES ({insert_vals})"
            print(insert_command)
            cur.execute(insert_command)

        conn.commit()
        conn.close()

    def insert_objects(self):
        """Inserts the objects it's holding"""

        self.insert(self.objects)

    def objects_from_search(self, search_criteria, order_by=None):
        """Creates object of class using results from search, given search criteria
        Requires object have a 'create from db' class method
        If search is empty, returns entire db"""
        if search_criteria:
            search_string = f'''SELECT * FROM {self.table_name} WHERE {search_criteria}'''
        else:
            search_string = f'SELECT * FROM {self.table_name}'
        if order_by is not None:
            search_string = search_string + f' ORDER BY {order_by} DESC'
        print(search_string)
        conn = sqlite3.connect(PATH_TO_DB)
        cur = conn.cursor()
        cur.execute(search_string)
        rows = cur.fetchall()
        conn.close()

        returned_objects = []
        #  Given rows, create objects
        for a_row in rows:
            returned_objects.append(self.cls.create_from_db(a_row))

        return returned_objects

    def add_to_object_container(self, obj):
        """Adds to the internal object container"""
        self.objects.append(obj)

    def create_objects_from_factory(self, creation_factory, values_tuple):
        """Given a tuple of values, creates objects using method given and adds to container"""
        for a_row in values_tuple:
            self.objects.append(creation_factory(a_row))

class EcommPersistenceManager(PersistenceManager):
    """Persistence manager tailored for ecomm objects specifically"""

    def __init__(self, table_name, cls):
        super().__init__(table_name, cls)

    def insert_objects(self):
        super().insert_objects()

    def create_objects_from_factory(self, creation_factory, values_tuple):
        super().create_objects_from_factory(creation_factory, values_tuple)


def initialize_db():
    """Creates a new db"""
    '''order_number, cc_item_num, manufac_item_num, order_date,
       tire_data, labelled_state, order_quantity, order_status, db_id'''
    conn = sqlite3.connect(PATH_TO_DB)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS ecomm_orders 
                   (db_id integer PRIMARY KEY,
                    order_number text,
                    cc_item_num text,
                    manufac_item_num text,
                    order_date text,
                    tire_data text,
                    labelled_state text,
                    order_quantity integer,
                    order_status text)''')
    conn.commit()
    cur.execute('''CREATE TABLE IF NOT EXISTS new_ecomm_orders 
                       (db_id integer PRIMARY KEY,
                        order_number text,
                        cc_item_num text,
                        manufac_item_num text,
                        order_date text,
                        tire_data text,
                        labelled_state text,
                        order_quantity integer,
                        order_status text)''')
    conn.commit()
    cur.execute('''CREATE TABLE IF NOT EXISTS item_numbers
                   (row_id integer PRIMARY KEY,
                    cc_item_num text,
                    manufac_item_num text,
                    note text)''')
    conn.commit()
    cur.execute('''DROP TABLE IF EXISTS tsa1''')
    cur.execute('''DROP TABLE IF EXISTS nssdr''')
    conn.commit()
    cur.execute(
        '''CREATE TABLE tsa1 (db_id integer PRIMARY KEY, cc_item_num integer, trans_date text, quantity integer, amount text, invoice_number text)''')
    cur.execute(
        '''CREATE TABLE nssdr (db_id integer PRIMARY KEY, cc_item_num integer, trans_date text, quantity integer, amount text, invoice_number text)''')
    conn.commit()
    cur.execute('''CREATE TABLE IF NOT EXISTS ecomm_audit (db_id integer PRIMARY KEY, order_number text, state text)''')

    conn.close()


def drop_inv_tools_tables():
    """Drops the two tables used by inv tools NSSDR and TSA1 report"""

    conn = sqlite3.connect(PATH_TO_DB)
    cur = conn.cursor()
    cur.execute('''DROP TABLE IF EXISTS tsa1''')
    cur.execute('''DROP TABLE IF EXISTS nssdr''')
    conn.commit()
    cur.execute(
        '''CREATE TABLE tsa1 (db_id integer PRIMARY KEY, cc_item_num integer, trans_date text, quantity integer, amount text, invoice_number text)''')
    cur.execute(
        '''CREATE TABLE nssdr (db_id integer PRIMARY KEY, cc_item_num integer, trans_date text, quantity integer, amount text, invoice_number text)''')
    conn.commit()
    conn.close()


def push_item_number_table():
    """Pushes the item number database into the cloud"""
    #  Not yet implemented
    pass


def pull_item_number_table():
    """Pulls the item number database and updates the db file.  Wipes the db first."""
    gc = g_sheets.g_authenticate()
    item_number_spreadsheet = gc.open_by_key("1K3GCrU0vZeo0sb8b_ydTKoKx_SmQquaRvBe2Gx32eJI").sheet1

    item_number_spreadsheet_contents = item_number_spreadsheet.get_all_values()

    conn = sqlite3.connect(PATH_TO_DB)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS item_numbers")
    conn.commit()
    cur.execute('''CREATE TABLE IF NOT EXISTS item_numbers
                       (row_id integer PRIMARY KEY,
                        cc_item_num text,
                        manufac_item_num text,
                        note text)''')

    for a_row in item_number_spreadsheet_contents:
        insert_dict = {'cc_item_num': a_row[0], 'manufac_item_num': a_row[1], 'note': a_row[2]}
        cur.execute('''INSERT INTO item_numbers (cc_item_num, manufac_item_num, note) 
                       VALUES (:cc_item_num, :manufac_item_num, :note)''', insert_dict)

    conn.commit()
    conn.close()


def add_manufac_item_number_to_orders(orders):
    """Takes a list of order objects, adds a manufacturer item number to each if possible"""
    for an_order in orders:
        manufac_item_num = find_manufac_item_num(an_order.cc_item_num)
        if len(manufac_item_num) > 1:
            print(f'Multiple item numbers found for {an_order.cc_item_num}')
        else:
            an_order.manufac_item_num = manufac_item_num[0][0]


def find_manufac_item_num(cc_item_num):
    """Searches the db and finds a manufac item number to go with the cc item num"""

    found_rows = execute_in_db(f"SELECT manufac_item_num FROM item_numbers WHERE cc_item_num = {cc_item_num}")

    # 3 situations.  No result, multiple results, one result.
    if found_rows:
        return found_rows
    else:
        print(f'No result found for item number {cc_item_num}')
        return None


def find_cc_item_num(manufac_item_num):
    """Searches the db and finds a cc item num given a manufac item num"""
    found_rows = execute_in_db(f"SELECT cc_item_num FROM item_numbers WHERE manufac_item_num = {manufac_item_num}")

    # 3 situations.  No result, multiple results, one result.
    if found_rows:
        return found_rows
    else:
        print(f'No result found for item number {manufac_item_num}')
        return None


def execute_in_db(execute_string):
    """Executes string and returns tuple of rows"""
    conn = sqlite3.connect(PATH_TO_DB)
    cur = conn.cursor()
    cur.execute(execute_string)
    ret_tuple = cur.fetchall()
    conn.commit()
    conn.close()
    return ret_tuple


def check_item_number_db_for_duplicates():
    """Checks item number list for duplicate manufac item numbers, and returns a list of them"""
    conn = sqlite3.connect(PATH_TO_DB)
    cur = conn.cursor()
    cur.execute('SELECT manufac_item_num, COUNT(*) c FROM item_numbers GROUP BY manufac_item_num HAVING c > 1')
    duplicate_item_numbers = cur.fetchall()
    conn.close()
    return duplicate_item_numbers
