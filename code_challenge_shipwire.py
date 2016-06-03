#!/usr/bin/python

""" Simulation of handling inventories
    and serving orders,
"""
# Tested with Python 2.7.6

import random

# Globals and constants
valid_streams = range(1, 6)
max_quant = 5
#inventory = {"A":10, "B":15, "C":5, "D":12, "E":8}
inventory = {"A":150, "B":150, "C":100, "D":100, "E":200}


class InventoryAllocator(object):
    """Handler of orders: updates state of inventories, records orders,
       allocation of inventories, and backorders.
    """
    def __init__(self):
        self.inventory = inventory
        self.track_order = []
        self.products_in_inventory = self.inventory.keys()
        self.products_in_inventory.sort()
        self.num_of_products = len(self.products_in_inventory)

    def update_inv(self, order_to_process):
        """ Modifies the inventory register based on an incoming order.
        Creates a composit record comprising current order, allocation of
        inventory for the order, and backorder. Adds the record to the
        order catalog by calling update_track_order.
    
        Args:
            order_to_process (dict): description of order
               in the following format:
 
               {"Header": k, "Lines": [{"Product": "A", "Quantity": a},
                    ...,{"Product": "C", "Quantity": c}]}

               where k, a, c, ..., are whole positive numbers
                   from 1 through max_quant.

        Returns:
            bool:  False if all inventory quantities are at 0, True otherwise.
        """
        # all inventory quantities are at zero
        if self.all_inv_at_zero():
            return False

        # init lists - parts of the record
        order_list = [0 for i in range(self.num_of_products)]
        allocated_list = [0 for i in range(self.num_of_products)]
        backorder_list = [0 for i in range(self.num_of_products)]

        # put the ordered quantities in the order list
        for current_line in order_to_process['Lines']:
            order_list[self.products_in_inventory.index(current_line['Product'])] \
                = current_line['Quantity']

        # collect indices of non zero elements of order_list,
        # then address one of 3 possible scenarios:
        # (1) available inventory exceeds or equals to the ordered quantity:
        #     then: allocate as much as was ordered, reduce the inventory
        #     by ordered amount
        # (2) ordered quantity exceed the available inventory:
        #     then: allocate all the inventory for the order,
        #     set the inventory to zero, backorder the lacking amount 
        # (3) the inventory of interest is at zero: backorder the whole ordered amoount
        nonzero_orders = [i for i in range(len(order_list)) if order_list[i] != 0]
        for current_nonz in nonzero_orders:
            product_of_interest = self.products_in_inventory[current_nonz]
            thediff = self.inventory[product_of_interest] - order_list[current_nonz]
            if thediff >= 0:
                self.inventory[product_of_interest] = thediff
                allocated_list[current_nonz] = order_list[current_nonz]                 	
            else:
                backorder_list[current_nonz] = abs(thediff)
                if  self.inventory[product_of_interest] > 0:
                    allocated_list[current_nonz] = self.inventory[product_of_interest]
                    self.inventory[product_of_interest] = 0
                    
        # add the record to the order catalog
	self.update_track_order(order_to_process['Header'], order_list, allocated_list, backorder_list)
        return True

    def all_inv_at_zero(self):
        """ Detects condition \"all inventory dropped to 0\"

        Returns:
            bool: True if all inventory at 0, False otherwise            
        """
        all_zero = True
        for current_level in self.inventory.values():
            all_zero = all_zero and (current_level == 0)

        return all_zero

    def update_track_order(self, header, order_l, allocated_l, backorder_l):
        """ Creates record of the order and adds the record at the end of the order catalog.
        Each record is formated as

            header: <ordered quantities>::<allocated quantities>::<backordered quantities>

        For example:

             2: 1,2,2,5,1::0,2,0,0,1::1,0,2,5,0

        Args:
            header      (int): stream identifier.
            order_l     (list of ints): ordered quantities.
            allocated_l (list of ints): allocated quantities.
            backorder_l (list of ints): backordered quantities. 
        """
        # prep format specifier
	sl = (self.num_of_products - 1 )*"%d," + "%d"
        sl2colon = sl + "::"
        sf = "%d: " + 2*sl2colon + sl            

        # create record of the order and add it to catalog
        item_to_add = sf % tuple([header] + order_l + allocated_l + backorder_l)
        self.track_order.append(item_to_add)

    def output_track_order(self):
        """ Ouputs catalog of orders.
        Number of each order shows as string number.
        """ 
	i = 1
        for current_order in self.track_order:
            print i, "     ", current_order
            i = i + 1
	

def data_source():
    """ Generator of orders.
        
    Yields:     
        The next order formatted as 

        {"Header": 4, "Lines": [{"Product": "A", "Quantity": "1"}, ..., {"Product": "C", "Quantity": "1"}]}

    """
    types_of_products = inventory.keys()

    num_of_product_types = len(inventory)

    while True:
            # select a stream
	    istream = random.choice(valid_streams) 

	    # select number of product types in the given request
	    num_of_products_requested = random.randrange(1, num_of_product_types + 1)

	    # select products 
	    products_requested = random.sample(types_of_products, num_of_products_requested) 

	    # select number of requested units for each selected products
            quantities = num_of_products_requested *[0]
            quantities = [random.randint(1, max_quant) for quantities in quantities]

            # prering and formatting order to return
	    types_and_quant = dict(zip(products_requested, quantities))
	    current_order = {}
	    current_order['Header'] = istream
	    current_order['Lines']  = []
	    for (pro_type, pro_quant) in types_and_quant.items():
		pro_to_quant = {}
		pro_to_quant["Product"] = pro_type
		pro_to_quant["Quantity"] = pro_quant 
		current_order['Lines'].append(pro_to_quant)
	    current_order['Lines'].sort()

            yield current_order
    

def main():
    """ The driving routine.
    Emulates orders arrival and processing. 
    Terminates when inventory drops to zero,
    at which point it outputs the catalog of
    orders.
    """ 

    # activate supplier ot orders
    order_from_source = data_source()	

    # instantiate inventory allocator
    ia = InventoryAllocator()

    # loop "get order" -> "process order"
    i = 0
    while True:
        i = i + 1
    	is_ok = ia.update_inv(next(order_from_source))
        if not is_ok:
            print "\n%d orders were served before inventory dropped to zero\n" % (i - 1)
            break

    # iinventory allocato to output record of all orders
    ia.output_track_order()


if __name__ == '__main__':
    main()

