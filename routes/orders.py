import random
import string
from flask import Blueprint, request, jsonify, render_template
from models import db, Restaurant, Product, Order, OrderItem

orders_bp = Blueprint("orders", __name__)


def generate_order_number():
    suffix = "".join(random.choices(string.digits, k=4))
    return f"ORD-{suffix}"


@orders_bp.route("/order/place", methods=["POST"])
def place_order():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    restaurant = Restaurant.query.first()
    if not restaurant.is_open:
        return jsonify({"error": "المطعم مغلق حالياً"}), 400

    car_plate = (data.get("car_plate") or "").strip()
    car_color = (data.get("car_color") or "").strip()
    if not car_plate or not car_color:
        return jsonify({"error": "رقم اللوحة ولون السيارة مطلوبان"}), 400

    cart_items = data.get("items", [])
    if not cart_items:
        return jsonify({"error": "السلة فارغة"}), 400

    # Generate unique order number
    order_number = generate_order_number()
    while Order.query.filter_by(order_number=order_number).first():
        order_number = generate_order_number()

    total = 0
    order_items = []
    for item in cart_items:
        prod = Product.query.get(item.get("id"))
        if not prod or not prod.is_available:
            continue
        qty = max(1, int(item.get("qty", 1)))
        unit_price = float(prod.price)
        total += unit_price * qty
        order_items.append(OrderItem(
            product_id=prod.id,
            quantity=qty,
            unit_price=unit_price,
            product_name_ar=prod.name_ar,
            product_name_en=prod.name_en,
        ))

    if not order_items:
        return jsonify({"error": "لا توجد منتجات متاحة في السلة"}), 400

    order = Order(
        order_number=order_number,
        car_plate=car_plate,
        car_color=car_color,
        car_model=(data.get("car_model") or "").strip() or None,
        parking_spot=(data.get("parking_spot") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
        status="pending",
        total_amount=round(total, 3),
        restaurant_id=restaurant.id,
    )
    db.session.add(order)
    db.session.flush()
    for oi in order_items:
        oi.order_id = order.id
        db.session.add(oi)
    db.session.commit()

    return jsonify({"success": True, "order_number": order_number})


@orders_bp.route("/order/confirm/<order_number>")
def confirm(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    restaurant = Restaurant.query.first()
    return render_template("customer/confirm.html",
                           order=order,
                           restaurant=restaurant)
