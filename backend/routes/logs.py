"""ECIMS — Audit Logs Routes (read-only for managers, immutable)"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from backend.models import AuditLog
from backend.helpers import ok

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("", methods=["GET"])
@jwt_required()
def list_logs():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    action = request.args.get("action", "").strip()

    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()) \
                .offset((page - 1) * per_page).limit(per_page).all()

    return ok({
        "logs": [l.to_dict() for l in logs],
        "total": total,
        "page": page,
        "per_page": per_page
    })
