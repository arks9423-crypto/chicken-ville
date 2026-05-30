from flask import Blueprint, render_template
from models import Restaurant, Category, Product

menu_bp = Blueprint("menu", __name__)


@menu_bp.route("/menu")
def menu_page():
    restaurant = Restaurant.query.first()
    categories = Category.query.filter_by(restaurant_id=restaurant.id) \
        .order_by(Category.sort_order).all()
    return render_template("customer/menu.html",
                           restaurant=restaurant,
                           categories=categories)
