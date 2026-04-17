from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models import StockEntry, SKU
from backend.helpers import generate_uid, log_action, ok, err

stock_bp = Blueprint("stock", __name__)


@stock_bp.route("", methods=["POST"])
@jwt_required()
def add_stock():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    sku = SKU.query.get(data.get("sku_id"))
    if not sku:
        return err("SKU not found", 404)
    uid = generate_uid(sku)
    entry = StockEntry(
        sku_id=data["sku_id"], uid=uid, packet_no=data.get("packet_no"),
        qty_added=int(data["qty_added"]), qty_available=int(data["qty_added"]),
        unit_price=float(data["unit_price"]), supplier_id=data.get("supplier_id"),
        purchase_date=data.get("purchase_date"), created_by=user_id
    )
    db.session.add(entry)
    db.session.commit()
    log_action("STOCK_ENTRY", f"UID: {uid} | SKU: {sku.part_name} | Qty: {data['qty_added']}")
    return ok(entry.to_dict(), status=201)


@stock_bp.route("", methods=["GET"])
@jwt_required()
def list_stock():
    sku_id = request.args.get("sku_id")
    query = StockEntry.query
    if sku_id:
        query = query.filter_by(sku_id=sku_id)
    return ok([e.to_dict() for e in query.order_by(StockEntry.id.desc()).all()])


@stock_bp.route("/uids-for-sku/<int:sku_id>", methods=["GET"])
@jwt_required()
def uids_for_sku(sku_id):
    entries = StockEntry.query.filter(
        StockEntry.sku_id == sku_id,
        StockEntry.qty_available > 0
    ).all()
    return ok([{"uid": e.uid, "qty_available": e.qty_available} for e in entries])
