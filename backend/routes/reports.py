from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract
from backend.extensions import db
from backend.models import StockEntry, Allocation, Return, SKU, Employee
from backend.helpers import ok

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    total_skus = SKU.query.count()
    low_stock_count = sum(
        1 for sku in SKU.query.all()
        if sum(se.qty_available for se in sku.stock_entries) < sku.min_qty
    )
    total_stock_value = db.session.query(
        func.sum(StockEntry.qty_available * StockEntry.unit_price)
    ).scalar() or 0
    pending_returns = db.session.query(func.sum(Allocation.qty)).filter(
        Allocation.returnable == True
    ).scalar() or 0
    return ok({
        "total_skus": total_skus,
        "low_stock_count": low_stock_count,
        "total_stock_value_inr": float(total_stock_value),
        "pending_returns": int(pending_returns)
    })


@reports_bp.route("/monthly", methods=["GET"])
@jwt_required()
def monthly_report():
    year = int(request.args.get("year", 2026))
    month = int(request.args.get("month", 1))
    stock = db.session.query(
        func.count(StockEntry.id).label("entries"),
        func.sum(StockEntry.qty_added).label("qty"),
        func.sum(StockEntry.qty_added * StockEntry.unit_price).label("value")
    ).filter(
        extract("year", StockEntry.purchase_date) == year,
        extract("month", StockEntry.purchase_date) == month
    ).first()
    allocs = db.session.query(
        func.count(Allocation.id).label("count"),
        func.sum(Allocation.qty).label("qty")
    ).filter(
        extract("year", Allocation.allocation_date) == year,
        extract("month", Allocation.allocation_date) == month
    ).first()
    rets = db.session.query(
        func.count(Return.id).label("count"),
        func.sum(Return.qty_returned).label("qty")
    ).filter(
        extract("year", Return.return_date) == year,
        extract("month", Return.return_date) == month
    ).first()
    return ok({
        "year": year, "month": month,
        "stock_added": {"entries": stock.entries or 0, "qty": int(stock.qty or 0), "value_inr": float(stock.value or 0)},
        "allocations": {"count": allocs.count or 0, "qty": int(allocs.qty or 0)},
        "returns": {"count": rets.count or 0, "qty": int(rets.qty or 0)}
    })


@reports_bp.route("/sku", methods=["GET"])
@jwt_required()
def sku_report():
    skus = SKU.query.all()
    result = []
    for sku in skus:
        total_in = sum(se.qty_added for se in sku.stock_entries)
        total_available = sum(se.qty_available for se in sku.stock_entries)
        total_value = sum(float(se.unit_price) * se.qty_added for se in sku.stock_entries)
        result.append({
            "sku_id": sku.id, "part_name": sku.part_name, "ref_name": sku.ref_name,
            "category": sku.category, "package": sku.package,
            "total_in": total_in, "total_available": total_available,
            "total_allocated": total_in - total_available,
            "total_value_inr": round(total_value, 2),
            "low_stock": total_available < sku.min_qty
        })
    return ok(sorted(result, key=lambda x: x["part_name"]))


@reports_bp.route("/employee", methods=["GET"])
@jwt_required()
def employee_report():
    employees = Employee.query.filter_by(active=True).all()
    result = []
    for emp in employees:
        total_alloc = sum(a.qty for a in emp.allocations)
        total_returned = sum(r.qty_returned for a in emp.allocations for r in a.returns)
        outstanding = sum(
            (a.qty - sum(r.qty_returned for r in a.returns))
            for a in emp.allocations if a.returnable
        )
        result.append({
            "employee_id": emp.employee_id, "name": emp.name,
            "department": emp.department, "total_allocated": total_alloc,
            "total_returned": total_returned, "outstanding_returnable": outstanding,
            "allocation_count": len(emp.allocations)
        })
    return ok(result)
