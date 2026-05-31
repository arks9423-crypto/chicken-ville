from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, make_response
from flask_login import login_required, current_user
from models import Restaurant, Category, Product, Order, OrderItem, User, Coupon, db
from functools import wraps
from datetime import datetime, date, timedelta
import qrcode
from io import BytesIO
import json

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')


def restaurant_required(roles=None):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if current_user.role == 'superadmin':
                abort(403)
            if not current_user.restaurant:
                abort(403)
            if current_user.restaurant.status != 'active':
                flash('حسابك في انتظار الموافقة', 'warning')
                return redirect(url_for('auth.login'))
            if roles and current_user.role not in roles:
                flash('ليس لديك صلاحية الوصول لهذه الصفحة', 'error')
                return redirect(url_for('restaurant.dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


@restaurant_bp.route('/dashboard')
@restaurant_required()
def dashboard():
    rid = current_user.restaurant_id
    today = date.today()

    today_orders = Order.query.filter(
        Order.restaurant_id == rid,
        db.func.date(Order.created_at) == today
    ).all()

    today_revenue = sum(float(o.total_amount) for o in today_orders if o.status not in ('cancelled',))
    today_count = len([o for o in today_orders if o.status not in ('cancelled',)])

    month_start = today.replace(day=1)
    month_count = Order.query.filter(
        Order.restaurant_id == rid,
        Order.created_at >= month_start,
        Order.status != 'cancelled'
    ).count()

    new_orders = Order.query.filter_by(restaurant_id=rid, status='new').order_by(Order.created_at.asc()).all()
    preparing_orders = Order.query.filter_by(restaurant_id=rid, status='preparing').order_by(Order.created_at.asc()).all()
    ready_orders = Order.query.filter_by(restaurant_id=rid, status='ready').order_by(Order.created_at.asc()).all()

    done_orders = Order.query.filter(
        Order.restaurant_id == rid,
        Order.status.in_(['delivered', 'cancelled'])
    ).order_by(Order.updated_at.desc()).limit(30).all()

    return render_template('restaurant/dashboard.html',
                           new_orders=new_orders,
                           preparing_orders=preparing_orders,
                           ready_orders=ready_orders,
                           done_orders=done_orders,
                           today_revenue=today_revenue,
                           today_count=today_count,
                           month_count=month_count)


@restaurant_bp.route('/orders/<int:oid>/status', methods=['POST'])
@restaurant_required()
def update_order_status(oid):
    rid = current_user.restaurant_id
    order = Order.query.filter_by(id=oid, restaurant_id=rid).first_or_404()
    new_status = request.form.get('status')
    valid_statuses = ['new', 'preparing', 'ready', 'delivered', 'cancelled']
    if new_status in valid_statuses:
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('restaurant.dashboard'))


# ─── Products ───────────────────────────────────────────────────────────────

@restaurant_bp.route('/products')
@restaurant_required(roles=['owner', 'manager'])
def products():
    rid = current_user.restaurant_id
    categories = Category.query.filter_by(restaurant_id=rid).order_by(Category.sort_order).all()
    products_all = Product.query.filter_by(restaurant_id=rid).order_by(Product.category_id, Product.id).all()
    return render_template('restaurant/products.html', categories=categories, products=products_all)


@restaurant_bp.route('/products/add', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def add_product():
    rid = current_user.restaurant_id
    name_ar = request.form.get('name_ar', '').strip()
    name_en = request.form.get('name_en', '').strip()

    if not name_ar or not name_en:
        flash('اسم المنتج مطلوب', 'error')
        return redirect(url_for('restaurant.products'))

    cat_id = request.form.get('category_id')
    category = Category.query.filter_by(id=cat_id, restaurant_id=rid).first()
    if not category:
        flash('القسم غير صحيح', 'error')
        return redirect(url_for('restaurant.products'))

    try:
        price_val = round(float(request.form.get('price', '0')), 3)
    except ValueError:
        flash('السعر غير صحيح', 'error')
        return redirect(url_for('restaurant.products'))

    image_b64 = request.form.get('image_base64', '').strip() or None

    product = Product(
        restaurant_id=rid,
        category_id=category.id,
        name_ar=name_ar,
        name_en=request.form.get('name_en', '').strip(),
        description_ar=request.form.get('description_ar', '').strip() or None,
        description_en=request.form.get('description_en', '').strip() or None,
        price=price_val,
        image_base64=image_b64,
        is_featured=request.form.get('is_featured') == 'on'
    )
    db.session.add(product)
    db.session.commit()
    flash('تم إضافة المنتج بنجاح', 'success')
    return redirect(url_for('restaurant.products'))


@restaurant_bp.route('/products/<int:pid>/edit', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def edit_product(pid):
    rid = current_user.restaurant_id
    product = Product.query.filter_by(id=pid, restaurant_id=rid).first_or_404()

    product.name_ar = request.form.get('name_ar', '').strip() or product.name_ar
    product.name_en = request.form.get('name_en', '').strip() or product.name_en
    product.description_ar = request.form.get('description_ar', '').strip() or None
    product.description_en = request.form.get('description_en', '').strip() or None
    product.is_featured = request.form.get('is_featured') == 'on'
    product.is_available = request.form.get('is_available') == 'on'

    new_image = request.form.get('image_base64', '').strip()
    if new_image:
        product.image_base64 = new_image

    try:
        product.price = round(float(request.form.get('price', product.price)), 3)
    except (ValueError, TypeError):
        pass

    cat_id = request.form.get('category_id')
    if cat_id:
        cat = Category.query.filter_by(id=cat_id, restaurant_id=rid).first()
        if cat:
            product.category_id = cat.id

    db.session.commit()
    flash('تم تحديث المنتج', 'success')
    return redirect(url_for('restaurant.products'))


@restaurant_bp.route('/products/<int:pid>/delete', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def delete_product(pid):
    rid = current_user.restaurant_id
    product = Product.query.filter_by(id=pid, restaurant_id=rid).first_or_404()
    db.session.delete(product)
    db.session.commit()
    flash('تم حذف المنتج', 'success')
    return redirect(url_for('restaurant.products'))


@restaurant_bp.route('/products/<int:pid>/toggle', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def toggle_product(pid):
    rid = current_user.restaurant_id
    product = Product.query.filter_by(id=pid, restaurant_id=rid).first_or_404()
    product.is_available = not product.is_available
    db.session.commit()
    return redirect(url_for('restaurant.products'))


# ─── Categories ──────────────────────────────────────────────────────────────

@restaurant_bp.route('/categories')
@restaurant_required(roles=['owner', 'manager'])
def categories():
    rid = current_user.restaurant_id
    cats = Category.query.filter_by(restaurant_id=rid).order_by(Category.sort_order).all()
    return render_template('restaurant/categories.html', categories=cats)


@restaurant_bp.route('/categories/add', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def add_category():
    rid = current_user.restaurant_id
    name_ar = request.form.get('name_ar', '').strip()
    name_en = request.form.get('name_en', '').strip()
    if not name_ar or not name_en:
        flash('اسم القسم مطلوب', 'error')
        return redirect(url_for('restaurant.categories'))
    max_order = db.session.query(db.func.max(Category.sort_order)).filter_by(restaurant_id=rid).scalar() or 0
    cat = Category(restaurant_id=rid, name_ar=name_ar, name_en=name_en, sort_order=max_order + 1)
    db.session.add(cat)
    db.session.commit()
    flash('تم إضافة القسم', 'success')
    return redirect(url_for('restaurant.categories'))


@restaurant_bp.route('/categories/<int:cid>/edit', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def edit_category(cid):
    rid = current_user.restaurant_id
    cat = Category.query.filter_by(id=cid, restaurant_id=rid).first_or_404()
    cat.name_ar = request.form.get('name_ar', '').strip() or cat.name_ar
    cat.name_en = request.form.get('name_en', '').strip() or cat.name_en
    cat.is_active = request.form.get('is_active') == 'on'
    db.session.commit()
    flash('تم تحديث القسم', 'success')
    return redirect(url_for('restaurant.categories'))


@restaurant_bp.route('/categories/<int:cid>/delete', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def delete_category(cid):
    rid = current_user.restaurant_id
    cat = Category.query.filter_by(id=cid, restaurant_id=rid).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    flash('تم حذف القسم', 'success')
    return redirect(url_for('restaurant.categories'))


# ─── Reports ─────────────────────────────────────────────────────────────────

@restaurant_bp.route('/reports')
@restaurant_required(roles=['owner', 'manager'])
def reports():
    rid = current_user.restaurant_id
    period = request.args.get('period', 'today')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    today = date.today()

    if period == 'week':
        date_from = today - timedelta(days=6)
        date_to = today
    elif period == 'month':
        date_from = today.replace(day=1)
        date_to = today
    elif period == 'custom' and date_from_str and date_to_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = today
            date_to = today
    else:
        date_from = today
        date_to = today

    orders = Order.query.filter(
        Order.restaurant_id == rid,
        db.func.date(Order.created_at) >= date_from,
        db.func.date(Order.created_at) <= date_to,
        Order.status != 'cancelled'
    ).order_by(Order.created_at.desc()).all()

    total_revenue = sum(float(o.total_amount) for o in orders)
    avg_order = total_revenue / len(orders) if orders else 0

    from sqlalchemy import func
    top_products = db.session.query(
        OrderItem.product_name_ar,
        func.sum(OrderItem.quantity).label('total_qty')
    ).join(Order).filter(
        Order.restaurant_id == rid,
        db.func.date(Order.created_at) >= date_from,
        db.func.date(Order.created_at) <= date_to,
        Order.status != 'cancelled'
    ).group_by(OrderItem.product_name_ar).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    return render_template('restaurant/reports.html',
                           orders=orders,
                           total_revenue=total_revenue,
                           avg_order=avg_order,
                           top_products=top_products,
                           period=period,
                           date_from=date_from,
                           date_to=date_to)


# ─── Settings ────────────────────────────────────────────────────────────────

@restaurant_bp.route('/settings', methods=['GET', 'POST'])
@restaurant_required(roles=['owner'])
def settings():
    restaurant = current_user.restaurant

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'info':
            restaurant.name_ar = request.form.get('name_ar', '').strip() or restaurant.name_ar
            restaurant.name_en = request.form.get('name_en', '').strip() or restaurant.name_en
            restaurant.phone = request.form.get('phone', '').strip() or None
            restaurant.email = request.form.get('email', '').strip() or None
            restaurant.order_mode = request.form.get('order_mode', 'car')
            restaurant.is_open = request.form.get('is_open') == 'on'
            logo = request.form.get('logo_base64', '').strip()
            if logo:
                restaurant.logo_base64 = logo
            db.session.commit()
            flash('تم حفظ إعدادات المطعم', 'success')

        elif action == 'theme':
            restaurant.theme = request.form.get('theme', 'amber')
            restaurant.primary_color = request.form.get('primary_color', '#F59E0B')
            restaurant.secondary_color = request.form.get('secondary_color', '#D97706')
            db.session.commit()
            flash('تم حفظ الثيم', 'success')

        elif action == 'password':
            current_pwd = request.form.get('current_password', '')
            new_pwd = request.form.get('new_password', '')
            if not current_user.check_password(current_pwd):
                flash('كلمة المرور الحالية غير صحيحة', 'error')
            elif len(new_pwd) < 6:
                flash('كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل', 'error')
            else:
                current_user.set_password(new_pwd)
                db.session.commit()
                flash('تم تغيير كلمة المرور', 'success')

        elif action == 'toggle_open':
            restaurant.is_open = not restaurant.is_open
            db.session.commit()

        return redirect(url_for('restaurant.settings'))

    return render_template('restaurant/settings.html', restaurant=restaurant)


# ─── QR Code ─────────────────────────────────────────────────────────────────

@restaurant_bp.route('/qrcode')
@restaurant_required(roles=['owner'])
def qrcode_page():
    restaurant = current_user.restaurant
    base_url = request.host_url.rstrip('/')
    menu_url = f'{base_url}/r/{restaurant.slug}/'

    qr = qrcode.QRCode(version=1, box_size=10, border=4,
                        error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(menu_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=restaurant.primary_color, back_color='white')
    buf = BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = 'data:image/png;base64,' + __import__('base64').b64encode(buf.getvalue()).decode()

    return render_template('restaurant/qrcode.html', restaurant=restaurant, qr_image_b64=qr_b64)


@restaurant_bp.route('/qrcode/download')
@restaurant_required(roles=['owner'])
def download_qrcode():
    restaurant = current_user.restaurant
    base_url = request.host_url.rstrip('/')
    menu_url = f'{base_url}/r/{restaurant.slug}/'

    qr = qrcode.QRCode(version=1, box_size=10, border=4,
                        error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(menu_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=restaurant.primary_color, back_color='white')

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    response = make_response(buf.read())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'attachment; filename=qr-{restaurant.slug}.png'
    return response


# ─── Staff ───────────────────────────────────────────────────────────────────

@restaurant_bp.route('/staff')
@restaurant_required(roles=['owner'])
def staff():
    rid = current_user.restaurant_id
    staff_members = User.query.filter_by(restaurant_id=rid).order_by(User.created_at).all()
    return render_template('restaurant/staff.html', staff_members=staff_members)


@restaurant_bp.route('/staff/add', methods=['POST'])
@restaurant_required(roles=['owner'])
def add_staff():
    rid = current_user.restaurant_id
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'cashier')

    if role not in ('manager', 'cashier', 'kitchen'):
        flash('دور غير صحيح', 'error')
        return redirect(url_for('restaurant.staff'))
    if not username:
        flash('اسم المستخدم مطلوب', 'error')
        return redirect(url_for('restaurant.staff'))
    if User.query.filter_by(username=username).first():
        flash('اسم المستخدم مستخدم بالفعل', 'error')
        return redirect(url_for('restaurant.staff'))
    if len(password) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
        return redirect(url_for('restaurant.staff'))

    user = User(username=username, role=role, restaurant_id=rid)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('تم إضافة الموظف', 'success')
    return redirect(url_for('restaurant.staff'))


@restaurant_bp.route('/staff/<int:uid>/toggle', methods=['POST'])
@restaurant_required(roles=['owner'])
def toggle_staff(uid):
    rid = current_user.restaurant_id
    user = User.query.filter_by(id=uid, restaurant_id=rid).first_or_404()
    if user.role == 'owner':
        flash('لا يمكن تعطيل المالك', 'error')
        return redirect(url_for('restaurant.staff'))
    user.is_active = not user.is_active
    db.session.commit()
    flash('تم تحديث حالة الموظف', 'success')
    return redirect(url_for('restaurant.staff'))


@restaurant_bp.route('/staff/<int:uid>/delete', methods=['POST'])
@restaurant_required(roles=['owner'])
def delete_staff(uid):
    rid = current_user.restaurant_id
    user = User.query.filter_by(id=uid, restaurant_id=rid).first_or_404()
    if user.role == 'owner':
        flash('لا يمكن حذف المالك', 'error')
        return redirect(url_for('restaurant.staff'))
    db.session.delete(user)
    db.session.commit()
    flash('تم حذف الموظف', 'success')
    return redirect(url_for('restaurant.staff'))


# ─── Coupons ─────────────────────────────────────────────────────────────────

@restaurant_bp.route('/coupons')
@restaurant_required(roles=['owner', 'manager'])
def coupons():
    rid = current_user.restaurant_id
    coupons_list = Coupon.query.filter_by(restaurant_id=rid).order_by(Coupon.id.desc()).all()
    return render_template('restaurant/coupons.html', coupons=coupons_list)


@restaurant_bp.route('/coupons/add', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def add_coupon():
    rid = current_user.restaurant_id
    code = request.form.get('code', '').strip().upper()
    discount_type = request.form.get('discount_type', 'percentage')
    expires_at_str = request.form.get('expires_at', '')

    if not code:
        flash('كود الكوبون مطلوب', 'error')
        return redirect(url_for('restaurant.coupons'))
    if Coupon.query.filter_by(restaurant_id=rid, code=code).first():
        flash('هذا الكود موجود بالفعل', 'error')
        return redirect(url_for('restaurant.coupons'))

    try:
        discount_value = float(request.form.get('discount_value', '0'))
        min_order = float(request.form.get('min_order', '0'))
    except ValueError:
        flash('قيم غير صحيحة', 'error')
        return redirect(url_for('restaurant.coupons'))

    max_uses_str = request.form.get('max_uses', '').strip()
    max_uses = int(max_uses_str) if max_uses_str.isdigit() else None

    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d')
        except ValueError:
            pass

    coupon = Coupon(
        restaurant_id=rid,
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        min_order=min_order,
        max_uses=max_uses,
        expires_at=expires_at
    )
    db.session.add(coupon)
    db.session.commit()
    flash('تم إضافة الكوبون', 'success')
    return redirect(url_for('restaurant.coupons'))


@restaurant_bp.route('/coupons/<int:cid>/toggle', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def toggle_coupon(cid):
    rid = current_user.restaurant_id
    coupon = Coupon.query.filter_by(id=cid, restaurant_id=rid).first_or_404()
    coupon.is_active = not coupon.is_active
    db.session.commit()
    flash('تم تحديث الكوبون', 'success')
    return redirect(url_for('restaurant.coupons'))


@restaurant_bp.route('/coupons/<int:cid>/delete', methods=['POST'])
@restaurant_required(roles=['owner', 'manager'])
def delete_coupon(cid):
    rid = current_user.restaurant_id
    coupon = Coupon.query.filter_by(id=cid, restaurant_id=rid).first_or_404()
    db.session.delete(coupon)
    db.session.commit()
    flash('تم حذف الكوبون', 'success')
    return redirect(url_for('restaurant.coupons'))


# ─── Kitchen ─────────────────────────────────────────────────────────────────

@restaurant_bp.route('/kitchen')
@restaurant_required()
def kitchen():
    rid = current_user.restaurant_id
    new_orders = Order.query.filter_by(restaurant_id=rid, status='new').order_by(Order.created_at.asc()).all()
    preparing_orders = Order.query.filter_by(restaurant_id=rid, status='preparing').order_by(Order.created_at.asc()).all()
    return render_template('restaurant/kitchen.html',
                           new_orders=new_orders,
                           preparing_orders=preparing_orders)
