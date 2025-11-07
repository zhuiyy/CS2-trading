from cs2_trading.cs2_daily import Inventory, Stuff

def buy_item(inventory: Inventory, item: Stuff, quantity: int) -> None:
    for _ in range(quantity):
        inventory.items.append(item)