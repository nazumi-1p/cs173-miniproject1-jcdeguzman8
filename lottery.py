# John Rowan C. De Guzman
# 2019-08681
# This is a modification of the lottery contract as portrayed in Building a dapp on Tezos in SmartPy - Part 2 | TezAsia Hackathon 2022
# https://www.youtube.com/watch?v=CCk5IO-IzZE

# Modifications include:
# Allows user to buy a specified number of tickets, rather than limited to 1 per transaction
# Extra errors will be raised if:
#   -Entered ticket amount invalid (<=0)
#   -Requested tickets is greater than remaining tickets
#   -Amount paid is insufficient for requested tickets

import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        # storage
        self.init(
            players=sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost=sp.tez(1),
            tickets_available=sp.nat(5),
            max_tickets=sp.nat(5),
            operator = sp.test_account("admin").address
        )
    @sp.entry_point
    def buy_ticket(self, ticketcount):
        sp.set_type(ticketcount, sp.TNat)
        
        #Assertions
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(ticketcount > 0, "INVALID NUMBER OF TICKETS")
        sp.verify(self.data.tickets_available - ticketcount >= 0, "INSUFFICIENT TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.mul(sp.tez(1), ticketcount), "INVALID AMOUNT")
        #sp.verify(sp.amount >= sp.tez(1), "INVALID AMOUNT")

        #Storage changes
        r = sp.range(0, ticketcount, step=1)
        sp.for x in r:
            self.data.players[sp.len(self.data.players)] = sp.sender

        self.data.tickets_available = sp.as_nat(self.data.tickets_available - ticketcount)
        #return extra tez
        extra_amount = sp.amount - sp.mul(self.data.ticket_cost, ticketcount)
        sp.if extra_amount > sp.tez(0):
            sp.send(sp.sender, extra_amount)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)
        
        # Assertion
        sp.verify(self.data.tickets_available == 0, "GAME IS STILL ON")
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORIZED")
        
        #Generate winner
        winner_index = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_index]

        # send rewards
        sp.send(winner_address, sp.balance)

        #reset game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    #test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    john = sp.test_account("john")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")

    #contract instance
    lottery = Lottery()
    scenario += lottery

    #buy_ticket
    # normal, simulates returning extra funds
    scenario += lottery.buy_ticket(2).run(
        amount = sp.tez(4), sender = alice
    )
    # simulates insufficient funds error
    scenario += lottery.buy_ticket(3).run(
        amount = sp.tez(2), sender = bob
    )
    # normal
    scenario += lottery.buy_ticket(1).run(
        amount = sp.tez(1), sender = john
    )
    # simulates insufficient tickets error
    scenario += lottery.buy_ticket(3).run(
        amount = sp.tez(3), sender = mike
    )
    # normal
    scenario += lottery.buy_ticket(2).run(
        amount = sp.tez(2), sender = charles
    )
    #end game
    scenario += lottery.end_game(23).run(now = sp.timestamp(3), sender = admin)