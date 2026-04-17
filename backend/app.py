from flask import Flask
from flask_cors import CORS
from backend.config import Config
from backend.extensions import db, jwt
import bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins="*")
    db.init_app(app)
    jwt.init_app(app)

    from backend.routes.auth import auth_bp
    from backend.routes.skus import skus_bp
    from backend.routes.stock import stock_bp
    from backend.routes.allocations import allocations_bp
    from backend.routes.employees import employees_bp
    from backend.routes.projects import projects_bp
    from backend.routes.suppliers import suppliers_bp
    from backend.routes.reports import reports_bp
    from backend.routes.logs import logs_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(skus_bp, url_prefix="/api/skus")
    app.register_blueprint(stock_bp, url_prefix="/api/stock")
    app.register_blueprint(allocations_bp, url_prefix="/api/allocations")
    app.register_blueprint(employees_bp, url_prefix="/api/employees")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(suppliers_bp, url_prefix="/api/suppliers")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(logs_bp, url_prefix="/api/logs")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "system": "Jarsh Safety ECIMS"}

    with app.app_context():
        db.create_all()
        _seed()

    return app


def _seed():
    from backend.models import User, Supplier
    if not User.query.filter_by(username="admin").first():
        h = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        db.session.add(User(username="admin", password_hash=h, role="admin"))
    for name in ["LCSC", "Mouser", "DigiKey", "Local"]:
        if not Supplier.query.filter_by(name=name).first():
            db.session.add(Supplier(name=name))
    db.session.commit()
