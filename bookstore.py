import csv
from datetime import datetime
from typing import Tuple, Optional, List

from geopy import Nominatim
from geopy.distance import geodesic

"""Feature Card:
-----------------------
Our bookstore's customer base is expanding, and we're introducing new order types to meet diverse customer needs.
1. Some customers are eligible for promotional discounts. We need a way to handle these discounted orders.
2. We're going global! For customers ordering from outside our country, we need to include additional shipping charges based on their location.
Your task: Enhance the Order system to support these new requirements. Aim for a solution that integrates smoothly with our existing system and can be easily expanded in the future as we grow.
Note: Your focus is on enhancing the product's capabilities. Think about how to structure your solution to make the system more adaptable and maintainable."""

"""
1 - Example of discounts:
Pre order discount => (target a specific group of customers) 
Discount for customer who's account is 1 year old
Discount for customer during black friday
Discount for customer from a specific location 

Post order discount => (target a product or an amount)
Discount for customer for a specific author
Discount for a customer using a COUPON code
Discount free shiping for order above 50$

"""


class Location:
    BERLIN = "berlin"
    PARIS = "PARIS"


class Discount:
    def __init__(self, id, start_valid, end_valid, amount=0, nb_usage=1, coupon_code=None, author_specific=None):
        self.id: int = id
        self.start_valid: datetime = start_valid
        self.end_valid: datetime = end_valid
        self.amount: float = amount
        self.nb_usage: int = nb_usage
        self.coupon_code: str = coupon_code
        self.author_specific: str = author_specific

    @property
    def valid(self):
        return (datetime.now() >= self.start_valid) and (datetime.now() <= self.end_valid)

    def __str__(self):
        return f"Discount: {(self.id, self.amount)}"


class Book:
    def __init__(self, title, author, price):
        self.title: str = title
        self.author: str = author
        self.price: float = price

    def __str__(self):
        return f"Book: {self.title}"


class Shipping:
    def __init__(self):
        pass

    @classmethod
    def get_coordinates(cls, city) -> Optional[Tuple[float, float]]:
        geolocator = Nominatim(user_agent="qevlar-ai")
        location = geolocator.geocode(city)
        return (location.latitude, location.longitude) if location else None

    @classmethod
    def calculate_distance(cls, capital1, capital2) -> Optional[float]:

        # Get coordinates for the capitals
        coordinates1 = cls.get_coordinates(capital1)
        coordinates2 = cls.get_coordinates(capital2)

        if coordinates1 and coordinates2:
            # Calculate distance using geopy
            distance_km = geodesic(coordinates1, coordinates2).kilometers
            return distance_km
        else:
            return None

    @classmethod
    def shipping_cost(cls, store_location, customer_location) -> float:
        distance = cls.calculate_distance(store_location, customer_location)
        if distance is not None:
            return 0.02 * distance
        return 0


class Order:
    def __init__(self):
        self.books: List[Tuple[Book, int]] = []
        self.customer: Optional[Customer] = None

    def add_book(self, book, quantity):
        self.books.append((book, quantity))

    def apply_coupon(self):
        pass

    def calculate_total_price(self) -> float:
        # apply targeted customer discount
        author_specific_discounts = list(filter(lambda discount: discount.valid and discount.author_specific, self.customer.discounts))
        valid_discounts = list(filter(lambda discount: discount.valid and not discount.author_specific, self.customer.discounts))

        # apply product specific discount (psd)
        total_price = 0
        for book, quantity in self.books:
            psd = next(filter(lambda discount: discount.author_specific == book.author, author_specific_discounts), None)
            discount = 1 - psd.amount if psd else 1
            total_price += book.price * discount * quantity
            if psd:
                psd.nb_usage -= 1
                if psd.nb_usage == 0:
                    # remove the discount after usage
                    self.customer.discounts = list(filter(lambda x: x.id != psd.id, self.customer.discounts))

        # apply each targeted discount and product discount
        for discount in valid_discounts:
            total_price *= (1 - discount.amount)
            discount.nb_usage -= 1
            if discount.nb_usage == 0:
                # remove the discount after usage
                self.customer.discounts = list(filter(lambda x: x.id != discount.id, self.customer.discounts))

        # apply threshold and other discount
        shipping_cost = Shipping.shipping_cost("paris", self.customer.location)
        if total_price > 50:
            shipping_cost = 0
        return round(total_price + shipping_cost, 2)

    def __str__(self) -> str:
        return f"Order: {self.books}"


