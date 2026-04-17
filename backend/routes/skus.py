"""
ECIMS — SKU Routes
GET    /api/skus
POST   /api/skus
PUT    /api/skus/<id>
GET    /api/skus/<id>
GET    /api/skus/low-stock
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from extensions import db
from models import SKU
from helpers import log_action, ok, err
import csv, io

skus_bp = Blueprint("skus", __name__)


@skus_bp.route("", methods=["GET"])
@jwt_required()
def list_skus():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = SKU.query
    if search:
        query = query.filter(
            SKU.part_name.ilike(f"%{search}%") |
            SKU.ref_name.ilike(f"%{search}%") |
            SKU.lcsc_part_number.ilike(f"%{search}%")
        )
    if category:
        query = query.filter(SKU.category == category)

    skus = query.order_by(SKU.part_name).all()

    # Attach stock totals
    result = []
    for sku in skus:
        d = sku.to_dict()
        d["total_available"] = sum(se.qty_available for se in sku.stock_entries)
        d["low_stock"] = d["total_available"] < sku.min_qty
        result.append(d)

    return ok(result)


@skus_bp.route("/<int:sku_id>", methods=["GET"])
@jwt_required()
def get_sku(sku_id):
    sku = SKU.query.get_or_404(sku_id)
    d = sku.to_dict()
    d["total_available"] = sum(se.qty_available for se in sku.stock_entries)
    d["stock_entries"] = [se.to_dict() for se in sku.stock_entries]
    return ok(d)


@skus_bp.route("", methods=["POST"])
@jwt_required()
def create_sku():
    data = request.get_json()
    if not data.get("part_name") or not data.get("category"):
        return err("part_name and category are required")

    sku = SKU(
        lcsc_part_number=data.get("lcsc_part_number"),
        part_name=data["part_name"],
        ref_name=data.get("ref_name"),
        category=data["category"],
        package=data.get("package"),
        supplier_id=data.get("supplier_id"),
        min_qty=int(data.get("min_qty", 10)),
        remarks=data.get("remarks")
    )
    db.session.add(sku)
    db.session.commit()
    log_action("CREATE_SKU", f"SKU: {sku.part_name} ({sku.lcsc_part_number})")
    return ok(sku.to_dict(), status=201)


@skus_bp.route("/<int:sku_id>", methods=["PUT"])
@jwt_required()
def update_sku(sku_id):
    sku = SKU.query.get_or_404(sku_id)
    data = request.get_json()

    fields = ["lcsc_part_number", "part_name", "ref_name", "category",
              "package", "supplier_id", "min_qty", "remarks"]
    for f in fields:
        if f in data:
            setattr(sku, f, data[f])

    db.session.commit()
    log_action("UPDATE_SKU", f"SKU id={sku_id}: {sku.part_name}")
    return ok(sku.to_dict())


@skus_bp.route("/low-stock", methods=["GET"])
@jwt_required()
def low_stock():
    skus = SKU.query.all()
    result = []
    for sku in skus:
        total = sum(se.qty_available for se in sku.stock_entries)
        if total < sku.min_qty:
            d = sku.to_dict()
            d["total_available"] = total
            result.append(d)
    return ok(result)


@skus_bp.route("/import", methods=["POST"])
@jwt_required()
def import_csv():
    """
    Accepts CSV: LCSC Part #, Part Name, Ref Name, Package, Qty, Price, Supplier
    """
    if "file" not in request.files:
        return err("No file uploaded")

    f = request.files["file"]
    content = f.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    created, skipped = 0, 0
    for row in reader:
        try:
            sku = SKU(
                lcsc_part_number=row.get("LCSC Part #", "").strip(),
                part_name=row.get("Part Name", "").strip(),
                ref_name=row.get("Ref Name", "").strip(),
                category="Other",
                package=row.get("Package", "").strip(),
            )
            db.session.add(sku)
            created += 1
        except Exception:
            skipped += 1

    db.session.commit()
    log_action("IMPORT_SKU_CSV", f"Imported {created} SKUs, skipped {skipped}")
    return ok({"created": created, "skipped": skipped})
