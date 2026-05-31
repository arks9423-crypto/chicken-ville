from flask import Flask, send_from_directory, jsonify, redirect, url_for, flash, request
from extensions import db, login_manager
from config import Config
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.errorhandler(413)
    def too_large(e):
        # Return to previous page with flash message instead of blank error
        flash('الصورة كبيرة جداً. يتم ضغطها تلقائياً — حاول مجدداً.', 'error')
        return redirect(request.referrer or url_for('main.index')), 303

    db.init_app(app)
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/sw.js')
    def service_worker():
        return send_from_directory(app.static_folder, 'sw.js',
                                   mimetype='application/javascript')

    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.platform import platform_bp
    from routes.restaurant import restaurant_bp
    from routes.menu import menu_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app
