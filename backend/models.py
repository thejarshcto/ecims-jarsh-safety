"""
ECIMS — SQLAlchemy Models
"""
from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "manager"), nullable=False, default="manager")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "role": self.role}


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    contact = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "contact": self.contact}


class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "employee_id": self.employee_id,
            "name": self.name, "department": self.department,
            "active": self.active
        }


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description, "active": self.active}


class SKU(db.Model):
    __tablename__ = "sku_master"
    id = db.Column(db.Integer, primary_key=True)
    lcsc_part_number = db.Column(db.String(100))
    part_name = db.Column(db.String(200), nullable=False)
    ref_name = db.Column(db.String(100))
    category = db.Column(db.Enum(
        "Resistor", "Capacitor", "IC", "Inductor", "Diode",
        "Transistor", "Connector", "LED", "Crystal", "Other"
    ), nullable=False)
    package = db.Column(db.String(50))
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    min_qty = db.Column(db.Integer, default=10)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    supplier = db.relationship("Supplier", backref="skus")

    def to_dict(self):
        return {
            "id": self.id, "lcsc_part_number": self.lcsc_part_number,
            "part_name": self.part_name, "ref_name": self.ref_name,
            "category": self.category, "package": self.package,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "min_qty": self.min_qty, "remarks": self.remarks,
            "created_at": self.created_at.isoformat()
        }


class StockEntry(db.Model):
    __tablename__ = "stock_entries"
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.Integer, db.ForeignKey("sku_master.id"), nullable=False)
    uid = db.Column(db.String(50), unique=True, nullable=False)
    packet_no = db.Column(db.String(100))
    qty_added = db.Column(db.Integer, nullable=False)
    qty_available = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 4), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    purchase_date = db.Column(db.Date, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    sku = db.relationship("SKU", backref="stock_entries")
    supplier = db.relationship("Supplier")

    def to_dict(self):
        return {
            "id": self.id, "sku_id": self.sku_id, "uid": self.uid,
            "packet_no": self.packet_no, "qty_added": self.qty_added,
            "qty_available": self.qty_available,
            "unit_price": float(self.unit_price),
            "total_price": float(self.unit_price) * self.qty_added,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "part_name": self.sku.part_name if self.sku else None,
            "ref_name": self.sku.ref_name if self.sku else None
        }


class Allocation(db.Model):
    __tablename__ = "allocations"
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), db.ForeignKey("stock_entries.uid"), nullable=False)
    sku_id = db.Column(db.Integer, db.ForeignKey("sku_master.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    qty = db.Column(db.Integer, nullable=False)
    returnable = db.Column(db.Boolean, default=False)
    remarks = db.Column(db.Text)
    allocation_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    employee = db.relationship("Employee", backref="allocations")
    project = db.relationship("Project", backref="allocations")
    sku = db.relationship("SKU")

    def to_dict(self):
        qty_returned = sum(r.qty_returned for r in self.returns)
        return {
            "id": self.id, "uid": self.uid, "sku_id": self.sku_id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "employee_code": self.employee.employee_id if self.employee else None,
            "project_id": self.project_id,
            "project_name": self.project.name if self.project else None,
            "qty": self.qty, "returnable": self.returnable,
            "remarks": self.remarks,
            "allocation_date": self.allocation_date.isoformat(),
            "part_name": self.sku.part_name if self.sku else None,
            "qty_returned": qty_returned,
            "qty_outstanding": self.qty - qty_returned
        }


class Return(db.Model):
    __tablename__ = "returns"
    id = db.Column(db.Integer, primary_key=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocations.id"), nullable=False)
    qty_returned = db.Column(db.Integer, nullable=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    allocation = db.relationship("Allocation", backref="returns")

    def to_dict(self):
        return {
            "id": self.id, "allocation_id": self.allocation_id,
            "qty_returned": self.qty_returned,
            "return_date": self.return_date.isoformat(),
            "remarks": self.remarks
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    username = db.Column(db.String(100))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "username": self.username, "action": self.action,
            "details": self.details, "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat()
        }
