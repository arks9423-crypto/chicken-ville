from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Restaurant, db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'superadmin':
            return redirect(url_for('platform.dashboard'))
        return redirect(url_for('restaurant.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
            return render_template('login.html')

        if not user.is_active:
            flash('حسابك معطل، تواصل مع الإدارة', 'error')
            return render_template('login.html')

        if user.role != 'superadmin':
            if not user.restaurant:
                flash('لا يوجد مطعم مرتبط بحسابك', 'error')
                return render_template('login.html')
            if user.restaurant.status == 'pending':
                flash('طلب تسجيل مطعمك قيد المراجعة. سيتم التواصل معك عند الموافقة.', 'warning')
                return render_template('login.html')
            if user.restaurant.status == 'inactive':
                flash('حساب مطعمك معطل، تواصل مع إدارة المنصة', 'error')
                return render_template('login.html')

        login_user(user, remember=True)

        if user.role == 'superadmin':
            return redirect(url_for('platform.dashboard'))
        return redirect(url_for('restaurant.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name_ar = request.form.get('name_ar', '').strip()
        name_en = request.form.get('name_en', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        errors = []

        if not name_ar:
            errors.append('اسم المطعم بالعربية مطلوب')
        if not name_en:
            errors.append('اسم المطعم بالإنجليزية مطلوب')
        if not username:
            errors.append('اسم المستخدم مطلوب')
        if len(password) < 6:
            errors.append('كلمة المرور يجب أن تكون 6 أحرف على الأقل')

        if username and User.query.filter_by(username=username).first():
            errors.append('اسم المستخدم مستخدم بالفعل')

        if email and User.query.filter_by(email=email).first():
            errors.append('البريد الإلكتروني مستخدم بالفعل')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html', form_data=request.form)

        slug = Restaurant.generate_slug(name_en)

        restaurant = Restaurant(
            name_ar=name_ar,
            name_en=name_en,
            slug=slug,
            phone=phone or None,
            email=email or None,
            status='pending'
        )
        db.session.add(restaurant)
        db.session.flush()

        user = User(
            username=username,
            email=email if email else None,
            role='owner',
            restaurant_id=restaurant.id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('تم تسجيل طلبك بنجاح! سيتم مراجعته والتواصل معك قريباً.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form_data={})
