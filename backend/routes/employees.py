"""
ECIMS — Employees Routes
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from extensions import db
from models import Employee
from helpers import log_action, ok, err

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("", methods=["GET"])
@jwt_required()
def list_employees():
    employees = Employee.query.filter_by(active=True).order_by(Employee.name).all()
    return ok([e.to_dict() for e in employees])


@employees_bp.route("", methods=["POST"])
@jwt_required()
def create_employee():
    data = request.get_json()
    if not data.get("employee_id") or not data.get("name"):
        return err("employee_id and name required")

    if Employee.query.filter_by(employee_id=data["employee_id"]).first():
        return err("Employee ID already exists")

    emp = Employee(
        employee_id=data["employee_id"],
        name=data["name"],
        department=data.get("department")
    )
    db.session.add(emp)
    db.session.commit()
    log_action("CREATE_EMPLOYEE", f"{emp.name} ({emp.employee_id})")
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


@employees_bp.route("/<int:emp_id>/holdings", methods=["GET"])
@jwt_required()
def employee_holdings(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    allocations = []
    for a in emp.allocations:
        d = a.to_dict()
        if d["qty_outstanding"] > 0:
            allocations.append(d)
    return ok({"employee": emp.to_dict(), "holdings": allocations})
