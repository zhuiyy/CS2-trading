from cs2_trading.data.inventory import Inventory, Stuff

def end_day(inventory: Inventory) -> None:
    for item in inventory.items:
        item.in_hand += 1
        if item.in_hand >= 7:
            item.ready_to_sell = True

    inventory.items.sort(key=lambda x: (x.id, -x.in_hand, x.bought_price))




if __name__ == "__main__":
    stuff1 = Stuff(id=1, name="ItemA", bought_price=10.0)
    stuff2 = Stuff(id=2, name="ItemB", bought_price=15.0)
    stuff3 = Stuff(id=1, name="ItemC", bought_price=12.0)

    inventory = Inventory(items=[stuff1, stuff2, stuff3])
    print("Before end_day:")
    print(inventory)

    end_day(inventory)

    print("After end_day:")
    print(inventory)
