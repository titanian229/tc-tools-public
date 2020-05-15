'''Functions related to inventory checking, rectifying nssdr to tsa1'''
import resources.db_work as db
import objects.inventory_objects as inventory_objects
import g_sheets.g_sheets as g_sheets
from datetime import date as datetimedate

def generate_nssdr_tsa1_report():
    """Generates a report rectifying NSSDR and TSA1"""

    db.drop_inv_tools_tables()
    # TODO Update so the table is preserved, and it checks if data exists already

    # GETTING TSA1
    gc = g_sheets.g_authenticate()

    inv_spreadsheet = gc.open_by_key("1bwgIwWbYVTuuVW18oIXYwjrGmE1nf3W9i3zEvW6YgmM")
    if inv_spreadsheet is None:
        print('Authentication failure')
        raise ValueError('Auth failure')

    tsa1_input_spreadsheet = inv_spreadsheet.worksheet('TSA1Input')
    tsa1_input_spreadsheet_contents = tsa1_input_spreadsheet.get_all_values()

    if len(tsa1_input_spreadsheet_contents) < 4:
        # The list is empty
        return False

    # The sheet is not empty
    tsa1_persistence = db.PersistenceManager('tsa1', inventory_objects.InvTransaction)

    for a_row in tsa1_input_spreadsheet_contents:
        tsa1_persistence.objects.append(inventory_objects.InvTransaction.create_from_tsa1_row(a_row))

    # Logging those objects to the db file in the standard format
    tsa1_persistence.insert_objects()

    print('TSA1 items successfully added')

    #  GETTING NSSDR
    nssdr_input_spreadsheet = inv_spreadsheet.worksheet('NSSDRInput')
    nssdr_input_spreadsheet_contents = nssdr_input_spreadsheet.get_all_values()

    if len(nssdr_input_spreadsheet_contents) < 4:
        return False

    nssdr_persistence = db.PersistenceManager('nssdr', inventory_objects.InvTransaction)


    #Looping to create objects
    row_num = 0
    while True:
        a_row = [x for x in nssdr_input_spreadsheet_contents[row_num][0].split(' ') if x != '']
        date_check = a_row[0].split('/')

        if len(date_check) != 3:
            # This is a row beginning with an item number
            cc_item_num = int(a_row[0])

            # Looping to find the date in the row
            i = 1
            while i < len(a_row):

                date_check = a_row[i].split('/')
                if len(date_check) == 3:
                    date = str(datetimedate(int('20' + str(date_check[2])), int(date_check[0]), int(date_check[1])))
                    quantity = float(a_row[i + 3])
                    dollar_amount = a_row[i + 4]
                    break

                #  TODO add check for row with no date present
                i += 1
        elif len(date_check) == 3:
            # This is a row following one with an itemnum, assume the itemnum is assigned already and use it

            date = str(datetimedate(int('20' + str(date_check[2])), int(date_check[0]), int(date_check[1])))
            quantity = float(a_row[3])
            dollar_amount = a_row[4]
        else:
            # Ya dun fucked up son
            print('Error 24, row error')
            raise ValueError

        invoice_number = nssdr_input_spreadsheet_contents[row_num + 1][0].split('B/T Form: ')[1]

        nssdr_persistence.objects.append(inventory_objects.InvTransaction(invoice_number, date,
                                                                          cc_item_num, quantity, dollar_amount))
        row_num += 2
        if row_num > len(nssdr_input_spreadsheet_contents) - 1:
            break

    nssdr_persistence.insert_objects()

    # GENERATING REPORT

    accurate_keyed_list = []
    to_be_keyed = []
    keys_to_be_reversed = []
    reversed_keys = []

    # Woo party time, the fun part

    # Iterating NSSDR to remove corrected amounts
    nssdr_neg_table = db.execute_in_db("SELECT cc_item_num, trans_date, quantity, amount, invoice_number,\
     db_id FROM nssdr WHERE quantity = '-1'")

    for a_row in nssdr_neg_table:

        inv_obj = inventory_objects.InvTransaction.create_from_db(a_row)

        match = db.execute_in_db(f"""SELECT cc_item_num, trans_date, quantity, amount, invoice_number, db_id from nssdr 
                    WHERE cc_item_num={inv_obj.cc_item_num} AND invoice_number={inv_obj.invoice_number}
                     AND amount={inv_obj.amount} AND quantity='1'""",)

        if match:
            print('Match is for ', str(inv_obj))
            print(match)
            # Delete each from nssdr
            # Delete original
            db.execute_in_db(f"DELETE FROM nssdr WHERE db_id = {a_row[-1]}")
            # Delete match
            db.execute_in_db(f"DELETE FROM nssdr WHERE db_id = {match[0][-1]}")
            reversed_keys.append(inv_obj)

    # Grabbing entire TSA1 db to iterate
    tsa1_table = db.execute_in_db('''SELECT cc_item_num, trans_date, quantity, amount, invoice_number, db_id FROM tsa1''')

    for a_row in tsa1_table:

        # Making the row into an object
        inv_obj = inventory_objects.InvTransaction.create_from_db(a_row)

        # Iterating through each
        # Check for matching item in NSSDR with same itemnumber, invoice number, and amount
        matches = db.execute_in_db(f"""SELECT cc_item_num, trans_date, quantity, amount, invoice_number, db_id FROM
nssdr WHERE cc_item_num = {inv_obj.cc_item_num} AND invoice_number = {inv_obj.invoice_number} AND amount = {inv_obj.amount}""")
        print('SEARCHING')
        print('Matching ', str(inv_obj.report_format()))

        # If matches, remove from both dbs and add to corrections list
        if matches:
            accurate_keyed_list.append(inv_obj)

            # Remove from tsa1
            db.execute_in_db(f'''DELETE FROM tsa1 WHERE db_id = {inv_obj.db_id}''')
            # Delete from nssdr
            db.execute_in_db(f'''DELETE FROM nssdr WHERE db_id = {matches[0][-1]}''')
            print('Match found, deleted from both dbs')

        else:
            # No match, put on list to correct
            to_be_keyed.append(inv_obj)
            db.execute_in_db(f'''DELETE FROM tsa1 WHERE db_id = {inv_obj.db_id}''')

    # Now sorting NSSDR for anything not removed
    nssdr_table = db.execute_in_db('''SELECT cc_item_num, trans_date, quantity, amount, invoice_number, db_id FROM nssdr''')
    print('This is what is left in nssdr')
    print(nssdr_table)

    for a_row in nssdr_table:
        keys_to_be_reversed.append(inventory_objects.InvTransaction.create_from_db(a_row))

    print('\nsuccessfully keyed')
    [print(i) for i in accurate_keyed_list]
    print('\nto be made')
    [print(i) for i in to_be_keyed]
    print('\nTo be reversed')
    [print(i) for i in keys_to_be_reversed]
    print('\nReversed already')
    [print(i) for i in reversed_keys]
    print('Total is ', len(accurate_keyed_list) + len(to_be_keyed) + len(keys_to_be_reversed) + len(reversed_keys))

    # Now, adding to sheets the full report
    report_contents = []
    title_filler = [''] * 4
    title = ['TSA1 and NSSDR Report (J TC Tools app v1)'] + title_filler
    report_header = ['Item Number', 'Quantity', 'Amount', 'Invoice Number', 'Date']
    blank_space = [''] * 5

    report_contents.append(title)
    report_contents.append(report_header)
    report_contents.append(blank_space)
    report_contents.append(['Items to be Keyed'] + title_filler)

    for an_obj in to_be_keyed:
        report_contents.append(an_obj.report_format())

    report_contents.append(blank_space)
    report_contents.append(['Keyed-Outs needing reversal'] + title_filler)

    for an_obj in keys_to_be_reversed:
        report_contents.append(an_obj.report_format())

    report_contents.append(blank_space)
    report_contents.append(['Keyed Out'] + title_filler)

    for an_obj in accurate_keyed_list:
        report_contents.append(an_obj.report_format())

    report_contents.append(blank_space)
    report_contents.append(['Reversed Keys'] + title_filler)

    for an_obj in reversed_keys:
        report_contents.append(an_obj.report_format())

    # Insert into gspread
    # inv_spreadsheet = inv_spreadsheet.worksheet('Output')
    inv_spreadsheet.worksheet('Output').clear()
    inv_spreadsheet.values_update('Output!A1',
                                  params={'valueInputOption': 'RAW'},
                                  body={'values': report_contents})
    inv_spreadsheet.worksheet('TSA1Input').clear()
    inv_spreadsheet.worksheet('NSSDRInput').clear()