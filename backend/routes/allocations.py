"""
ECIMS — Allocation & Returns Routes
POST /api/allocations
GET  /api/allocations
POST /api/allocations/<id>/return
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models import Allocation, StockEntry, Return
from backend.helpers import log_action, ok, err

allocations_bp = Blueprint("allocations", __name__)


@allocations_bp.route("", methods=["POST"])
@jwt_required()
def allocate():
    identity = get_jwt_identity()
    data = request.get_json()

    required = ["uid", "sku_id", "employee_id", "qty"]
    for r in required:
        if r not in data:
            return err(f"Missing field: {r}")

    entry = StockEntry.query.filter_by(uid=data["uid"]).first()
    if not entry:
        return err("UID not found", 404)

    qty = int(data["qty"])
    if qty <= 0:
        return err("Quantity must be positive")
    if entry.qty_available < qty:
        return err(
            f"Insufficient stock. Available: {entry.qty_available}, Requested: {qty}"
        )

    allocation = Allocation(
        uid=data["uid"],
        sku_id=data["sku_id"],
        employee_id=data["employee_id"],
        project_id=data.get("project_id"),
        qty=qty,
        returnable=bool(data.get("returnable", False)),
        remarks=data.get("remarks"),
        created_by=identity["id"]
    )
    entry.qty_available -= qty

    db.session.add(allocation)
    db.session.commit()

    log_action(
        "ALLOCATE",
        f"UID: {data['uid']} | Qty: {qty} | Employee: {data['employee_id']} | Project: {data.get('project_id', 'N/A')}"
    )
    return ok(allocation.to_dict(), status=201)


@allocations_bp.route("", methods=["GET"])
@jwt_required()
def list_allocations():
    employee_id = request.args.get("employee_id")
    sku_id = request.args.get("sku_id")
    query = Allocation.query

    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if sku_id:
        query = query.filter_by(sku_id=sku_id)

    allocations = query.order_by(Allocation.allocation_date.desc()).all()
    return ok([a.to_dict() for a in allocations])


@allocations_bp.route("/<int:alloc_id>/return", methods=["POST"])
@jwt_required()
def process_return(alloc_id):
    identity = get_jwt_identity()
    data = request.get_json()

    allocation = Allocation.query.get_or_404(alloc_id)
    if not allocation.returnable:
        return err("This allocation is marked as non-returnable")

    qty_returned = int(data.get("qty_returned", 0))
    if qty_returned <= 0:
        return err("qty_returned must be positive")

    # Calculate how much has already been returned
    already_returned = sum(r.qty_returned for r in allocation.returns)
    outstanding = allocation.qty - already_returned
    if qty_returned > outstanding:
        return err(f"Cannot return more than outstanding ({outstanding})")

    ret = Return(
        allocation_id=alloc_id,
        qty_returned=qty_returned,
        remarks=data.get("remarks"),
        created_by=identity["id"]
    )

    # Restore stock
    entry = StockEntry.query.filter_by(uid=allocation.uid).first()
    if entry:
        entry.qty_available += qty_returned

    db.session.add(ret)
    db.session.commit()

    log_action(
        "RETURN",
        f"Allocation ID: {alloc_id} | Returned: {qty_returned} | UID: {allocation.uid}"
    )
    return ok(ret.to_dict(), status=201)
