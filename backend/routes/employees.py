from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models import Employee
from backend.helpers import log_action, ok, err

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("", methods=["GET"])
@jwt_required()
def list_employees():
    return ok([e.to_dict() for e in Employee.query.filter_by(active=True).order_by(Employee.name).all()])


@employees_bp.route("", methods=["POST"])
@jwt_required()
def create_employee():
    data = request.get_json()
    if Employee.query.filter_by(employee_id=data["employee_id"]).first():
        return err("Employee ID already exists")
    emp = Employee(
        employee_id=data["employee_id"],
        name=data["name"],
        department=data.get("department")
    )
    db.session.add(emp)
    db.session.commit()
    log_action("CREATE_EMPLOYEE", f"{emp.name}")
    return ok(emp.to_dict(), status=201)


@employees_bp.route("/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    data = request.get_json()
    for f in ["name", "department", "active"]:
        if f in data:
            setattr(emp, f, data[f])
    db.session.commit()
    return ok(emp.to_dict())
