"""main.py
The main kivy program
"""

# Kivy Imports
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
# from kivy.uix.boxlayout import BoxLayout
# from kivy.clock import Clock
from kivy.core.window import Window
Window.clearcolor = (0, 0.8, 0.6, 1)

# Custom Module Imports
from inv_tools import generate_nssdr_tsa1_report
import ecomm_tools


class ScreenMain(Screen):
    """Primary menu screen"""
    pass


class ScreenOther(Screen):
    pass


class ScreenSearchIN(Screen):
    """Input for item number, option to search for order or just CC IN"""
    pass


class ScreenOutputLabel(Screen):
    """Output screen for tire labels"""

    chosen_label_button = ObjectProperty()


class ScreenOutput(Screen):
    """basic general purpose output screen"""
    output = StringProperty('')
    orderinfo = ObjectProperty()


class ScreenFixIN(Screen):
    """Screen for adding IN pairs"""
    pass


class ScreenOrderList(Screen):
    pass


class ScreenListOptions(Screen):
    pass


class ScreenAuditOrders(Screen):
    pass


class ScreenInventoryTools(Screen):
    pass


class SM(ScreenManager):
    data_pass = StringProperty()
    pass


class WarningPopup:
    text = StringProperty()

    def __init__(self, **kwargs):
        super(WarningPopup, self).__init__(**kwargs)


class ScreenLabelOutput:
    pass


class LabelButton(Button):
    lb = ObjectProperty()
    scr = ObjectProperty()
    pass


class OrderListLabel(Label):
    pass


