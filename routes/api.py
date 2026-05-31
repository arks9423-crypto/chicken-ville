from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from models import Restaurant, Product, Order, OrderItem, Coupon, PushSubscription, CustomerSubscription, db
from datetime import datetime
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/orders/place', methods=['POST'])
def place_order():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'بيانات غير صحيحة'}), 400

    slug = data.get('slug', '')
    restaurant = Restaurant.query.filter_by(slug=slug, status='active').first()
    if not restaurant:
        return jsonify({'error': 'المطعم غير موجود'}), 404
    if not restaurant.is_open:
        return jsonify({'error': 'المطعم مغلق حالياً'}), 400

    items_data = data.get('items', [])
    if not items_data:
        return jsonify({'error': 'السلة فارغة'}), 400

    order_type = data.get('order_type', 'car')
    car_plate = data.get('car_plate', '').strip()
    table_number = data.get('table_number', '').strip()
    notes = data.get('notes', '').strip()
    coupon_code = data.get('coupon_code', '').strip().upper()

    if order_type == 'car' and not car_plate:
        return jsonify({'error': 'رقم السيارة مطلوب'}), 400
    if order_type == 'table' and not table_number:
        return jsonify({'error': 'رقم الطاولة مطلوب'}), 400

    # Build items
    order_items = []
    subtotal = 0.0
    for item_data in items_data:
        product = Product.query.filter_by(
            id=item_data.get('id'), restaurant_id=restaurant.id, is_available=True
        ).first()
        if not product:
            continue
        qty = max(1, int(item_data.get('qty', 1)))
        order_items.append((product, qty))
        subtotal += float(product.price) * qty

    if not order_items:
        return jsonify({'error': 'لا توجد منتجات صالحة'}), 400

    # Coupon
    discount = 0.0
    coupon = None
    if coupon_code:
        coupon = Coupon.query.filter_by(restaurant_id=restaurant.id, code=coupon_code).first()
        if coupon:
            valid, msg = coupon.is_valid(subtotal)
            if valid:
                discount = coupon.calculate_discount(subtotal)
            else:
                return jsonify({'error': msg}), 400

    total = max(0.0, subtotal - discount)

    order = Order(
        restaurant_id=restaurant.id,
        order_number=Order.generate_number(restaurant),
        status='new',
        order_type=order_type,
        car_plate=car_plate if order_type == 'car' else None,
        table_number=table_number if order_type == 'table' else None,
        notes=notes or None,
        total_amount=round(total, 3),
        discount_amount=round(discount, 3),
        coupon_id=coupon.id if coupon else None
    )
    db.session.add(order)
    db.session.flush()

    for product, qty in order_items:
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=product.price,
            product_name_ar=product.name_ar,
            product_name_en=product.name_en
        )
        db.session.add(item)
        product.sales_count += qty

    if coupon:
        coupon.used_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'redirect': f'/r/{slug}/order/{order.order_number}'
    })


@api_bp.route('/orders/poll')
@login_required
def poll_orders():
    if current_user.role == 'superadmin':
        return jsonify({'error': 'forbidden'}), 403

    rid = current_user.restaurant_id
    since_str = request.args.get('since', '')

    orders = Order.query.filter(
        Order.restaurant_id == rid,
        Order.status.in_(['new', 'preparing', 'ready'])
    ).order_by(Order.created_at.asc()).all()

    has_new = False
    if since_str:
        try:
            since = datetime.fromisoformat(since_str.rstrip('Z'))
            has_new = any(o.created_at > since for o in orders if o.status == 'new')
        except (ValueError, TypeError):
            pass

    return jsonify({
        'orders': [o.to_dict() for o in orders],
        'has_new': has_new,
        'server_time': datetime.utcnow().isoformat()
    })


@api_bp.route('/orders/<int:oid>/status', methods=['POST'])
@login_required
def update_status(oid):
    if current_user.role == 'superadmin':
        return jsonify({'error': 'forbidden'}), 403

    rid = current_user.restaurant_id
    order = Order.query.filter_by(id=oid, restaurant_id=rid).first_or_404()

    data = request.get_json() or {}
    new_status = data.get('status')
    valid = ('new', 'preparing', 'ready', 'delivered', 'cancelled')
    if new_status not in valid:
        return jsonify({'error': 'حالة غير صحيحة'}), 400

    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()

    if new_status == 'ready':
        _notify_customer(order)

    return jsonify({'success': True, 'order': order.to_dict()})


@api_bp.route('/orders/<order_number>/status')
def order_status(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return jsonify({
        'status': order.status,
        'status_ar': order.status_ar,
        'updated_at': (order.updated_at or order.created_at).isoformat()
    })


@api_bp.route('/orders/<order_number>/rate', methods=['POST'])
def rate_order(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    data = request.get_json() or {}
    rating = data.get('rating')
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'تقييم غير صحيح'}), 400
    order.rating = rating
    order.rating_comment = data.get('comment', '')
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/coupons/validate', methods=['POST'])
def validate_coupon():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    slug = data.get('slug', '')
    order_total = float(data.get('total', 0))

    restaurant = Restaurant.query.filter_by(slug=slug).first()
    if not restaurant:
        return jsonify({'valid': False, 'message': 'المطعم غير موجود'})

    coupon = Coupon.query.filter_by(restaurant_id=restaurant.id, code=code).first()
    if not coupon:
        return jsonify({'valid': False, 'message': 'الكوبون غير موجود'})

    valid, msg = coupon.is_valid(order_total)
    if not valid:
        return jsonify({'valid': False, 'message': msg})

    discount = coupon.calculate_discount(order_total)
    label = f'{float(coupon.discount_value):.0f}{"%" if coupon.discount_type == "percentage" else " OMR"}'
    return jsonify({
        'valid': True,
        'discount': round(discount, 3),
        'new_total': round(max(0.0, order_total - discount), 3),
        'message': f'خصم {label}'
    })


@api_bp.route('/push/subscribe/restaurant', methods=['POST'])
@login_required
def subscribe_restaurant_push():
    if current_user.role == 'superadmin':
        return jsonify({'error': 'forbidden'}), 403
    rid = current_user.restaurant_id
    data = request.get_json() or {}
    sub = PushSubscription(
        restaurant_id=rid,
        subscription_json=json.dumps(data.get('subscription', {}))
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/push/subscribe/customer', methods=['POST'])
def subscribe_customer_push():
    data = request.get_json() or {}
    order_number = data.get('order_number', '')
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return jsonify({'error': 'الطلب غير موجود'}), 404
    sub = CustomerSubscription(
        order_id=order.id,
        subscription_json=json.dumps(data.get('subscription', {}))
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({'success': True})


def _notify_customer(order):
    try:
        from flask import current_app
        vapid_private = current_app.config.get('VAPID_PRIVATE_KEY', '')
        vapid_email = current_app.config.get('VAPID_CLAIMS_EMAIL', 'admin@qrmenu.om')
        if not vapid_private:
            return
        from pywebpush import webpush
        subs = CustomerSubscription.query.filter_by(order_id=order.id).all()
        for sub in subs:
            try:
                subscription_info = json.loads(sub.subscription_json)
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps({
                        'title': 'طلبك جاهز! 🎉',
                        'body': f'طلب رقم {order.order_number} جاهز للاستلام',
                        'url': f'/r/{order.restaurant.slug}/order/{order.order_number}'
                    }),
                    vapid_private_key=vapid_private,
                    vapid_claims={'sub': f'mailto:{vapid_email}'}
                )
            except Exception:
                pass
    except Exception:
        pass
