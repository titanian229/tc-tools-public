"""Ecomm Order Object"""
from datetime import date as datetimedate


class InventoryObject(object):
    """Abstract for ecomm and inv objects"""

    @classmethod
    def create_from_db(cls, row):
        raise NotImplementedError

    @classmethod
    def create_from_gspread(cls, row):
        raise NotImplementedError

    def insert_to_db(self):
        raise NotImplementedError


class Order(InventoryObject):
    """EcommOrder object.  Represents one order with all associated data
    from the db.
    OrderNumber,CItemNumber,ManufacItemNumber,Date,TireData,
    LabelledStatus,TireQuantity, order_status, and optional db_id"""
    insert_command = '''INSERT INTO ecomm_orders
                            (order_number, cc_item_num, manufac_item_num, order_date,
                             tire_data, labelled_state, order_quantity, order_status)
                             VALUES (:order_number, :cc_item_num, :manufac_item_num, :order_date,
                             :tire_data, :labelled_state, :order_quantity, :order_status)'''

    def __init__(self, order_number, cc_item_num, order_date,
                 tire_data, labelled_state, order_quantity, manufac_item_num=None,
                 order_status=None, db_id=None):
        super(Order, self).__init__()
        self.order_number = order_number  # String
        self.cc_item_num = cc_item_num  # string
        self.order_date = order_date  # string yyyy-mm-dd
        self.tire_data = tire_data  # String of data about the tire
        self.labelled_state = labelled_state  # True or false
        self.order_quantity = order_quantity  # Number of tires ordered
        self.manufac_item_num = manufac_item_num  # string
        self.order_status = order_status  # Received, shipped, reserved, etc.  Expandable.
        self.db_id = db_id  # The unique id for the order in the db, if already entered

    def __str__(self):
        pass

    def insert_db(self):
        """Similar to __dict__, returns a set of key, value, type"""

        column_names = ('order_number', 'cc_item_num', 'order_date', 'tire_data', 'labelled_state', 'order_quantity',
                        'manufac_item_num', 'order_status')
        column_values = (str(self.order_number), str(self.cc_item_num), str(self.order_date), str(self.tire_data),
                         str(self.labelled_state), int(self.order_quantity), str(self.manufac_item_num),
                         str(self.order_status))
        return str(column_names), str(column_values)

    @staticmethod
    def date_parser(date):
        """Takes a dd/mm/yy and returns a string of yyyy-mm-dd, for easier sorting.
        Does so by creating a datetime object"""

        date = date.split('/')
        if len(date) == 3:
            return str(datetimedate(int('20' + str(date[2])), int(date[0]), int(date[1])))
        elif len(date) == 1:
            return str(date[0])
        else:
            print('Date input error')
            raise ValueError

    def get_button_text(self, detail_level):
        """Returns a string of text representing the order to place on buttons on the
           all orders screen or the search screen"""
        if self.order_status == 'Received':
            ord_status = 'R'
        elif self.order_status == 'Reserved':
            ord_status = 'D'
        elif self.order_status == 'Shipped':
            ord_status = 'S'
        else:
            ord_status = self.order_status[:1]
        if detail_level == 'Search':
            ret_text = "{} : {} | #: {}, {} {}".format(self.order_number, self.order_date,
                                                         self.order_quantity, 'Labelled' if bool(self.labelled_state) else 'Unlabelled',
                                                         ord_status)
        elif detail_level == 'All':
            ret_text = "{} : {} | #: {}, {} {}\nManufac: {} CC: {}".format(self.order_number, self.order_date,
                                                                             self.order_quantity,
                                                                             'Labelled' if self.labelled_state == 'True' else 'Unlabelled',
                                                                             ord_status, self.manufac_item_num,
                                                                             self.cc_item_num)
        else:
            raise ValueError

        return ret_text

    # def post(self):
    #     '''Inserts or updates db with order'''
    #
    #     if self.db_id is None:
    #         insert_dict = {'order_number' : self.order_number, 'cc_item_num' : self.cc_item_num,
    #                        'order_date' : self.order_date, 'tire_data' : self.tire_data,
    #                        'labelled_state' : self.labelled_state, 'order_quantity' : self.order_quantity,
    #                        'manufac_item_num' : self.manufac_item_num, 'order_status' : self.order_status}
    #         insert_command = '''INSERT INTO ecomm_orders
    #                             (order_number, cc_item_num, manufac_item_num, order_date,
    #                              tire_data, labelled_state, order_quantity, order_status)
    #                              VALUES (:order_number, :cc_item_num, :manufac_item_num, :order_date,
    #                              :tire_data, :labelled_state, :order_quantity, :order_status)'''
    #
    #         db_work.insert(insert_command, insert_dict)
    #
    #     else:
    #         update_dict = {'order_number' : self.order_number, 'cc_item_num' : self.cc_item_num,
    #                        'order_date' : self.order_date, 'tire_data' : self.tire_data,
    #                        'labelled_state' : self.labelled_state, 'order_quantity' : self.order_quantity,
    #                        'manufac_item_num' : self.manufac_item_num, 'order_status' : self.order_status,
    #                        'db_id' : self.db_id}
    #         update_command = '''INSERT INTO ecomm_orders
    #                             (order_number, cc_item_num, manufac_item_num, order_date,
    #                              tire_data, labelled_state, order_quantity, order_status, db_id)
    #                              VALUES (:order_number, :cc_item_num, :manufac_item_num, :order_date,
    #                              :tire_data, :labelled_state, :order_quantity, :order_status, :db_id)'''
    #         db_work.insert(update_command, update_dict)

    @classmethod
    def create_from_gspread(cls, row):
        """Creates an order object from the raw google sheet input"""
        # stripping empty items
        row = [x for x in row if x != '' and x != ' ']

        if len(row) == 8:  # The initial input from spreadsheet, assuming labelled is False
            (cc_item_num, tire_data, order_status, order_date, order_number,
             _, _, order_quantity) = row
            order_date = cls.date_parser(order_date)
            labelled_state = False
            return cls(order_number, cc_item_num, order_date,
                       tire_data, labelled_state, order_quantity, order_status=order_status)
        elif len(row) == 6:
            #This is a reserved, missing POs
            (cc_item_num, tire_data, order_status, order_date, order_number, order_quantity) = row
            order_date = cls.date_parser(order_date)
            labelled_state = True #Assumes reserveds are labelled
            return cls(order_number, cc_item_num, order_date,
                       tire_data, labelled_state, order_quantity, order_status=order_status)
        elif len(row) == 7:  # This has been pushed to the ss, has a labelled status
            (cc_item_num, tire_data, order_status, order_date, order_number,
             order_quantity, labelled_state) = row
            return cls(order_number, cc_item_num, order_date,
                       tire_data, labelled_state, order_quantity, order_status=order_status)

    @classmethod
    def create_from_db(cls, row):
        """Creates an order from single row of SELECT * string in db"""

        (db_id, order_number, cc_item_num, manufac_item_num, order_date,
         tire_data, labelled_state, order_quantity, order_status) = row
        return cls(order_number, cc_item_num, order_date, tire_data,
                   labelled_state, order_quantity, manufac_item_num,
                   order_status, db_id)


