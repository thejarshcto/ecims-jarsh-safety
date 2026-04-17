"""
Jarsh Safety — ECIMS Backend
Flask Application Entry Point — Railway Deployment
"""

from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, jwt
from routes.auth import auth_bp
from routes.skus import skus_bp
from routes.stock import stock_bp
from routes.allocations import allocations_bp
from routes.employees import employees_bp
from routes.projects import projects_bp
from routes.suppliers import suppliers_bp
from routes.reports import reports_bp
from routes.logs import logs_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Allow all origins for Railway deployment
    CORS(app, origins="*")

    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints
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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
