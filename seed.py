"""
QRMenu SaaS — Database Seeder
Usage: python seed.py
"""

from app import create_app
from extensions import db
from models import User, Restaurant, Category, Product, Coupon
from datetime import datetime


def seed():
    app = create_app()
    with app.app_context():
        print('Dropping all tables...')
        db.drop_all()
        print('Creating all tables...')
        db.create_all()

        # ── Super Admin ──────────────────────────────────────
        admin = User(
            username='admin',
            email='admin@qrmenu.om',
            role='superadmin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush()

        # ── Restaurant 1: مطعم الواحة (Active, Amber) ────────
        r1 = Restaurant(
            name_ar='مطعم الواحة',
            name_en='Al Waha Restaurant',
            slug='al-waha',
            phone='+96891234567',
            email='info@alwaha.om',
            status='active',
            theme='amber',
            primary_color='#F59E0B',
            secondary_color='#D97706',
            is_open=True,
            order_mode='car',
            plan='pro',
            approved_at=datetime.utcnow(),
            approved_by=admin.id
        )
        db.session.add(r1)
        db.session.flush()

        owner1 = User(username='waha_owner', email='owner@alwaha.om', role='owner', restaurant_id=r1.id)
        owner1.set_password('waha123')
        db.session.add(owner1)

        kitchen1 = User(username='waha_kitchen', role='kitchen', restaurant_id=r1.id)
        kitchen1.set_password('kitchen123')
        db.session.add(kitchen1)

        cashier1 = User(username='waha_cashier', role='cashier', restaurant_id=r1.id)
        cashier1.set_password('cashier123')
        db.session.add(cashier1)

        # Categories
        cats1 = [
            Category(restaurant_id=r1.id, name_ar='سندويشات', name_en='Sandwiches', sort_order=1),
            Category(restaurant_id=r1.id, name_ar='وجبات', name_en='Meals', sort_order=2),
            Category(restaurant_id=r1.id, name_ar='مشروبات', name_en='Drinks', sort_order=3),
            Category(restaurant_id=r1.id, name_ar='حلويات', name_en='Desserts', sort_order=4),
        ]
        for c in cats1:
            db.session.add(c)
        db.session.flush()

        c_sand, c_meal, c_drink, c_sweet = cats1

        # Products
        products1 = [
            Product(restaurant_id=r1.id, category_id=c_sand.id,
                    name_ar='برجر الواحة المميز', name_en='Al Waha Special Burger',
                    description_ar='برجر لحم طازج مع جبن وخس وطماطم وصوص خاص',
                    description_en='Fresh beef burger with cheese, lettuce, tomatoes and special sauce',
                    price=2.500, is_available=True, is_featured=True),
            Product(restaurant_id=r1.id, category_id=c_sand.id,
                    name_ar='ساندويش دجاج مشوي', name_en='Grilled Chicken Sandwich',
                    description_ar='دجاج مشوي طازج مع صوص الثوم',
                    description_en='Fresh grilled chicken with garlic sauce',
                    price=2.000, is_available=True),
            Product(restaurant_id=r1.id, category_id=c_sand.id,
                    name_ar='شاورما لحم', name_en='Beef Shawarma',
                    description_ar='شاورما لحم مع تحينة وخضار',
                    description_en='Beef shawarma with tahini and vegetables',
                    price=1.800, is_available=True),
            Product(restaurant_id=r1.id, category_id=c_meal.id,
                    name_ar='وجبة دجاج مع أرز', name_en='Chicken Rice Meal',
                    description_ar='نصف دجاجة مشوية مع أرز وسلطة وخبز',
                    description_en='Half grilled chicken with rice, salad and bread',
                    price=3.500, is_available=True, is_featured=True),
            Product(restaurant_id=r1.id, category_id=c_meal.id,
                    name_ar='وجبة كباب مشوي', name_en='Grilled Kebab Meal',
                    description_ar='كباب مشوي مع أرز وخبز وسلطة',
                    description_en='Grilled kebab with rice, bread and salad',
                    price=3.000, is_available=True),
            Product(restaurant_id=r1.id, category_id=c_meal.id,
                    name_ar='بيتزا جبن مشكل', name_en='Mixed Cheese Pizza',
                    description_ar='بيتزا بالجبن الإيطالي والخضار الطازجة',
                    description_en='Pizza with Italian cheese and fresh vegetables',
                    price=2.750, is_available=True),
            Product(restaurant_id=r1.id, category_id=c_drink.id,
                    name_ar='عصير برتقال طازج', name_en='Fresh Orange Juice',
                    description_ar='عصير برتقال طازج 100% بدون إضافات',
                    description_en='100% fresh orange juice with no additives',
                    price=0.800, is_available=True),
            Product(restaurant_id=r1.id, category_id=c_drink.id,
                    name_ar='مياه معدنية باردة', name_en='Cold Mineral Water',
                    description_ar='زجاجة مياه معدنية 500مل',
                    description_en='500ml mineral water bottle',
                    price=0.200, is_available=True),
            Product(restaurant_id=r1.id, category_id=c_sweet.id,
                    name_ar='كنافة بالقشطة', name_en='Kunafa with Cream',
                    description_ar='كنافة عمانية أصيلة بالقشطة والعسل الطبيعي',
                    description_en='Authentic Omani kunafa with cream and natural honey',
                    price=1.500, is_available=True, is_featured=True),
        ]
        for p in products1:
            db.session.add(p)

        # Coupon
        coupon1 = Coupon(
            restaurant_id=r1.id,
            code='WELCOME10',
            discount_type='percentage',
            discount_value=10,
            min_order=5.000,
            is_active=True
        )
        db.session.add(coupon1)

        coupon2 = Coupon(
            restaurant_id=r1.id,
            code='SAVE1',
            discount_type='fixed',
            discount_value=1.000,
            min_order=3.000,
            max_uses=50,
            is_active=True
        )
        db.session.add(coupon2)

        # ── Restaurant 2: كافيه النخيل (Pending, Ocean) ──────
        r2 = Restaurant(
            name_ar='كافيه النخيل',
            name_en='Al Nakheel Cafe',
            slug='al-nakheel',
            phone='+96898765432',
            email='info@alnakheel.om',
            status='pending',
            theme='ocean',
            primary_color='#0EA5E9',
            secondary_color='#0284C7',
            is_open=True,
            order_mode='table',
            plan='basic'
        )
        db.session.add(r2)
        db.session.flush()

        owner2 = User(username='nakheel_owner', email='owner@alnakheel.om', role='owner', restaurant_id=r2.id)
        owner2.set_password('nakheel123')
        db.session.add(owner2)

        cats2 = [
            Category(restaurant_id=r2.id, name_ar='مشروبات ساخنة', name_en='Hot Drinks', sort_order=1),
            Category(restaurant_id=r2.id, name_ar='مشروبات باردة', name_en='Cold Drinks', sort_order=2),
            Category(restaurant_id=r2.id, name_ar='كيك وحلويات', name_en='Cakes & Sweets', sort_order=3),
        ]
        for c in cats2:
            db.session.add(c)
        db.session.flush()

        c_hot, c_cold, c_cake = cats2

        products2 = [
            Product(restaurant_id=r2.id, category_id=c_hot.id,
                    name_ar='قهوة عربية', name_en='Arabic Coffee',
                    description_ar='قهوة عربية أصيلة بالهيل والزعفران',
                    description_en='Authentic Arabic coffee with cardamom and saffron',
                    price=0.500, is_available=True),
            Product(restaurant_id=r2.id, category_id=c_hot.id,
                    name_ar='شاي كرك', name_en='Karak Tea',
                    description_ar='شاي كرك بالحليب والهيل الأصيل',
                    description_en='Karak tea with milk and authentic cardamom',
                    price=0.400, is_available=True, is_featured=True),
            Product(restaurant_id=r2.id, category_id=c_hot.id,
                    name_ar='قهوة كابتشينو', name_en='Cappuccino',
                    description_ar='كابتشينو إيطالي بالحليب المبخر',
                    description_en='Italian cappuccino with steamed milk',
                    price=1.200, is_available=True),
            Product(restaurant_id=r2.id, category_id=c_cold.id,
                    name_ar='موهيتو بالنعناع', name_en='Mint Mojito',
                    description_ar='موهيتو منعش بالنعناع الطازج والليمون',
                    description_en='Refreshing mojito with fresh mint and lemon',
                    price=1.200, is_available=True, is_featured=True),
            Product(restaurant_id=r2.id, category_id=c_cold.id,
                    name_ar='عصير مانجو', name_en='Mango Juice',
                    description_ar='عصير مانجو طازج 100%',
                    description_en='100% fresh mango juice',
                    price=1.000, is_available=True),
            Product(restaurant_id=r2.id, category_id=c_cake.id,
                    name_ar='كيكة الشوكولاتة الفاخرة', name_en='Premium Chocolate Cake',
                    description_ar='كيكة شوكولاتة بلجيكية غنية',
                    description_en='Rich Belgian chocolate cake',
                    price=1.500, is_available=True, is_featured=True),
        ]
        for p in products2:
            db.session.add(p)

        db.session.commit()

        import sys
        out = sys.stdout
        sep = '=' * 60
        lines = [
            sep,
            '  QRMenu SaaS - Database seeded successfully!',
            sep,
            '',
            '  Super Admin:',
            '    URL:      http://localhost:5000/login',
            '    Username: admin',
            '    Password: admin123',
            '',
            '  Al Waha Restaurant (active - amber theme):',
            '    Menu:     http://localhost:5000/r/al-waha/',
            '    Dashboard:http://localhost:5000/restaurant/dashboard',
            '    Owner:    waha_owner / waha123',
            '    Kitchen:  waha_kitchen / kitchen123',
            '    Cashier:  waha_cashier / cashier123',
            '    Coupon 1: WELCOME10 (10% off, min 5 OMR)',
            '    Coupon 2: SAVE1 (fixed 1 OMR off, min 3 OMR)',
            '',
            '  Al Nakheel Cafe (pending - ocean theme):',
            '    Owner:    nakheel_owner / nakheel123',
            '    (Needs Super Admin approval first)',
            '',
            '  Register new restaurant:',
            '    http://localhost:5000/register',
            '',
            sep,
        ]
        for line in lines:
            print(line)


if __name__ == '__main__':
    seed()
