from datetime import datetime
from flask import request
from backend.extensions import db
from backend.models import AuditLog, StockEntry, SKU
import re

CATEGORY_TYPE_MAP = {
    "Resistor": "R", "Capacitor": "C", "IC": "IC", "Inductor": "L",
    "Diode": "D", "Transistor": "Q", "Connector": "CN", "LED": "LED",
    "Crystal": "XL", "Other": "X",
}


def generate_uid(sku):
    type_code = CATEGORY_TYPE_MAP.get(sku.category, "X")
    package = re.sub(r"\s+", "", sku.package or "").upper()
    ref = re.sub(r"\s+", "", sku.ref_name or sku.part_name or "").replace("/", "-")
    year = str(datetime.utcnow().year)
    existing = StockEntry.query.filter_by(sku_id=sku.id).count()
    running = str(existing + 1).zfill(4)
    uid = f"{type_code}{package}-{ref}-{year}-{running}"
    while StockEntry.query.filter_by(uid=uid).first():
        running = str(int(running) + 1).zfill(4)
        uid = f"{type_code}{package}-{ref}-{year}-{running}"
    return uid


def log_action(action, details=""):
    try:
        from flask_jwt_extended import get_jwt_identity
        identity = get_jwt_identity()
        user_id = identity.get("id") if identity else None
        username = identity.get("username") if identity else "system"
    except Exception:
        user_id = None
        username = "system"
    entry = AuditLog(
        user_id=user_id, username=username, action=action,
        details=details, ip_address=request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()


def ok(data=None, message="success", status=200):
    return {"success": True, "message": message, "data": data}, status


def err(message="error", status=400):
    return {"success": False, "message": message}, status
