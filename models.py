from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Restaurant(db.Model):
    __tablename__ = "restaurant"
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False, default="مطعمي")
    name_en = db.Column(db.String(100), nullable=False, default="My Restaurant")
    logo_filename = db.Column(db.String(200), nullable=True)
    primary_color = db.Column(db.String(7), nullable=False, default="#E85D04")
    secondary_color = db.Column(db.String(7), nullable=False, default="#1A1A2E")
    admin_username = db.Column(db.String(50), nullable=False, default="admin")
    admin_password_hash = db.Column(db.String(256), nullable=False)
    address_ar = db.Column(db.String(200), nullable=True)
    address_en = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_open = db.Column(db.Boolean, nullable=False, default=True)

    categories = db.relationship("Category", backref="restaurant", lazy=True, cascade="all, delete-orphan")
    products = db.relationship("Product", backref="restaurant", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="restaurant", lazy=True, cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(80), nullable=False)
    name_en = db.Column(db.String(80), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)

    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    description_ar = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 3), nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)

    order_items = db.relationship("OrderItem", backref="product", lazy=True)


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), nullable=False, unique=True)
    car_plate = db.Column(db.String(20), nullable=False)
    car_color = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(100), nullable=True)
    parking_spot = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    # pending | preparing | ready | delivered
    total_amount = db.Column(db.Numeric(10, 3), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    @property
    def status_ar(self):
        return {
            "pending": "قيد الانتظار",
            "preparing": "قيد التحضير",
            "ready": "جاهز",
            "delivered": "تم التوصيل",
        }.get(self.status, self.status)

    @property
    def status_color(self):
        return {
            "pending": "yellow",
            "preparing": "blue",
            "ready": "green",
            "delivered": "gray",
        }.get(self.status, "gray")


class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 3), nullable=False)
    product_name_ar = db.Column(db.String(100), nullable=False)
    product_name_en = db.Column(db.String(100), nullable=False)
