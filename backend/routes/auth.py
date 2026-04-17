from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from functools import wraps
import bcrypt
from backend.extensions import db
from backend.models import User
from backend.helpers import log_action, ok, err

auth_bp = Blueprint("auth", __name__)


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return err("Admin access required", 403)
        return fn(*args, **kwargs)
    return wrapper


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return err("Username and password required")
    user = User.query.filter_by(username=data["username"]).first()
    if not user:
        return err("Invalid credentials", 401)
    if not bcrypt.checkpw(data["password"].encode(), user.password_hash.encode()):
        return err("Invalid credentials", 401)
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username, "role": user.role}
    )
    log_action("LOGIN", f"User {user.username} logged in")
    return ok({"token": token, "user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    claims = get_jwt()
    log_action("LOGOUT", f"User {claims.get('username')} logged out")
    return ok(message="Logged out")


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    user = User.query.get(user_id)
    if not bcrypt.checkpw(data["current_password"].encode(), user.password_hash.encode()):
        return err("Current password incorrect", 401)
    user.password_hash = bcrypt.hashpw(
        data["new_password"].encode(), bcrypt.gensalt()
    ).decode()
    db.session.commit()
    return ok(message="Password updated")


@auth_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    return ok([u.to_dict() for u in User.query.all()])


@auth_bp.route("/users", methods=["POST"])
@admin_required
def create_user():
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return err("Username already exists")
    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        username=data["username"],
        password_hash=hashed,
        role=data.get("role", "manager")
    )
    db.session.add(user)
    db.session.commit()
    log_action("CREATE_USER", f"Created: {user.username}")
    return ok(user.to_dict(), status=201)


@auth_bp.route("/users/<int:uid>/reset-password", methods=["POST"])
@admin_required
def reset_password(uid):
    data = request.get_json()
    user = User.query.get_or_404(uid)
    user.password_hash = bcrypt.hashpw(
        data.get("new_password", "Welcome@123").encode(), bcrypt.gensalt()
    ).decode()
    db.session.commit()
    log_action("RESET_PASSWORD", f"Reset password for: {user.username}")
    return ok(message=f"Password reset for {user.username}")


@auth_bp.route("/users/<int:uid>", methods=["DELETE"])
@admin_required
def delete_user(uid):
    identity = int(get_jwt_identity())
    if uid == identity:
        return err("Cannot delete your own account")
    user = User.query.get_or_404(uid)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_action("DELETE_USER", f"Deleted: {username}")
    return ok(message="User deleted")
