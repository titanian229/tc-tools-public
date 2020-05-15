"""Ecomm functions, functionality related to tracking and labelling ecomm orders, as well as converting item numbers"""
import g_sheets.g_sheets as gs
import resources.db_work as db
import objects.inventory_objects as inv


def update_order_table_from_gspread():
    """Grabs the db, grabs the data out of the STA copy/paste google sheet, compares and updates the db"""

    #  Making the new_ecomm_orders table
    db.execute_in_db('''CREATE TABLE IF NOT EXISTS new_ecomm_orders 
                           (db_id integer PRIMARY KEY,
                            order_number text,
                            cc_item_num text,
                            manufac_item_num text,
                            order_date text,
                            tire_data text,
                            labelled_state text,
                            order_quantity integer,
                            order_status text)''')

    #  Grabs data from the STA google sheet, creating objects as I go
    gc = gs.g_authenticate()
    sta_input_sheet = gc.open_by_key("1x0t2veo2VKH9BJN0o10THwKxU94khs-c_6diAQa4Mu0").sheet1

    sta_input_contents = sta_input_sheet.get_all_values()

    orders_persistence = db.PersistenceManager('new_ecomm_orders', inv.Order)

    orders_persistence.create_objects_from_factory(orders_persistence.cls.create_from_gspread, sta_input_contents)

    #  Adding manufac item numbers to orders
    db.add_manufac_item_number_to_orders(orders_persistence.objects)

    #  Adding to the temporary new_orders table
    orders_persistence.insert_objects()

    #  Removing anything from the ecomm_order table that doesn't exist in the new_ecomm_order table, representing
    #  orders that have been cancelled or picked up
    db.execute_in_db('''DELETE FROM ecomm_orders WHERE order_number NOT IN (SELECT order_number FROM new_ecomm_orders)''')

    #  Updating shipped/recieved/reserved et for orders in ecomm_orders from new_ecomm_orders
    db.execute_in_db('''UPDATE ecomm_orders
	SET (order_status) = (SELECT new_ecomm_orders.order_status FROM new_ecomm_orders 
	WHERE new_ecomm_orders.order_number = ecomm_orders.order_number) 
	WHERE EXISTS (SELECT * FROM new_ecomm_orders WHERE new_ecomm_orders.order_number = ecomm_orders.order_number)''')

    #  Now, adding the orders to ecomm_orders from new_ecomm_orders that aren't already there
    db.execute_in_db('''INSERT INTO ecomm_orders (order_number, cc_item_num, manufac_item_num, order_date,
            tire_data, labelled_state, order_quantity, order_status) 
            SELECT order_number, cc_item_num, 
            manufac_item_num, order_date, tire_data, labelled_state, order_quantity, order_status
            FROM new_ecomm_orders WHERE order_number NOT IN (SELECT order_number FROM ecomm_orders)''')

    db.execute_in_db('DROP TABLE new_ecomm_orders')

    # Wiping the input spreadsheet
    # sta_input_sheet.clear()


def search_for_order(search_string):
    """Given a manufacturer item number, returns orders"""
    if search_string == '':
        print('Empty search')
        return None

    found_orders_persistence = db.PersistenceManager('ecomm_orders', inv.Order)
    found_orders = found_orders_persistence.objects_from_search(f'manufac_item_num = {search_string}', 'order_date')

    if not found_orders:
        return None

    #  Returning ordered by status as well, and ordered by labelled
    # ret_list = [an_obj for an_obj in found_orders if an_obj.order_status == 'Received'] + \
    #     [an_obj for an_obj in found_orders if an_obj.order_status == 'Reserved'] + \
    #     [an_obj for an_obj in found_orders if an_obj.order_status == 'Shipped'] + \
    #     [an_obj for an_obj in found_orders if an_obj.order_status != 'Received' and
    #         an_obj.order_status != 'Reserved' and an_obj.order_status != 'Shipped']
    found_orders.sort(key=lambda x: x.order_date)  # Sort by date
    ret_list = [i for j in ['Received', 'Reserved', 'Shipped', 'None']
                for i in filter(lambda x: x.order_status == j, found_orders)]
    ret_list = [i for j in ['False', 'True', 'None'] for i in filter(lambda x: x.labelled_state == j, ret_list)]

    # A quick check that my filter based sorting didn't remove elements
    if len(found_orders) != len(ret_list):
        print('Sorting removed elements')
        raise AttributeError

    return ret_list


