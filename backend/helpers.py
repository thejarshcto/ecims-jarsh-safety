"""
ECIMS — Shared Helpers
"""
from datetime import datetime
from flask import request
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import AuditLog, StockEntry, SKU
import re


# ── UID Generation ────────────────────────────────────────────────────────────

CATEGORY_TYPE_MAP = {
    "Resistor": "R",
    "Capacitor": "C",
    "IC": "IC",
    "Inductor": "L",
    "Diode": "D",
    "Transistor": "Q",
    "Connector": "CN",
    "LED": "LED",
    "Crystal": "XL",
    "Other": "X",
}


def generate_uid(sku: SKU) -> str:
    """
    Format: [TYPE][PACKAGE]-[REF]-[YEAR]-[RUNNING4]
    Example: R0603-10K-2026-0001
    """
    type_code = CATEGORY_TYPE_MAP.get(sku.category, "X")
    package = re.sub(r"\s+", "", sku.package or "").upper()
    ref = re.sub(r"\s+", "", sku.ref_name or sku.part_name or "").replace("/", "-")
    year = str(datetime.utcnow().year)

    # Count existing entries for this SKU to get running number
    existing = StockEntry.query.filter_by(sku_id=sku.id).count()
    running = str(existing + 1).zfill(4)

    uid = f"{type_code}{package}-{ref}-{year}-{running}"
    # Ensure uniqueness — increment if collision
    while StockEntry.query.filter_by(uid=uid).first():
        running = str(int(running) + 1).zfill(4)
        uid = f"{type_code}{package}-{ref}-{year}-{running}"

    return uid


# ── Audit Logging ─────────────────────────────────────────────────────────────

def log_action(action: str, details: str = ""):
    try:
        identity = get_jwt_identity()
        user_id = identity.get("id") if identity else None
        username = identity.get("username") if identity else "system"
    except Exception:
        user_id = None
        username = "system"

    entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()


# ── Response Helpers ──────────────────────────────────────────────────────────

def ok(data=None, message="success", status=200):
    return {"success": True, "message": message, "data": data}, status


def err(message="error", status=400):
    return {"success": False, "message": message}, status
