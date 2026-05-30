from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, Restaurant

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        restaurant = Restaurant.query.first()

        if restaurant and username == restaurant.admin_username and \
                check_password_hash(restaurant.admin_password_hash, password):
            session["admin_logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin.dashboard"))
        else:
            flash("اسم المستخدم أو كلمة المرور غير صحيحة", "error")

    return render_template("admin/login.html")


@auth_bp.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
