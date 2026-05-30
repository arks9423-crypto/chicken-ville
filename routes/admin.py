import os
import io
import base64
from functools import wraps
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, current_app, send_file, jsonify)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import qrcode
from qrcode.image.pil import PilImage
from models import db, Restaurant, Category, Product, Order

admin_bp = Blueprint("admin", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_upload(file, subfolder):
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    return filename


# ─── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route("/admin")
@login_required
def index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/dashboard")
@login_required
def dashboard():
    restaurant = Restaurant.query.first()
    orders = Order.query.filter(Order.status != "delivered") \
        .order_by(Order.created_at.desc()).all()
    delivered = Order.query.filter_by(status="delivered") \
        .order_by(Order.created_at.desc()).limit(20).all()
    return render_template("admin/dashboard.html",
                           restaurant=restaurant,
                           orders=orders,
                           delivered=delivered)


@admin_bp.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    valid = ["pending", "preparing", "ready", "delivered"]
    if new_status in valid:
        order.status = new_status
        db.session.commit()
    return redirect(url_for("admin.dashboard"))


# ─── Categories ───────────────────────────────────────────────────────────────

@admin_bp.route("/admin/categories")
@login_required
def categories():
    restaurant = Restaurant.query.first()
    cats = Category.query.filter_by(restaurant_id=restaurant.id) \
        .order_by(Category.sort_order).all()
    return render_template("admin/categories.html", restaurant=restaurant, categories=cats)


@admin_bp.route("/admin/categories/add", methods=["POST"])
@login_required
def add_category():
    restaurant = Restaurant.query.first()
    name_ar = request.form.get("name_ar", "").strip()
    name_en = request.form.get("name_en", "").strip()
    sort_order = int(request.form.get("sort_order", 0))
    if name_ar and name_en:
        cat = Category(name_ar=name_ar, name_en=name_en,
                       sort_order=sort_order, restaurant_id=restaurant.id)
        db.session.add(cat)
        db.session.commit()
        flash("تم إضافة القسم بنجاح", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/admin/categories/<int:cat_id>/edit", methods=["POST"])
@login_required
def edit_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    cat.name_ar = request.form.get("name_ar", cat.name_ar).strip()
    cat.name_en = request.form.get("name_en", cat.name_en).strip()
    cat.sort_order = int(request.form.get("sort_order", cat.sort_order))
    db.session.commit()
    flash("تم تعديل القسم", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash("تم حذف القسم", "success")
    return redirect(url_for("admin.categories"))


# ─── Products ─────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/products")
@login_required
def products():
    restaurant = Restaurant.query.first()
    cats = Category.query.filter_by(restaurant_id=restaurant.id) \
        .order_by(Category.sort_order).all()
    prods = Product.query.filter_by(restaurant_id=restaurant.id) \
        .order_by(Product.category_id, Product.id).all()
    return render_template("admin/products.html",
                           restaurant=restaurant, categories=cats, products=prods)


@admin_bp.route("/admin/products/add", methods=["POST"])
@login_required
def add_product():
    restaurant = Restaurant.query.first()
    image_filename = None
    if "image" in request.files and request.files["image"].filename:
        f = request.files["image"]
        if allowed_file(f.filename):
            image_filename = save_upload(f, "products")

    prod = Product(
        name_ar=request.form.get("name_ar", "").strip(),
        name_en=request.form.get("name_en", "").strip(),
        description_ar=request.form.get("description_ar", "").strip() or None,
        description_en=request.form.get("description_en", "").strip() or None,
        price=float(request.form.get("price", 0)),
        image_filename=image_filename,
        is_available=request.form.get("is_available") == "on",
        category_id=int(request.form.get("category_id")),
        restaurant_id=restaurant.id,
    )
    db.session.add(prod)
    db.session.commit()
    flash("تم إضافة المنتج بنجاح", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/admin/products/<int:prod_id>/edit", methods=["POST"])
@login_required
def edit_product(prod_id):
    prod = Product.query.get_or_404(prod_id)

    if "image" in request.files and request.files["image"].filename:
        f = request.files["image"]
        if allowed_file(f.filename):
            prod.image_filename = save_upload(f, "products")

    prod.name_ar = request.form.get("name_ar", prod.name_ar).strip()
    prod.name_en = request.form.get("name_en", prod.name_en).strip()
    prod.description_ar = request.form.get("description_ar", "").strip() or None
    prod.description_en = request.form.get("description_en", "").strip() or None
    prod.price = float(request.form.get("price", prod.price))
    prod.is_available = request.form.get("is_available") == "on"
    prod.category_id = int(request.form.get("category_id", prod.category_id))
    db.session.commit()
    flash("تم تعديل المنتج", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/admin/products/<int:prod_id>/delete", methods=["POST"])
@login_required
def delete_product(prod_id):
    prod = Product.query.get_or_404(prod_id)
    db.session.delete(prod)
    db.session.commit()
    flash("تم حذف المنتج", "success")
    return redirect(url_for("admin.products"))


# ─── Settings ─────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/settings")
@login_required
def settings():
    restaurant = Restaurant.query.first()
    return render_template("admin/settings.html", restaurant=restaurant)


@admin_bp.route("/admin/settings/save", methods=["POST"])
@login_required
def save_settings():
    restaurant = Restaurant.query.first()

    restaurant.name_ar = request.form.get("name_ar", restaurant.name_ar).strip()
    restaurant.name_en = request.form.get("name_en", restaurant.name_en).strip()
    restaurant.primary_color = request.form.get("primary_color", restaurant.primary_color)
    restaurant.secondary_color = request.form.get("secondary_color", restaurant.secondary_color)
    restaurant.address_ar = request.form.get("address_ar", "").strip() or None
    restaurant.address_en = request.form.get("address_en", "").strip() or None
    restaurant.phone = request.form.get("phone", "").strip() or None
    restaurant.is_open = request.form.get("is_open") == "on"

    new_username = request.form.get("admin_username", "").strip()
    if new_username:
        restaurant.admin_username = new_username

    new_password = request.form.get("new_password", "")
    if new_password:
        restaurant.admin_password_hash = generate_password_hash(new_password)

    if "logo" in request.files and request.files["logo"].filename:
        f = request.files["logo"]
        if allowed_file(f.filename):
            restaurant.logo_filename = save_upload(f, "logos")

    db.session.commit()
    flash("تم حفظ الإعدادات بنجاح", "success")
    return redirect(url_for("admin.settings"))


# ─── QR Code ──────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/qrcode")
@login_required
def qrcode_page():
    restaurant = Restaurant.query.first()
    menu_url = request.host_url.rstrip("/") + url_for("menu.menu_page")

    qr = qrcode.QRCode(version=1, box_size=10, border=4,
                       error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(menu_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=restaurant.secondary_color,
                        back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template("admin/qrcode.html",
                           restaurant=restaurant,
                           menu_url=menu_url,
                           qr_b64=qr_b64)


@admin_bp.route("/admin/qrcode/download")
@login_required
def download_qrcode():
    restaurant = Restaurant.query.first()
    menu_url = request.host_url.rstrip("/") + url_for("menu.menu_page")

    qr = qrcode.QRCode(version=1, box_size=12, border=4,
                       error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(menu_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=restaurant.secondary_color, back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png",
                     as_attachment=True,
                     download_name="qrcode-menu.png")
