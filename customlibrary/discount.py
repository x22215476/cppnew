class DiscountManager:
    def __init__(self):
        pass

    def apply_discount(self, total_price):
        # Apply a 5% discount
        discounted_price = total_price * 0.95
        return discounted_price
