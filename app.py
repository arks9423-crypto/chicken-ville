import os
from flask import Flask, redirect, url_for
from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "products"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "logos"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.menu import menu_bp
    from routes.orders import orders_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)

    @app.route("/")
    def index():
        return redirect(url_for("menu.menu_page"))

    with app.app_context():
        db.create_all()
        _auto_seed()

    return app


def _auto_seed():
    """Create default restaurant if none exists (first deploy)."""
    from models import Restaurant, Category, Product
    from werkzeug.security import generate_password_hash
    if Restaurant.query.first():
        return

    import os
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")

    r = Restaurant(
        name_ar="تشكن فيل",
        name_en="Chicken Ville",
        primary_color="#FFB800",
        secondary_color="#009B8D",
        admin_username=admin_user,
        admin_password_hash=generate_password_hash(admin_pass),
        address_ar="الخوير | صحار | لوى - سلطنة عمان",
        address_en="Al Khuwayr | Sohar | Liwa - Oman",
        is_open=True,
    )
    db.session.add(r)
    db.session.flush()

    cats = [
        Category(name_ar="سندويشات", name_en="Sandwiches", sort_order=1, restaurant_id=r.id),
        Category(name_ar="وجبات",    name_en="Meals",       sort_order=2, restaurant_id=r.id),
        Category(name_ar="الجانبية", name_en="Sides",       sort_order=3, restaurant_id=r.id),
        Category(name_ar="مشروبات",  name_en="Drinks",      sort_order=4, restaurant_id=r.id),
    ]
    db.session.add_all(cats)
    db.session.flush()
    sw, ml, sd, dr = cats

    prods = [
        Product(name_ar="سندويش دجاج كريسبي", name_en="Crispy Chicken Sandwich",
                description_ar="دجاج مقرمش بالصوص الخاص", description_en="Crispy chicken with special sauce",
                price=1.800, category_id=sw.id, restaurant_id=r.id),
        Product(name_ar="سندويش سبايسي", name_en="Spicy Sandwich",
                description_ar="دجاج حار مقرمش مع صوص الحار", description_en="Spicy crispy chicken",
                price=1.800, category_id=sw.id, restaurant_id=r.id),
        Product(name_ar="وجبة فاميلي", name_en="Family Meal",
                description_ar="6 قطع دجاج + بطاطس + كول سلو + مشروب", description_en="6 pcs + fries + coleslaw + drink",
                price=5.500, category_id=ml.id, restaurant_id=r.id),
        Product(name_ar="وجبة فردية", name_en="Single Meal",
                description_ar="سندويش + بطاطس + مشروب", description_en="Sandwich + fries + drink",
                price=2.500, category_id=ml.id, restaurant_id=r.id),
        Product(name_ar="بطاطس مقلية", name_en="French Fries",
                description_ar="بطاطس ذهبية مقرمشة", description_en="Golden crispy fries",
                price=0.600, category_id=sd.id, restaurant_id=r.id),
        Product(name_ar="اصابع موزاريلا", name_en="Mozzarella Sticks",
                description_ar="4 قطع موزاريلا مقرمشة", description_en="4 crispy mozzarella sticks",
                price=1.200, category_id=sd.id, restaurant_id=r.id),
        Product(name_ar="بيبسي / مشروب غازي", name_en="Pepsi / Soft Drink",
                description_ar="بيبسي، سفن اب، ميراندا", description_en="Pepsi, 7Up, Mirinda",
                price=0.200, category_id=dr.id, restaurant_id=r.id),
        Product(name_ar="عصير طازج", name_en="Fresh Juice",
                description_ar="برتقال / مانجو / رمان", description_en="Orange / Mango / Pomegranate",
                price=0.800, category_id=dr.id, restaurant_id=r.id),
    ]
    db.session.add_all(prods)
    db.session.commit()
