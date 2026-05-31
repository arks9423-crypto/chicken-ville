from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import Restaurant, User, db
from datetime import datetime
from functools import wraps

platform_bp = Blueprint('platform', __name__, url_prefix='/platform')


def superadmin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'superadmin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


@platform_bp.route('/dashboard')
@superadmin_required
def dashboard():
    status_filter = request.args.get('status', 'all')

    query = Restaurant.query.order_by(Restaurant.created_at.desc())
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    restaurants = query.all()

    stats = {
        'total': Restaurant.query.count(),
        'pending': Restaurant.query.filter_by(status='pending').count(),
        'active': Restaurant.query.filter_by(status='active').count(),
        'inactive': Restaurant.query.filter_by(status='inactive').count(),
    }

    return render_template('platform/dashboard.html',
                           restaurants=restaurants,
                           stats=stats,
                           status_filter=status_filter)


@platform_bp.route('/restaurants/<int:rid>/approve', methods=['POST'])
@superadmin_required
def approve_restaurant(rid):
    restaurant = Restaurant.query.get_or_404(rid)
    restaurant.status = 'active'
    restaurant.approved_at = datetime.utcnow()
    restaurant.approved_by = current_user.id
    db.session.commit()
    flash(f'تم تفعيل مطعم "{restaurant.name_ar}" بنجاح', 'success')
    return redirect(url_for('platform.dashboard'))


@platform_bp.route('/restaurants/<int:rid>/reject', methods=['POST'])
@superadmin_required
def reject_restaurant(rid):
    restaurant = Restaurant.query.get_or_404(rid)
    restaurant.status = 'inactive'
    db.session.commit()
    flash(f'تم رفض طلب مطعم "{restaurant.name_ar}"', 'warning')
    return redirect(url_for('platform.dashboard'))


@platform_bp.route('/restaurants/<int:rid>/disable', methods=['POST'])
@superadmin_required
def disable_restaurant(rid):
    restaurant = Restaurant.query.get_or_404(rid)
    if restaurant.status == 'active':
        restaurant.status = 'inactive'
        msg = f'تم تعطيل مطعم "{restaurant.name_ar}"'
    else:
        restaurant.status = 'active'
        restaurant.approved_at = datetime.utcnow()
        restaurant.approved_by = current_user.id
        msg = f'تم إعادة تفعيل مطعم "{restaurant.name_ar}"'
    db.session.commit()
    flash(msg, 'info')
    return redirect(url_for('platform.dashboard'))
