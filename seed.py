"""
Run once to create the database with demo data.
Usage: python seed.py
Default login: admin / admin123
"""
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, Restaurant, Category, Product

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    restaurant = Restaurant(
        name_ar="مطعم النجمة",
        name_en="Al Najma Restaurant",
        primary_color="#E85D04",
        secondary_color="#1A1A2E",
        admin_username="admin",
        admin_password_hash=generate_password_hash("admin123"),
        address_ar="شارع الملك فهد، الرياض",
        address_en="King Fahd Road, Riyadh",
        phone="+966 50 000 0000",
        is_open=True,
    )
    db.session.add(restaurant)
    db.session.flush()

    # Categories
    starters = Category(name_ar="المقبلات", name_en="Starters",
                        sort_order=1, restaurant_id=restaurant.id)
    mains = Category(name_ar="الأطباق الرئيسية", name_en="Main Dishes",
                     sort_order=2, restaurant_id=restaurant.id)
    drinks = Category(name_ar="المشروبات", name_en="Drinks",
                      sort_order=3, restaurant_id=restaurant.id)

    db.session.add_all([starters, mains, drinks])
    db.session.flush()

    # Products
    products = [
        Product(name_ar="سلطة فتوش", name_en="Fattoush Salad",
                description_ar="سلطة طازجة مع خبز مقلي وعصير الرمان",
                description_en="Fresh salad with fried bread and pomegranate",
                price=1.500, category_id=starters.id, restaurant_id=restaurant.id),
        Product(name_ar="حمص بالطحينة", name_en="Hummus",
                description_ar="حمص ناعم مع زيت الزيتون والبابريكا",
                description_en="Smooth hummus with olive oil and paprika",
                price=1.200, category_id=starters.id, restaurant_id=restaurant.id),
        Product(name_ar="دجاج مشوي", name_en="Grilled Chicken",
                description_ar="دجاج مشوي مع الأعشاب والليمون والأرز البسمتي",
                description_en="Grilled chicken with herbs, lemon and basmati rice",
                price=3.500, category_id=mains.id, restaurant_id=restaurant.id),
        Product(name_ar="برجر لحم", name_en="Beef Burger",
                description_ar="برجر لحم بقري مع جبنة شيدر والخضار",
                description_en="Beef burger with cheddar cheese and vegetables",
                price=2.800, category_id=mains.id, restaurant_id=restaurant.id),
        Product(name_ar="عصير برتقال طازج", name_en="Fresh Orange Juice",
                description_ar="عصير برتقال طبيعي طازج",
                description_en="Freshly squeezed orange juice",
                price=0.800, category_id=drinks.id, restaurant_id=restaurant.id),
        Product(name_ar="مياه غازية", name_en="Soft Drink",
                description_ar="كولا / بيبسي / سبرايت",
                description_en="Cola / Pepsi / Sprite",
                price=0.300, category_id=drinks.id, restaurant_id=restaurant.id),
    ]
    db.session.add_all(products)
    db.session.commit()

    print("=" * 50)
    print("[OK] Database created successfully!")
    print("=" * 50)
    print(f"  Username: admin")
    print(f"  Password: admin123")
    print(f"  Categories: 3  |  Products: {len(products)}")
    print("=" * 50)
    print("Run: python run.py")
    print("Then open: http://localhost:5000")
    print("Admin: http://localhost:5000/admin/login")
    print("=" * 50)
