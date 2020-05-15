import g_sheets.g_sheets as g_sheets
import sqlite3
PATH_TO_DB = r"C:\Users\jamie\Documents\Programming Projects\ecommProgramProject\tc_tools\resources\tire_tools_db.db"


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
                    order_quantity text,
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
                        order_quantity text,
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
    cur.execute('''CREATE TABLE tsa1 (db_id integer PRIMARY KEY, cc_item_number integer, trans_date text, quantity integer, amount text, invoice_number text)''')
    cur.execute('''CREATE TABLE nssdr (db_id integer PRIMARY KEY, cc_item_number integer, trans_date text, quantity integer, amount text, invoice_number text)''')
    conn.commit()
    conn.close()
    print('DB INITIALIZED, ADDING ITEM NUMBERS')
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


if __name__ == '__main__':
    print('Launched')
    initialize_db()
    print('Ending')