class InvTransaction(InventoryObject):
    """Inventory object, represents line in NSSDR or TSA1"""

    def __init__(self, invoice_number, trans_date, cc_item_num, quantity, amount, db_id=None):
        super(InvTransaction, self).__init__()

        self.invoice_number = str(invoice_number)
        self.trans_date = self.date_parser(trans_date)
        self.cc_item_num = str(cc_item_num)
        self.quantity = int(float(quantity))  # Takes both 1 or -1 and 1.00 and -1.00 and converts to integer
        self.amount = str(float(amount)) # Converts to float, to deal with trailing zeroes getting removed in sheets
        self.db_id = db_id

    def report_format(self):
        return [str(self.cc_item_num), str(self.quantity), str(self.amount), str(self.invoice_number), str(self.trans_date)]

    def insert_db(self):
        """Similar to __dict__, returns a set of key, value, type"""

        column_names = ('cc_item_num',  'trans_date', 'quantity', 'amount', 'invoice_number')
        column_values = (str(self.cc_item_num), str(self.trans_date), self.quantity, str(self.amount),
                         str(self.invoice_number))
        return str(column_names), str(column_values)


    @classmethod
    def create_from_db(cls, row):
        """Creates an object from a row of the db"""

        (cc_item_num, date, quantity, amount, invoice_number, db_id) = row

        return cls(invoice_number, date, cc_item_num, quantity, amount, db_id)

    @classmethod
    def create_from_tsa1_row(cls, row):
        """Creates an object from a tsa1 row in google sheets"""

        row = [x for x in row if x != '' and x != ' ']

        (invoice_number, date, item_num, quantity, amount) = row
        date = cls.date_parser(date)

        return cls(invoice_number, date, item_num, quantity, amount)

    @staticmethod
    def date_parser(date):
        """Parses date into yyyy-mm-dd"""
        date = date.split('/')
        if len(date) == 3:
            return str(datetimedate(int('20' + str(date[2])), int(date[0]), int(date[1])))
        elif len(date) == 1:
            return str(date[0])
        else:
            print('Date input error')
            raise ValueError