def toggle_order_labelled(order_db_id):
    """Toggles the labelled state of an order in the db"""

    order_number, labelled_state = \
        db.execute_in_db(f'SELECT order_number, labelled_state FROM ecomm_orders WHERE db_id = {int(order_db_id)}')[0]

    # For testing, making sure the order number is correct
    print('Check this is the button you pressed')
    print(order_number)
    new_state = "'" + str('False' if labelled_state == 'True' else 'True') + "'"
    print(new_state)
    db.execute_in_db(f'UPDATE ecomm_orders SET labelled_state = {new_state} WHERE db_id = {int(order_db_id)}')


def mark_labelled(order_db_id):
    """Marks as labelled, does not toggle"""

    db.execute_in_db(f"UPDATE ecomm_orders SET labelled_state = 'True' WHERE db_id = {int(order_db_id)}")


def search_for_order_by_ordernum(search_string):
    """Takes last 4 digits of order number, returns the db_id.  Can handle last 5 as well"""

    if search_string == '':
        print('Empty search')
        return None

    found_orders_persistence = db.PersistenceManager('ecomm_orders', inv.Order)
    found_orders = found_orders_persistence.objects_from_search(f"order_number LIKE '%{search_string}'", 'order_date')

    if not found_orders:
        return None

    return found_orders


def search_item_number(search_string):
    """Takes a string, searches for item number conversion"""

    cc_results = db.execute_in_db(f'SELECT cc_item_num, manufac_item_num FROM item_numbers WHERE manufac_item_num = {search_string}')
    if cc_results:
        return cc_results

    manufac_results = db.execute_in_db(f'SELECT cc_item_num, manufac_item_num FROM item_numbers WHERE cc_item_num = {search_string}')

    return manufac_results


def all_orders_screen_return():
    """Returns all orders, in the form of a list of the button texts"""

    return db.PersistenceManager('ecomm_orders', inv.Order).objects_from_search('', 'order_date')

    #  TODO Make a function that creates a new IN pair in the gspread sheet, then downloads that to the db file again


def audit_mark_not_present(order_number):
    """Marks an order number not present"""
    db.execute_in_db('''CREATE TABLE IF NOT EXISTS ecomm_audit (db_id integer PRIMARY KEY, order_number text, state text)''')
    db.execute_in_db(f"INSERT INTO ecomm_audit (order_number, state) VALUES ({order_number}, 'NotFound')")


def return_audit_report_items():
    """Returns objects in ecomm audit db.  Wipes that db"""
    db_items = db.execute_in_db('SELECT order_number, state FROM ecomm_audit')
    db.execute_in_db('''DROP TABLE IF EXISTS ecomm_audit''')

    unlabelled_orders = db.execute_in_db("SELECT order_number FROM ecomm_orders WHERE labelled_state = 'False'")
    print(unlabelled_orders)
    audit_report = ''

    for an_order in unlabelled_orders:
        audit_report = audit_report + an_order[0] + ' : Unlabelled' + '\n'

    for an_item in db_items:
        audit_report = audit_report + an_item[0] + ' : ' + an_item[1] + '\n'

    return audit_report


def clear_order_db():
    """Clears the order db and reinitializes"""
    db.execute_in_db('DROP TABLE IF EXISTS ecomm_orders')
    db.execute_in_db('''CREATE TABLE IF NOT EXISTS ecomm_orders 
                       (db_id integer PRIMARY KEY,
                        order_number text,
                        cc_item_num text,
                        manufac_item_num text,
                        order_date text,
                        tire_data text,
                        labelled_state text,
                        order_quantity integer,
                        order_status text)''')


def add_item_number_pair(cc_item_num, manufac_item_num):
    """Given a cc item num and a manufac item num, adds them to the gspread page.  Then redownloads the item number db"""

    gc = gs.g_authenticate()
    item_number_spreadsheet = gc.open_by_key("1K3GCrU0vZeo0sb8b_ydTKoKx_SmQquaRvBe2Gx32eJI").sheet1
    item_number_spreadsheet.append_row((int(cc_item_num), int(manufac_item_num), "Manually appended"))
    db.pull_item_number_table()


def sync_item_db():
    db.pull_item_number_table()