class tctoolsApp(App):
    def build(self):
        self.passed_order = StringProperty('')
        self.icon = 'icon.png'
        return SM()

    def display_popup(self, label_text):
        """Displays a popup with a given label text"""
        ly = GridLayout(cols=1, padding=10)
        bt = Button(text='Close', size_hint=(1, 0.1))
        lb = Label(text=label_text, markup=True)
        ly.add_widget(lb)
        ly.add_widget(bt)
        pp = Popup(title='Alert', content=ly,
                   size_hint=(0.9, 0.9))
        pp.open()
        bt.bind(on_press=pp.dismiss)


    #  Inv Tools Functionality

    def create_inv_report(self):
        """Wipes old report, Imports data from gspread for TSA1 and NSSDR, creates db, runs report and erases inputs"""

        generate_nssdr_tsa1_report()

    # Ecomm Functionality

    #  TODO Alter, move functions to other files, streamline

    def all_order_screen(self):
        """Populates and shows all orders screen"""

        all_orders = ecomm_tools.all_orders_screen_return()

        self.display_orders(all_orders)

    def audit_orders(self):
        """Audits the orders present.  Presents page with search, similar to search page.  When last 4 digits are typed
        in shows
        all matching orders.  When order is clicked it sets it as labelled in db if not already so.  Button at bottom of
         page to click, that presents report on
          all unlabelled tires"""

    def audit_order_search(self, search_string):
        """Takes a 4 digit number, the last four of an order.  Searches for order.  If only one found, marks as labelled.
          If mult found, return a page with
        all present orders"""

        results = ecomm_tools.search_for_order_by_ordernum(search_string)

        if results is None:
            self.display_popup("No orders found")
            ecomm_tools.audit_mark_not_present(search_string)
            return

        if len(results) == 1:
            # Only one found, label and carry on

            print('One found, marking as labelled')
            print(results[0].order_number)
            ecomm_tools.mark_labelled(results[0].db_id)

        if len(results) > 1:
            self.display_popup("Multiple orders found and that feature is not yet\n implemented.\
              Search by more digits please.")

        # TODO add ability to handle multiple results

    def show_audit_report(self):
        """Shows a page with all orders that are unlabelled, and all that are labelled but not found"""
        audit_report = ecomm_tools.return_audit_report_items()
        self.display_popup(audit_report)

    def all_orders_button_press(self, button_instance):
        """Action taken when button pressed on all orders screen.  Toggles labelled, changes colour."""

        # Update the db, changing the status of the order
        ecomm_tools.toggle_order_labelled(button_instance.lb)

        if button_instance.background_color == [0, 0.6, 0.7, 1]:  # Order is labelled, changing to unlabelled
            button_instance.background_color = [0, 0.6, 0.4, 1]
            button_instance.text = button_instance.text.replace('Labelled', 'Unlabelled')
        else:
            button_instance.background_color = [0, 0.6, 0.7, 1]
            button_instance.text = button_instance.text.replace('Unlabelled', 'Labelled')

    #  TODO Change variable names to fit PEP8, refactor kivy code once app functions

    #  TODO use inheritance more.  Esp for build_from_db, that can exist in a common class?

    def update_sta_button_action(self):
        # try:
        ecomm_tools.update_order_table_from_gspread()
        # except:
        #     print('Update failure')
        #     self.display_popup('Google Authentication Failure\nList not updated')
        #     return

        ly = GridLayout(cols=1, padding=10)
        bt = Button(text='Close', size_hint=(1, 0.1))
        lb = Label(text="Success!")
        ly.add_widget(lb)
        ly.add_widget(bt)
        pp = Popup(title='Warning', content=ly,
                   size_hint=(0.9, 0.9))
        pp.open()
        bt.bind(on_press=pp.dismiss)
        print('success')

    def search_order(self, search_string):
        """Takes a manufacturer item number, returns orders based on that"""
        results = ecomm_tools.search_for_order(search_string)

        if results is None:
            self.display_popup("No orders found")
            return

        self.display_orders(results)

        # self.root.ids.screen_labeloutput.orderinfo = \
        #     'Found orders for item number ' + str(results[0].cc_item_num) + '\n' + str(results[0].tire_data)
        #
        # lo_screen = self.root.ids.screen_labeloutput  # self.root.get_screen('screenlabeloutput')
        # sv = lo_screen.ids.labelout_sv
        #
        # for an_order in results:
        #     if an_order.labelled_state == 'False':
        #         colr = (0, 0.6, 0.4, 1)
        #     elif an_order.labelled_state == 'True':
        #         colr = (0, 0.6, 0.7, 1)
        #     else:
        #         colr = (1, 1, 1, 1)
        #         print('what')
        #     tb = LabelButton(text=an_order.get_button_text('Search'),
        #                      background_color=colr,
        #                      lb=an_order.db_id,  # Passing in the order's db_id
        #                      scr=lo_screen)
        #     sv.add_widget(tb)
        #     tb.bind(on_press=self.label_button_press)
        # self.root.current = 'screenlabeloutput'

    def label_button_press(self, button_instance):
        """Action taken when button pressed, changes labelled state in db and colour of button"""

        # Changing said entry to labelled in the database
        order_db_id = button_instance.lb
        print(button_instance)
        ecomm_tools.toggle_order_labelled(order_db_id)

        #  TODO Show a separate screen with the proper label, and a button to return to the previous screen

        # Returning to main screen
        self.root.current = 'ininputscreen'

        # Removing the label widgets from the old screen
        self.root.ids.screen_labeloutput.ids.labelout_sv.clear_widgets()

    def button_search_item_number(self, search_string):
        """Takes a string, searches first for cc item num then manufac"""

        results = ecomm_tools.search_item_number(search_string)
        print(results)

        search_return_label_texts = []
        if not results:
            search_return_label_texts.append('No matches found')

        else:
            for an_item_pair in results:
                search_return_label_texts.append('''
                        Found Item Number\n[b]CC[/b]                     : {}\n[b]Manufacturer[/b]  : {}'''.format(
                    an_item_pair[0], an_item_pair[1]))

        lyroot = GridLayout(cols=1)  # Root, holding results layout and button
        ly = GridLayout(cols=1, padding=10)
        bt = Button(text='Close', size_hint=(1, 0.1))
        for a_label in search_return_label_texts:
            ly.add_widget(Label(text=a_label, font_size='16sp', markup=True, size_hint_y=None))
            # Adding the labels to the grid
        # lb = Label(text=search_return,markup=True)
        lyroot.add_widget(ly)
        lyroot.add_widget(bt)
        pp = Popup(title='Found Item Number', content=lyroot,
                   size_hint=(0.9, 0.9))
        pp.open()
        bt.bind(on_press=pp.dismiss)

    def button_search_order_number(self, search_string):
        """Searches for an order based on the order number"""

        results = ecomm_tools.search_for_order_by_ordernum(search_string)

        if results is None:
            self.display_popup("No orders found")
            return

        self.display_orders(results)

    def display_orders(self, order_objects):
        """Takes a tuple of order objects, displays them.  Clicks toggle the labelled state."""

        self.root.ids.screen_labeloutput.ids.labelout_sv.clear_widgets()

        page_info_title = str(len([x for x in order_objects if x.order_status == 'Received'])) + \
            ' received and ' + str(len([x for x in order_objects if x.order_status == 'Shipped'])) + \
            ' shipped and ' + str(len([x for x in order_objects if x.order_status == 'Reserved'])) + \
            ' reserved'

        self.root.ids.screen_labeloutput.orderinfo = page_info_title

        lo_screen = self.root.ids.screen_labeloutput  # self.root.get_screen('screenlabeloutput')
        sv = lo_screen.ids.labelout_sv

        for an_order in order_objects:
            if an_order.labelled_state == 'False':
                colr = (0, 0.6, 0.4, 1)
            elif an_order.labelled_state == 'True':
                colr = (0, 0.6, 0.7, 1)
            else:
                colr = (1, 1, 1, 1)
                print('what')
            tb = LabelButton(text=an_order.get_button_text('All'),
                             background_color=colr,
                             lb=an_order.db_id,
                             scr=lo_screen)
            sv.add_widget(tb)
            tb.bind(on_press=self.all_orders_button_press)

        self.root.current = 'screenlabeloutput'

    def clear_order_file_button(self):
        """Clears the order db"""

        ecomm_tools.clear_order_db()

    def add_missing_in_pair(self, cc_item_num, manufac_item_num):
        """Adds a set of item numbers to the gspread page.  Then it wipes the item number database and reacquires it"""

        ecomm_tools.add_item_number_pair(cc_item_num, manufac_item_num)
        self.display_popup("Item number successfully added")

    def sync_item_number_db(self):
        """Deletes and resyncs the item number database"""
        ecomm_tools.sync_item_db()

    def push_order_db_to_cloud(self):
        """Pushes the order db to the cloud"""
        # TODO implement pushing ecomm db to cloud


if __name__ == '__main__':
    tctoolsApp().run()