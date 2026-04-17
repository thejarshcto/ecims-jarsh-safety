from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from backend.extensions import db
from backend.models import Supplier
from backend.helpers import ok, err

suppliers_bp = Blueprint("suppliers", __name__)


@suppliers_bp.route("", methods=["GET"])
@jwt_required()
def list_suppliers():
    return ok([s.to_dict() for s in Supplier.query.order_by(Supplier.name).all()])


@suppliers_bp.route("", methods=["POST"])
@jwt_required()
def create_supplier():
    data = request.get_json()
    s = Supplier(name=data["name"], contact=data.get("contact"))
    db.session.add(s)
    db.session.commit()
    return ok(s.to_dict(), status=201)
