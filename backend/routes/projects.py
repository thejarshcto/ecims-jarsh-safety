"""ECIMS — Projects Routes"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from backend.extensions import db
from backend.models import Project
from backend.helpers import log_action, ok, err

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    projects = Project.query.filter_by(active=True).order_by(Project.name).all()
    return ok([p.to_dict() for p in projects])


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    data = request.get_json()
    if not data.get("name"):
        return err("name required")
    p = Project(name=data["name"], description=data.get("description"))
    db.session.add(p)
    db.session.commit()
    log_action("CREATE_PROJECT", f"{p.name}")
    return ok(p.to_dict(), status=201)


@projects_bp.route("/<int:pid>", methods=["PUT"])
@jwt_required()
def update_project(pid):
    p = Project.query.get_or_404(pid)
    data = request.get_json()
    for f in ["name", "description", "active"]:
        if f in data:
            setattr(p, f, data[f])
    db.session.commit()
    return ok(p.to_dict())
