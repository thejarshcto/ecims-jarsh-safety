"""
ECIMS — Stock Entry Routes
POST /api/stock
GET  /api/stock
GET  /api/stock/uid/<uid>
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import StockEntry, SKU
from helpers import generate_uid, log_action, ok, err

stock_bp = Blueprint("stock", __name__)


@stock_bp.route("", methods=["POST"])
@jwt_required()
def add_stock():
    identity = get_jwt_identity()
    data = request.get_json()

    required = ["sku_id", "qty_added", "unit_price"]
    for r in required:
        if r not in data:
            return err(f"Missing field: {r}")

    sku = SKU.query.get(data["sku_id"])
    if not sku:
        return err("SKU not found", 404)

    uid = generate_uid(sku)

    entry = StockEntry(
        sku_id=data["sku_id"],
        uid=uid,
        packet_no=data.get("packet_no"),
        qty_added=int(data["qty_added"]),
        qty_available=int(data["qty_added"]),
        unit_price=float(data["unit_price"]),
        supplier_id=data.get("supplier_id"),
        purchase_date=data.get("purchase_date"),
        created_by=identity["id"]
    )
    db.session.add(entry)
    db.session.commit()

    log_action(
        "STOCK_ENTRY",
        f"UID: {uid} | SKU: {sku.part_name} | Qty: {data['qty_added']} | Price: ₹{data['unit_price']}"
    )
    return ok(entry.to_dict(), status=201)


@stock_bp.route("", methods=["GET"])
@jwt_required()
def list_stock():
    sku_id = request.args.get("sku_id")
    query = StockEntry.query

    if sku_id:
        query = query.filter_by(sku_id=sku_id)

    entries = query.order_by(StockEntry.id.desc()).all()
    return ok([e.to_dict() for e in entries])


@stock_bp.route("/uid/<uid>", methods=["GET"])
@jwt_required()
def get_by_uid(uid):
    entry = StockEntry.query.filter_by(uid=uid).first_or_404()
    d = entry.to_dict()
    d["allocations"] = [a.to_dict() for a in entry.sku.allocations if a.uid == uid]
    return ok(d)


@stock_bp.route("/uids-for-sku/<int:sku_id>", methods=["GET"])
@jwt_required()
def uids_for_sku(sku_id):
    """Return UIDs with available qty > 0 for allocation dropdown"""
    entries = StockEntry.query.filter(
        StockEntry.sku_id == sku_id,
        StockEntry.qty_available > 0
    ).all()
    return ok([{"uid": e.uid, "qty_available": e.qty_available} for e in entries])
