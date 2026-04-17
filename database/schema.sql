-- =============================================================
-- JARSH SAFETY — ECIMS Database Schema
-- Version: 1.0
-- Run this in MySQL after creating the database:
--   CREATE DATABASE ecims;
--   USE ecims;
-- =============================================================

CREATE DATABASE IF NOT EXISTS ecims;
USE ecims;

-- -------------------------------------------------------------
-- USERS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager') NOT NULL DEFAULT 'manager',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Default admin user: admin / admin123 (change after first login)
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$KIX5e5R1yPwgYn9Y3bGIEuRqRc0LJkGwE1rFfF7v0B5fMvPbqt6Cy', 'admin');
-- Password above is bcrypt hash of 'admin123'

-- -------------------------------------------------------------
-- SUPPLIERS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    contact VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO suppliers (name) VALUES ('LCSC'), ('Mouser'), ('DigiKey'), ('Local');

-- -------------------------------------------------------------
-- EMPLOYEES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- PROJECTS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- SKU MASTER
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sku_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lcsc_part_number VARCHAR(100),
    part_name VARCHAR(200) NOT NULL,
    ref_name VARCHAR(100),
    category ENUM('Resistor','Capacitor','IC','Inductor','Diode','Transistor','Connector','LED','Crystal','Other') NOT NULL,
    package VARCHAR(50),
    supplier_id INT,
    min_qty INT DEFAULT 10,
    remarks TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- -------------------------------------------------------------
-- STOCK ENTRIES (each purchase = new UID)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku_id INT NOT NULL,
    uid VARCHAR(50) NOT NULL UNIQUE,
    packet_no VARCHAR(100),
    qty_added INT NOT NULL,
    qty_available INT NOT NULL,
    unit_price DECIMAL(10,4) NOT NULL,
    total_price DECIMAL(12,2) GENERATED ALWAYS AS (qty_added * unit_price) STORED,
    supplier_id INT,
    purchase_date DATE DEFAULT (CURDATE()),
    created_by INT,
    FOREIGN KEY (sku_id) REFERENCES sku_master(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- -------------------------------------------------------------
-- ALLOCATIONS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS allocations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(50) NOT NULL,
    sku_id INT NOT NULL,
    employee_id INT NOT NULL,
    project_id INT,
    qty INT NOT NULL,
    returnable TINYINT(1) DEFAULT 0,
    remarks TEXT,
    allocation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (uid) REFERENCES stock_entries(uid),
    FOREIGN KEY (sku_id) REFERENCES sku_master(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- -------------------------------------------------------------
-- RETURNS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS returns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    allocation_id INT NOT NULL,
    qty_returned INT NOT NULL,
    return_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    created_by INT,
    FOREIGN KEY (allocation_id) REFERENCES allocations(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- -------------------------------------------------------------
-- AUDIT LOGS (immutable — no DELETE/UPDATE allowed via app)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- -------------------------------------------------------------
-- USEFUL VIEWS
-- -------------------------------------------------------------

-- Current available stock per SKU
CREATE OR REPLACE VIEW v_sku_stock AS
SELECT
    s.id AS sku_id,
    s.lcsc_part_number,
    s.part_name,
    s.ref_name,
    s.category,
    s.package,
    s.min_qty,
    COALESCE(SUM(se.qty_available), 0) AS total_available,
    COUNT(se.id) AS batch_count
FROM sku_master s
LEFT JOIN stock_entries se ON s.id = se.sku_id
GROUP BY s.id;

-- Low stock alert view
CREATE OR REPLACE VIEW v_low_stock AS
SELECT * FROM v_sku_stock
WHERE total_available < min_qty;

-- Allocation summary per employee
CREATE OR REPLACE VIEW v_employee_holdings AS
SELECT
    e.employee_id,
    e.name AS employee_name,
    a.id AS allocation_id,
    s.part_name,
    s.ref_name,
    a.uid,
    a.qty,
    a.returnable,
    a.allocation_date,
    COALESCE(SUM(r.qty_returned), 0) AS qty_returned,
    (a.qty - COALESCE(SUM(r.qty_returned), 0)) AS qty_outstanding
FROM allocations a
JOIN employees e ON a.employee_id = e.id
JOIN sku_master s ON a.sku_id = s.id
LEFT JOIN returns r ON a.id = r.allocation_id
GROUP BY a.id;
