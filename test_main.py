import pytest
from bookstore import Store, MasterData, Shipping


@pytest.fixture
def master_data():
    """
    Fixture to provide sample data for testing.
    """
    master_data = MasterData()
    master_data.init_master_data()
    return master_data


@pytest.fixture
def store(master_data):
    """
    Fixture to create a Store instance with sample data.
    """
    store = Store(master_data)
    return store


def test_select_customer(store):
    customer = store.select_customer(username="john_doe")
    assert customer is not None
    assert customer.username == "john_doe"


def test_select_discount(store):
    discount = store.select_discount(id=1)
    assert discount is not None
    assert discount.id == 1


def test_discount_one_year_customers(store):
    # it has to work because the customer is ancient enough
    store.discount_one_year_customers(1)
    customer = store.select_customer(username="john_doe")
    assert any(discount.id == 1 for discount in customer.discounts)


@pytest.mark.freeze_time('2023-11-24')
def test_discount_black_friday(store):
    # discount rule should be applied correctly to the customer profil
    store.discount_black_friday(2)
    customer = store.select_customer(username="john_doe")
    assert any(discount.id == 2 for discount in customer.discounts)


@pytest.mark.freeze_time('2023-11-23')
def test_discount_black_friday(store):
    # discount rule should be applied correctly to the customer profil
    store.discount_black_friday(2)
    customer = store.select_customer(username="john_doe")
    assert not any(discount.id == 2 for discount in customer.discounts)


def test_discount_location(store):
    # Assuming the discount rule is applied correctly
    store.discount_location(3, location="berlin")
    customer = store.select_customer(username="john_doe")
    assert any(discount.id == 3 for discount in customer.discounts)


def test_discount_specific_author(store):
    # Assuming the discount rule is applied correctly
    store.discount_specific_author(4, author="Douglas Adams")
    customer = store.select_customer(username="john_doe")
    assert any(discount.id == 4 for discount in customer.discounts)


def test_order_calculate_total_price(store):
    """
    discount one year client: 10%
    discount location: 20%
    discount for books of Douglas Adams: 40%

    """
    # define discount campaign
    store.discount_one_year_customers(1)
    store.discount_location(2, "berlin")
    store.discount_specific_author(3, "Douglas Adams")

    joe_doe = store.select_customer(username="john_doe")
    books_selected = [
        ("The Hitchhiker's Guide to the Galaxy", 1),
        ("Dune", 2),
        ("Starship Troopers", 1)
    ]
    books = [(store.select_book(title=title), quantity) for title, quantity in books_selected]
    joe_doe.place_order(books)

    total_price = joe_doe.order.calculate_total_price()
    assert total_price == round((12.99*0.6 + 2 * 14.95 + 12.75)*0.9*0.8 + Shipping.shipping_cost("paris", joe_doe.location),2)  # Assuming the correct calculations


def test_discount_usage_decreases_when_used(store):
    # Assuming the discount rule is applied correctly
    store.discount_one_year_customers(1)

    joe_doe = store.select_customer(username="john_doe")
    discount = next((d for d in joe_doe.discounts if d.id == 1), None)

    assert discount is not None
    initial_usage = discount.nb_usage

    books_selected = [
        ("The Hitchhiker's Guide to the Galaxy", 1),
    ]
    books = [(store.select_book(title=title), quantity) for title, quantity in books_selected]
    joe_doe.place_order(books)

    # Calculate total price, which should trigger the discount usage
    joe_doe.order.calculate_total_price()

    # Check that the discount's nb_usage has decreased after the order
    assert discount.nb_usage == initial_usage - 1


def test_discount_free_shipping(store):
    joe_doe = store.select_customer(username="john_doe")
    books_selected = [
        ("The Hitchhiker's Guide to the Galaxy", 5),
    ]
    books = [(store.select_book(title=title), quantity) for title, quantity in books_selected]
    joe_doe.place_order(books)

    # Calculate total price, which should include the discount for free shipping
    total_price = joe_doe.order.calculate_total_price()

    # Check that the shipping cost is $0
    assert total_price == round(5*12.99,2)  # Total price without shipping