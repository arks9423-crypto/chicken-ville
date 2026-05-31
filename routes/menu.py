from flask import Blueprint, render_template
from models import Restaurant, Category, Product, Order

menu_bp = Blueprint('menu', __name__)


@menu_bp.route('/r/<slug>/')
def menu_page(slug):
    restaurant = Restaurant.query.filter_by(slug=slug, status='active').first_or_404()
    categories = Category.query.filter_by(
        restaurant_id=restaurant.id, is_active=True
    ).order_by(Category.sort_order).all()
    products = Product.query.filter_by(
        restaurant_id=restaurant.id, is_available=True
    ).order_by(Product.category_id, Product.sales_count.desc()).all()
    return render_template('customer/menu.html',
                           restaurant=restaurant,
                           categories=categories,
                           products=products)


@menu_bp.route('/r/<slug>/order/<order_number>')
def order_placed(slug, order_number):
    restaurant = Restaurant.query.filter_by(slug=slug, status='active').first_or_404()
    order = Order.query.filter_by(order_number=order_number, restaurant_id=restaurant.id).first_or_404()
    return render_template('customer/order_placed.html', restaurant=restaurant, order=order)
