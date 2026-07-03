import os
from datetime import datetime
from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

from app.translations import t as translate, format_price, LANGUAGES, DEFAULT_LANG, LANGUAGE_LABELS


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/glam_nails_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message_category = 'warning'

    @login_manager.unauthorized_handler
    def _unauthorized():
        from flask import redirect, url_for, flash
        flash(translate('admin.login_required'), 'warning')
        return redirect(url_for('admin.login'))

    # ─── i18n: resolve language once per request ─────────────────────────────
    @app.before_request
    def resolve_language():
        lang = request.args.get('lang') or request.cookies.get('lang')
        if lang not in LANGUAGES:
            lang = DEFAULT_LANG
        g.lang = lang

    @app.after_request
    def persist_language(response):
        requested = request.args.get('lang')
        if requested in LANGUAGES:
            response.set_cookie('lang', requested, max_age=60 * 60 * 24 * 365)
        return response

    @app.context_processor
    def inject_globals():
        return {
            'lang': getattr(g, 'lang', DEFAULT_LANG),
            'languages': LANGUAGES,
            'language_labels': LANGUAGE_LABELS,
            'current_year': datetime.utcnow().year,
        }

    app.jinja_env.globals['t'] = translate
    app.jinja_env.filters['price'] = format_price

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app