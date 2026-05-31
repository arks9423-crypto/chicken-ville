from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import re
import random
import string


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # superadmin|owner|manager|cashier|kitchen
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship('Restaurant', back_populates='users', foreign_keys=[restaurant_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_ar(self):
        labels = {
            'superadmin': 'مدير المنصة',
            'owner': 'مالك',
            'manager': 'مدير',
            'cashier': 'كاشير',
            'kitchen': 'مطبخ'
        }
        return labels.get(self.role, self.role)

    def can(self, *roles):
        return self.role in roles


class Restaurant(db.Model):
    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    logo_base64 = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending|active|inactive
    theme = db.Column(db.String(20), default='amber', nullable=False)  # amber|ocean|rose|slate
    primary_color = db.Column(db.String(7), default='#F59E0B', nullable=False)
    secondary_color = db.Column(db.String(7), default='#D97706', nullable=False)
    is_open = db.Column(db.Boolean, default=True, nullable=False)
    order_mode = db.Column(db.String(10), default='car', nullable=False)  # car|table|both
    plan = db.Column(db.String(20), default='basic', nullable=False)  # basic|pro|premium
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    users = db.relationship('User', back_populates='restaurant', foreign_keys='User.restaurant_id')
    categories = db.relationship('Category', back_populates='restaurant', cascade='all, delete-orphan')
    products = db.relationship('Product', back_populates='restaurant', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='restaurant', cascade='all, delete-orphan')
    coupons = db.relationship('Coupon', back_populates='restaurant', cascade='all, delete-orphan')
    push_subscriptions = db.relationship('PushSubscription', back_populates='restaurant', cascade='all, delete-orphan')

    @property
    def status_ar(self):
        labels = {'pending': 'في الانتظار', 'active': 'نشط', 'inactive': 'معطل'}
        return labels.get(self.status, self.status)

    @property
    def plan_ar(self):
        labels = {'basic': 'الأساسية', 'pro': 'الاحترافية', 'premium': 'المميزة'}
        return labels.get(self.plan, self.plan)

    @staticmethod
    def generate_slug(name_en):
        slug = re.sub(r'[^a-z0-9]+', '-', name_en.lower()).strip('-')
        if not slug:
            slug = 'restaurant'
        base = slug
        counter = 1
        while Restaurant.query.filter_by(slug=slug).first():
            slug = f'{base}-{counter}'
            counter += 1
        return slug


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name_ar = db.Column(db.String(80), nullable=False)
    name_en = db.Column(db.String(80), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    restaurant = db.relationship('Restaurant', back_populates='categories')
    products = db.relationship('Product', back_populates='category', cascade='all, delete-orphan')


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    description_ar = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 3), nullable=False)
    image_base64 = db.Column(db.Text, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sales_count = db.Column(db.Integer, default=0)

    restaurant = db.relationship('Restaurant', back_populates='products')
    category = db.relationship('Category', back_populates='products')
    order_items = db.relationship('OrderItem', back_populates='product')

    @property
    def price_formatted(self):
        return f'{float(self.price):.3f} OMR'


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='new', nullable=False)  # new|preparing|ready|delivered|cancelled
    order_type = db.Column(db.String(20), default='car', nullable=False)  # car|table|cashier
    car_plate = db.Column(db.String(20), nullable=True)
    table_number = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total_amount = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=True)
    rating_comment = db.Column(db.Text, nullable=True)

    restaurant = db.relationship('Restaurant', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    coupon = db.relationship('Coupon', back_populates='orders')
    customer_subscriptions = db.relationship('CustomerSubscription', back_populates='order', cascade='all, delete-orphan')

    @property
    def status_ar(self):
        labels = {
            'new': 'جديد',
            'preparing': 'قيد التحضير',
            'ready': 'جاهز',
            'delivered': 'تم التسليم',
            'cancelled': 'ملغي'
        }
        return labels.get(self.status, self.status)

    @property
    def status_color(self):
        colors = {
            'new': 'badge-new',
            'preparing': 'badge-preparing',
            'ready': 'badge-ready',
            'delivered': 'badge-delivered',
            'cancelled': 'badge-cancelled'
        }
        return colors.get(self.status, '')

    @property
    def identifier(self):
        if self.order_type == 'car':
            return f'سيارة: {self.car_plate}'
        elif self.order_type == 'table':
            return f'طاولة: {self.table_number}'
        return 'كاشير'

    @staticmethod
    def generate_number(restaurant):
        prefix = ''.join([c for c in restaurant.name_en.upper() if c.isalpha()])[:2]
        if len(prefix) < 2:
            prefix = prefix.ljust(2, 'X')
        suffix = ''.join(random.choices(string.digits, k=4))
        num = f'{prefix}-{suffix}'
        while Order.query.filter_by(order_number=num).first():
            suffix = ''.join(random.choices(string.digits, k=4))
            num = f'{prefix}-{suffix}'
        return num

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'status_ar': self.status_ar,
            'order_type': self.order_type,
            'car_plate': self.car_plate,
            'table_number': self.table_number,
            'notes': self.notes,
            'total_amount': float(self.total_amount),
            'discount_amount': float(self.discount_amount),
            'created_at': self.created_at.isoformat(),
            'updated_at': (self.updated_at or self.created_at).isoformat(),
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Numeric(10, 3), nullable=False)
    product_name_ar = db.Column(db.String(100), nullable=False)
    product_name_en = db.Column(db.String(100), nullable=False)

    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', back_populates='order_items')

    @property
    def subtotal(self):
        return float(self.unit_price) * self.quantity

    def to_dict(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': self.subtotal,
            'product_name_ar': self.product_name_ar,
            'product_name_en': self.product_name_en
        }


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage|fixed
    discount_value = db.Column(db.Numeric(10, 3), nullable=False)
    min_order = db.Column(db.Numeric(10, 3), default=0)
    max_uses = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    restaurant = db.relationship('Restaurant', back_populates='coupons')
    orders = db.relationship('Order', back_populates='coupon')

    __table_args__ = (db.UniqueConstraint('restaurant_id', 'code', name='uq_restaurant_coupon'),)

    def is_valid(self, order_total):
        if not self.is_active:
            return False, 'الكوبون غير نشط'
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False, 'الكوبون منتهي الصلاحية'
        if self.max_uses and self.used_count >= self.max_uses:
            return False, 'تم استخدام الكوبون بالحد الأقصى'
        if order_total < float(self.min_order):
            return False, f'الحد الأدنى للطلب {float(self.min_order):.3f} OMR'
        return True, 'صالح'

    def calculate_discount(self, order_total):
        if self.discount_type == 'percentage':
            return round(order_total * float(self.discount_value) / 100, 3)
        return min(float(self.discount_value), order_total)


class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    subscription_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurant = db.relationship('Restaurant', back_populates='push_subscriptions')


class CustomerSubscription(db.Model):
    __tablename__ = 'customer_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    subscription_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', back_populates='customer_subscriptions')