class Customer:
    def __init__(self, username, location, signup_date):
        self.username: str = username
        self.location: str = location
        self.signup_date: datetime = signup_date
        self.discounts: List[Discount] = []
        self.order: Optional[Order] = None

    def place_order(self, books_selected):
        order = Order()
        self.order = order
        order.customer = self

        for book, quantity in books_selected:
            order.add_book(book, quantity)

    def __str__(self) -> str:
        return f"Customer: {(self.username, self.location)}"


class MasterData:
    def __init__(self):
        self.books: List[Book] = []
        self.discounts: List[Discount] = []
        self.customers: List[Customer] = []

    def init_master_data(self):
        self.init_books()
        self.init_customers()
        self.init_discounts()

    def init_discounts(self):
        with open("./master-data/discounts.csv", mode="r") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                # Convert string representations to datetime objects
                start_valid = datetime.strptime(row["start_valid"], "%Y-%m-%d %H:%M:%S")
                end_valid = datetime.strptime(row["end_valid"], "%Y-%m-%d %H:%M:%S")

                discount = Discount(
                    id=int(row["id"]),
                    start_valid=start_valid,
                    end_valid=end_valid,
                    amount=float(row["amount"]),
                    nb_usage=int(row["nb_usage"]),
                    coupon_code=row["coupon_code"],
                )
                self.discounts.append(discount)

    def init_customers(self):
        with open("./master-data/customers.csv", mode="r") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                signup_date = datetime.strptime(row["signup_date"], "%Y-%m-%d").date()
                customer = Customer(
                    username=row["username"],
                    location=row["location"],
                    signup_date=signup_date
                )
                self.customers.append(customer)

    def init_books(self):
        with open("./master-data/books.csv", mode="r") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                book = Book(
                    title=row["title"],
                    author=row["author"],
                    price=float(row["price"])
                )
                self.books.append(book)

    def __str__(self):
        return f"""
        Books: {[str(book) for book in self.books]}
        Customers: {[str(customer) for customer in self.customers]}
        Discounts: {[str(discount) for discount in self.discounts]}
        """


class Store:
    def __init__(self, master_data: MasterData):
        self.master_data = master_data

    def select_discount(self, id):
        return next(filter(lambda discount: discount.id == id, self.master_data.discounts), None)

    def select_discounts(self, valid: bool):
        return list(filter(lambda discount: discount.valid == valid, self.master_data.discounts))

    def select_customer(self, username):
        return next(filter(lambda customer: customer.username == username, self.master_data.customers), None)

    def select_customers(self, location):
        return list(filter(lambda customer: customer.location == location, self.master_data.customers))

    def select_book(self, title):
        return next(filter(lambda book: book.title == title, self.master_data.books), None)

    def select_books(self, author):
        return list(filter(lambda book: book.author == author, self.master_data.books))

    def discount_one_year_customers(self, discount_id):
        # clients who's account was created 1 year or more ago will benefit from a discount
        selected_discount = self.select_discount(discount_id)
        selected_customers = [customer for customer in self.master_data.customers if
                              (datetime.now().date() - customer.signup_date).days >= 365]
        for customer in selected_customers:
            customer.discounts.append(selected_discount)

    def discount_black_friday(self, discount_id):
        # all black friday everyone gets a discount
        today = datetime.now().date()
        if today == datetime(today.year, 11, 24).date():
            selected_discount = self.select_discount(discount_id)
            for customer in self.master_data.customers:
                customer.discounts.append(selected_discount)

    def discount_location(self, discount_id, location):
        selected_discount = self.select_discount(discount_id)
        selected_customers = self.select_customers(location.lower())
        for customer in selected_customers:
            customer.discounts.append(selected_discount)

    def discount_specific_author(self, discount_id, author):
        selected_discount = self.select_discount(discount_id)
        selected_discount.author_specific = author
        selected_customers = self.master_data.customers
        for customer in selected_customers:
            customer.discounts.append(selected_discount)

    def run_all_discount_rules(self):
        self.discount_black_friday(2)
        self.discount_one_year_customers(1)


# execution
def main():
    # init master data
    master_data = MasterData()
    master_data.init_master_data()
    # create a store
    store_session = Store(master_data)

    # distribute discounts to customers according to rules
    # could be made into a cronjob in a real app
    store_session.discount_one_year_customers(1)
    store_session.discount_location(2, "berlin")
    store_session.discount_specific_author(3, "Douglas Adams")

    joe_doe = store_session.select_customer(username="john_doe")
    books_selected = [
        ("The Hitchhiker's Guide to the Galaxy", 1),
        ("Dune", 2),
        ("Starship Troopers", 1)
    ]
    books = [(store_session.select_book(title=title), quantity) for title, quantity in books_selected]
    joe_doe.place_order(books)

    print(joe_doe.order.calculate_total_price())


if __name__ == "__main__":
    main()
