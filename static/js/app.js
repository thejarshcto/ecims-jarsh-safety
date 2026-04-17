/* ECIMS — Main Application Logic */

let currentUser = null;

// ── Bootstrap ─────────────────────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("ecims_token");
  const user = localStorage.getItem("ecims_user");
  if (token && user) {
    authToken = token;
    currentUser = JSON.parse(user);
    showApp();
  } else {
    showLogin();
  }

  document.getElementById("loginPassword").addEventListener("keydown", e => {
    if (e.key === "Enter") doLogin();
  });
});

// ── Auth ──────────────────────────────────────────────────────────────────────

function showLogin() {
  document.getElementById("loginOverlay").style.display = "flex";
  document.getElementById("app").style.display = "none";
}

function showApp() {
  document.getElementById("loginOverlay").style.display = "none";
  document.getElementById("app").style.display = "flex";
  document.getElementById("sidebarUsername").textContent = currentUser.username;
  document.getElementById("sidebarRole").textContent =
    currentUser.role === "admin" ? "Administrator" : "Manager";
  document.getElementById("userAvatar").textContent =
    currentUser.username[0].toUpperCase();

  if (currentUser.role === "admin") {
    document.getElementById("adminNavItem").style.display = "block";
  }

  showPage("dashboard");
  loadDropdowns();
}

async function doLogin() {
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;
  const errEl = document.getElementById("loginError");
  errEl.style.display = "none";

  if (!username || !password) {
    errEl.textContent = "Please enter username and password.";
    errEl.style.display = "block";
    return;
  }

  const res = await API.post("/auth/login", { username, password });
  if (!res || !res.success) {
    errEl.textContent = res?.message || "Login failed.";
    errEl.style.display = "block";
    return;
  }

  authToken = res.data.token;
  currentUser = res.data.user;
  localStorage.setItem("ecims_token", authToken);
  localStorage.setItem("ecims_user", JSON.stringify(currentUser));
  showApp();
}

async function doLogout() {
  await API.post("/auth/logout", {});
  authToken = null;
  currentUser = null;
  localStorage.removeItem("ecims_token");
  localStorage.removeItem("ecims_user");
  showLogin();
}

// ── Navigation ────────────────────────────────────────────────────────────────

const PAGE_TITLES = {
  dashboard: "Dashboard", skus: "SKU Master", stock: "Stock Entry",
  allocate: "Allocations", returns: "Returns", employees: "Employees",
  projects: "Projects", reports: "Reports", logs: "Audit Logs", admin: "Admin"
};

function showPage(name) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const page = document.getElementById("page-" + name);
  if (page) page.classList.add("active");

  const nav = document.querySelector(`.nav-item[data-page="${name}"]`);
  if (nav) nav.classList.add("active");

  document.getElementById("pageTitle").textContent = PAGE_TITLES[name] || name;

  const loaders = {
    dashboard: loadDashboard,
    skus: loadSKUs,
    stock: loadStockPage,
    allocate: loadAllocatePage,
    returns: loadReturnsPage,
    employees: loadEmployees,
    projects: loadProjects,
    logs: loadLogs,
    admin: loadUsers,
  };
  if (loaders[name]) loaders[name]();
}

// ── Shared Dropdowns ──────────────────────────────────────────────────────────

async function loadDropdowns() {
  const [suppliers, employees, projects, skus] = await Promise.all([
    API.get("/suppliers"),
    API.get("/employees"),
    API.get("/projects"),
    API.get("/skus"),
  ]);

  if (suppliers?.success) {
    populateSelect("stockSupplier", suppliers.data, "id", "name", "Select supplier...");
    populateSelect("skuSupplier", suppliers.data, "id", "name", "Select supplier...");
  }
  if (employees?.success) {
    populateSelect("allocEmployee", employees.data, "id", "name", "Select employee...", e => `${e.name} (${e.employee_id})`);
  }
  if (projects?.success) {
    populateSelect("allocProject", projects.data, "id", "name", "Select project...");
  }
  if (skus?.success) {
    populateSelect("stockSKU", skus.data, "id", "part_name", "Select SKU...", s => `${s.part_name} ${s.ref_name ? '— ' + s.ref_name : ''}`);
    populateSelect("allocSKU", skus.data, "id", "part_name", "Select SKU...", s => `${s.part_name} ${s.ref_name ? '— ' + s.ref_name : ''}`);
  }
}

function populateSelect(id, items, valKey, labelKey, placeholder, labelFn = null) {
  const sel = document.getElementById(id);
  if (!sel) return;
  sel.innerHTML = `<option value="">${placeholder}</option>`;
  (items || []).forEach(item => {
    const opt = document.createElement("option");
    opt.value = item[valKey];
    opt.textContent = labelFn ? labelFn(item) : item[labelKey];
    sel.appendChild(opt);
  });
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

async function loadDashboard() {
  const res = await API.get("/reports/dashboard");
  if (!res?.success) return;
  const d = res.data;

  document.getElementById("statSKUs").textContent = d.total_skus;
  document.getElementById("statValue").textContent = "₹" + d.total_stock_value_inr.toLocaleString("en-IN", { maximumFractionDigits: 0 });
  document.getElementById("statLowStock").textContent = d.low_stock_count;
  document.getElementById("statReturns").textContent = d.pending_returns;

  if (d.low_stock_count > 0) {
    document.getElementById("lowStockBadge").style.display = "flex";
    document.getElementById("lowStockCount").textContent = d.low_stock_count;
  }

  // Low stock table
  const lsRes = await API.get("/skus/low-stock");
  if (lsRes?.success) {
    document.getElementById("lowStockTable").innerHTML = lsRes.data.length === 0
      ? `<div class="empty-state">✅ No low stock alerts</div>`
      : renderTable(lsRes.data, ["part_name", "ref_name", "category", "package", "total_available", "min_qty"], [
          "Part Name", "Ref", "Category", "Package", "Available", "Min Qty"
        ], row => `<span class="low-badge">⚠ ${row.total_available} / ${row.min_qty}</span>`);
  }

  // Recent logs
  const logsRes = await API.get("/logs?per_page=8");
  if (logsRes?.success) {
    document.getElementById("recentLogs").innerHTML = renderLogsTable(logsRes.data.logs);
  }
}

// ── SKUs ──────────────────────────────────────────────────────────────────────

async function loadSKUs() {
  const q = document.getElementById("skuSearch")?.value || "";
  const cat = document.getElementById("skuCatFilter")?.value || "";
  let url = "/skus?q=" + encodeURIComponent(q);
  if (cat) url += "&category=" + encodeURIComponent(cat);

  const res = await API.get(url);
  if (!res?.success) return;

  const html = res.data.length === 0
    ? `<div class="empty-state">No SKUs found. Add your first SKU.</div>`
    : `<table>
        <thead><tr>
          <th>LCSC #</th><th>Part Name</th><th>Ref</th><th>Category</th>
          <th>Package</th><th>Available</th><th>Min Qty</th><th>Status</th>
        </tr></thead>
        <tbody>
          ${res.data.map(s => `<tr>
            <td class="uid-tag">${s.lcsc_part_number || "—"}</td>
            <td><strong>${s.part_name}</strong></td>
            <td>${s.ref_name || "—"}</td>
            <td><span class="badge badge-info">${s.category}</span></td>
            <td>${s.package || "—"}</td>
            <td>${s.total_available}</td>
            <td>${s.min_qty}</td>
            <td>${s.low_stock ? '<span class="badge badge-warn">⚠ Low</span>' : '<span class="badge badge-ok">OK</span>'}</td>
          </tr>`).join("")}
        </tbody>
      </table>`;

  document.getElementById("skuTable").innerHTML = html;
}

async function submitSKU() {
  const body = {
    lcsc_part_number: val("skuLCSC"),
    part_name: val("skuPartName"),
    ref_name: val("skuRefName"),
    category: val("skuCategory"),
    package: val("skuPackage"),
    min_qty: parseInt(val("skuMinQty")) || 10,
    supplier_id: val("skuSupplier") || null,
    remarks: val("skuRemarks"),
  };
  if (!body.part_name || !body.category) return showToast("Part name and category required", "error");

  const res = await API.post("/skus", body);
  if (!res?.success) return showToast(res?.message || "Error", "error");

  showToast("SKU added successfully", "success");
  closeModal("modalSKU");
  loadSKUs();
  loadDropdowns();
}

// ── Stock Entry ───────────────────────────────────────────────────────────────

async function loadStockPage() {
  // Set today's date
  document.getElementById("stockDate").value = new Date().toISOString().split("T")[0];
  loadStockTable();
}

async function loadStockTable() {
  const res = await API.get("/stock");
  if (!res?.success) return;

  document.getElementById("stockTable").innerHTML = res.data.length === 0
    ? `<div class="empty-state">No stock entries yet.</div>`
    : `<table>
        <thead><tr>
          <th>UID</th><th>Part Name</th><th>Ref</th><th>Qty Added</th>
          <th>Available</th><th>Unit Price</th><th>Total</th><th>Date</th>
        </tr></thead>
        <tbody>
          ${res.data.map(e => `<tr>
            <td><span class="uid-tag">${e.uid}</span></td>
            <td>${e.part_name || "—"}</td>
            <td>${e.ref_name || "—"}</td>
            <td>${e.qty_added}</td>
            <td><strong>${e.qty_available}</strong></td>
            <td>₹${parseFloat(e.unit_price).toFixed(4)}</td>
            <td>₹${parseFloat(e.total_price).toFixed(2)}</td>
            <td>${e.purchase_date || "—"}</td>
          </tr>`).join("")}
        </tbody>
      </table>`;
}

function calcTotal() {
  const qty = parseFloat(document.getElementById("stockQty")?.value) || 0;
  const price = parseFloat(document.getElementById("stockPrice")?.value) || 0;
  document.getElementById("stockTotal").value = qty && price ? "₹" + (qty * price).toFixed(2) : "";
}

document.addEventListener("input", e => {
  if (e.target.id === "stockQty" || e.target.id === "stockPrice") calcTotal();
});

async function updateStockUIDs() { /* Not needed for stock entry */ }

async function submitStock() {
  const body = {
    sku_id: val("stockSKU"),
    qty_added: parseInt(val("stockQty")),
    unit_price: parseFloat(val("stockPrice")),
    packet_no: val("stockPacket"),
    supplier_id: val("stockSupplier") || null,
    purchase_date: val("stockDate"),
  };
  if (!body.sku_id) return showToast("Please select a SKU", "error");
  if (!body.qty_added || !body.unit_price) return showToast("Qty and price required", "error");

  const res = await API.post("/stock", body);
  if (!res?.success) return showToast(res?.message || "Error", "error");

  showToast(`Stock added — UID: ${res.data.uid}`, "success");
  ["stockPacket", "stockQty", "stockPrice", "stockTotal"].forEach(id => {
    document.getElementById(id).value = "";
  });
  loadStockTable();
  loadDashboard();
}

// ── Allocations ───────────────────────────────────────────────────────────────

async function loadAllocatePage() {
  loadAllocTable();
}

async function loadAllocUIDs() {
  const skuId = val("allocSKU");
  const sel = document.getElementById("allocUID");
  sel.innerHTML = '<option value="">Loading...</option>';

  if (!skuId) {
    sel.innerHTML = '<option value="">Select SKU first</option>';
    return;
  }

  const res = await API.get("/stock/uids-for-sku/" + skuId);
  if (!res?.success || res.data.length === 0) {
    sel.innerHTML = '<option value="">No stock available</option>';
    return;
  }

  sel.innerHTML = '<option value="">Select UID...</option>';
  res.data.forEach(u => {
    const opt = document.createElement("option");
    opt.value = u.uid;
    opt.textContent = `${u.uid} (avail: ${u.qty_available})`;
    sel.appendChild(opt);
  });
}

async function loadAllocTable() {
  const res = await API.get("/allocations");
  if (!res?.success) return;

  document.getElementById("allocTable").innerHTML = res.data.length === 0
    ? `<div class="empty-state">No allocations yet.</div>`
    : `<table>
        <thead><tr>
          <th>ID</th><th>Part</th><th>UID</th><th>Employee</th>
          <th>Project</th><th>Qty</th><th>Returnable</th><th>Date</th>
        </tr></thead>
        <tbody>
          ${res.data.map(a => `<tr>
            <td>${a.id}</td>
            <td>${a.part_name || "—"}</td>
            <td><span class="uid-tag">${a.uid}</span></td>
            <td>${a.employee_name} <small style="color:var(--text-muted)">(${a.employee_code})</small></td>
            <td>${a.project_name || "—"}</td>
            <td>${a.qty}</td>
            <td>${a.returnable ? '<span class="badge badge-info">Yes</span>' : '<span class="badge badge-ok">No</span>'}</td>
            <td>${a.allocation_date?.split("T")[0]}</td>
          </tr>`).join("")}
        </tbody>
      </table>`;
}

async function submitAllocation() {
  const body = {
    uid: val("allocUID"),
    sku_id: val("allocSKU"),
    employee_id: val("allocEmployee"),
    project_id: val("allocProject") || null,
    qty: parseInt(val("allocQty")),
    returnable: val("allocReturnable") === "true",
    remarks: val("allocRemarks"),
  };
  if (!body.uid || !body.employee_id || !body.qty) {
    return showToast("Employee, UID, and qty are required", "error");
  }

  const res = await API.post("/allocations", body);
  if (!res?.success) return showToast(res?.message || "Error saving allocation", "error");

  showToast("Allocated successfully", "success");
  ["allocQty", "allocRemarks"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("allocUID").innerHTML = '<option value="">Select UID after SKU...</option>';
  loadAllocTable();
  loadDashboard();
}

// ── Returns ───────────────────────────────────────────────────────────────────

async function loadReturnsPage() {
  const res = await API.get("/allocations");
  if (!res?.success) return;

  const returnable = res.data.filter(a => a.returnable && a.qty_outstanding > 0);

  document.getElementById("returnTable").innerHTML = returnable.length === 0
    ? `<div class="empty-state">No pending returnable items.</div>`
    : `<table>
        <thead><tr>
          <th>Alloc ID</th><th>Part</th><th>UID</th><th>Employee</th>
          <th>Qty</th><th>Returned</th><th>Outstanding</th><th>Action</th>
        </tr></thead>
        <tbody>
          ${returnable.map(a => `<tr>
            <td>${a.id}</td>
            <td>${a.part_name || "—"}</td>
            <td><span class="uid-tag">${a.uid}</span></td>
            <td>${a.employee_name}</td>
            <td>${a.qty}</td>
            <td>${a.qty_returned}</td>
            <td><strong>${a.qty_outstanding}</strong></td>
            <td>
              <button class="btn btn-outline btn-sm"
                onclick="prefillReturn(${a.id})">Return</button>
            </td>
          </tr>`).join("")}
        </tbody>
      </table>`;
}

function prefillReturn(id) {
  document.getElementById("returnAllocId").value = id;
  document.getElementById("returnQty").focus();
}

async function submitReturn() {
  const allocId = val("returnAllocId");
  const qty = parseInt(val("returnQty"));
  const remarks = val("returnRemarks");

  if (!allocId || !qty) return showToast("Allocation ID and qty required", "error");

  const res = await API.post(`/allocations/${allocId}/return`, { qty_returned: qty, remarks });
  if (!res?.success) return showToast(res?.message || "Error processing return", "error");

  showToast("Return processed successfully", "success");
  ["returnAllocId", "returnQty", "returnRemarks"].forEach(id => document.getElementById(id).value = "");
  loadReturnsPage();
  loadDashboard();
}

// ── Employees ─────────────────────────────────────────────────────────────────

async function loadEmployees() {
  const res = await API.get("/employees");
  if (!res?.success) return;

  document.getElementById("employeeTable").innerHTML = res.data.length === 0
    ? `<div class="empty-state">No employees yet.</div>`
    : `<table>
        <thead><tr>
          <th>Employee ID</th><th>Name</th><th>Department</th><th>Status</th>
        </tr></thead>
        <tbody>
          ${res.data.map(e => `<tr>
            <td class="uid-tag">${e.employee_id}</td>
            <td>${e.name}</td>
            <td>${e.department || "—"}</td>
            <td><span class="badge badge-ok">Active</span></td>
          </tr>`).join("")}
        </tbody>
      </table>`;
}

async function submitEmployee() {
  const body = {
    employee_id: val("empId"),
    name: val("empName"),
    department: val("empDept"),
  };
  if (!body.employee_id || !body.name) return showToast("Employee ID and name required", "error");

  const res = await API.post("/employees", body);
  if (!res?.success) return showToast(res?.message || "Error", "error");

  showToast("Employee added", "success");
  closeModal("modalEmployee");
  loadEmployees();
  loadDropdowns();
}

// ── Projects ──────────────────────────────────────────────────────────────────

async function loadProjects() {
  const res = await API.get("/projects");
  if (!res?.success) return;

  document.getElementById("projectTable").innerHTML = res.data.length === 0
    ? `<div class="empty-state">No projects yet.</div>`
    : `<table>
        <thead><tr><th>Name</th><th>Description</th><th>Status</th></tr></thead>
        <tbody>
          ${res.data.map(p => `<tr>
            <td><strong>${p.name}</strong></td>
            <td>${p.description || "—"}</td>
            <td><span class="badge badge-ok">Active</span></td>
          </tr>`).join("")}
        </tbody>
      </table>`;
}

async function submitProject() {
  const body = { name: val("projName"), description: val("projDesc") };
  if (!body.name) return showToast("Project name required", "error");

  const res = await API.post("/projects", body);
  if (!res?.success) return showToast(res?.message || "Error", "error");

  showToast("Project added", "success");
  closeModal("modalProject");
  loadProjects();
  loadDropdowns();
}

// ── Reports ───────────────────────────────────────────────────────────────────

function showReport(name, btn) {
  document.querySelectorAll(".report-section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.getElementById("report-" + name).classList.add("active");
  btn.classList.add("active");

  if (name === "monthly") loadMonthlyReport();
  if (name === "sku") loadSKUReport();
  if (name === "employee") loadEmployeeReport();
}

async function loadMonthlyReport() {
  const year = val("reportYear");
  const month = val("reportMonth");
  const res = await API.get(`/reports/monthly?year=${year}&month=${month}`);
  if (!res?.success) return;
  const d = res.data;

  document.getElementById("monthlyReportData").innerHTML = `
    <div class="monthly-cards">
      <div class="monthly-card">
        <h4>Stock Added</h4>
        <div class="mval">${d.stock_added.qty.toLocaleString()}</div>
        <div style="color:var(--text-muted);font-size:0.85rem">units across ${d.stock_added.entries} entries</div>
        <div style="margin-top:0.4rem;font-weight:600;color:var(--orange)">₹${d.stock_added.value_inr.toLocaleString("en-IN",{maximumFractionDigits:2})}</div>
      </div>
      <div class="monthly-card">
        <h4>Allocations</h4>
        <div class="mval">${d.allocations.qty.toLocaleString()}</div>
        <div style="color:var(--text-muted);font-size:0.85rem">units across ${d.allocations.count} allocations</div>
      </div>
      <div class="monthly-card">
        <h4>Returns</h4>
        <div class="mval">${d.returns.qty.toLocaleString()}</div>
        <div style="color:var(--text-muted);font-size:0.85rem">units across ${d.returns.count} returns</div>
      </div>
    </div>`;
}

async function loadSKUReport() {
  const res = await API.get("/reports/sku");
  if (!res?.success) return;

  document.getElementById("skuReportData").innerHTML = `
    <table id="skuReportTable">
      <thead><tr>
        <th>Part Name</th><th>Ref</th><th>Category</th><th>Package</th>
        <th>Total In</th><th>Available</th><th>Allocated</th><th>Value (₹)</th><th>Status</th>
      </tr></thead>
      <tbody>
        ${res.data.map(s => `<tr>
          <td>${s.part_name}</td>
          <td>${s.ref_name || "—"}</td>
          <td>${s.category}</td>
          <td>${s.package || "—"}</td>
          <td>${s.total_in}</td>
          <td>${s.total_available}</td>
          <td>${s.total_allocated}</td>
          <td>₹${s.total_value_inr.toLocaleString("en-IN")}</td>
          <td>${s.low_stock ? '<span class="badge badge-warn">⚠ Low</span>' : '<span class="badge badge-ok">OK</span>'}</td>
        </tr>`).join("")}
      </tbody>
    </table>`;
}

async function loadEmployeeReport() {
  const res = await API.get("/reports/employee");
  if (!res?.success) return;

  document.getElementById("empReportData").innerHTML = `
    <table id="empReportTable">
      <thead><tr>
        <th>Employee ID</th><th>Name</th><th>Department</th>
        <th>Total Allocated</th><th>Total Returned</th><th>Outstanding Returnable</th>
      </tr></thead>
      <tbody>
        ${res.data.map(e => `<tr>
          <td class="uid-tag">${e.employee_id}</td>
          <td>${e.name}</td>
          <td>${e.department || "—"}</td>
          <td>${e.total_allocated}</td>
          <td>${e.total_returned}</td>
          <td>${e.outstanding_returnable > 0
            ? `<span class="badge badge-warn">${e.outstanding_returnable}</span>`
            : `<span class="badge badge-ok">0</span>`}</td>
        </tr>`).join("")}
      </tbody>
    </table>`;
}

function exportCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) return showToast("No data to export", "error");
  const rows = Array.from(table.querySelectorAll("tr"));
  const csv = rows.map(row =>
    Array.from(row.querySelectorAll("th,td"))
      .map(cell => `"${cell.textContent.trim().replace(/"/g, '""')}"`)
      .join(",")
  ).join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename + ".csv";
  a.click(); URL.revokeObjectURL(url);
  showToast("CSV exported", "success");
}

// ── Audit Logs ────────────────────────────────────────────────────────────────

async function loadLogs() {
  const action = document.getElementById("logSearch")?.value || "";
  const res = await API.get("/logs?per_page=100&action=" + encodeURIComponent(action));
  if (!res?.success) return;

  document.getElementById("logsTable").innerHTML = renderLogsTable(res.data.logs);
}

function renderLogsTable(logs) {
  if (!logs || logs.length === 0) return `<div class="empty-state">No log entries.</div>`;
  return `<table>
    <thead><tr><th>ID</th><th>User</th><th>Action</th><th>Details</th><th>IP</th><th>Time</th></tr></thead>
    <tbody>
      ${logs.map(l => `<tr>
        <td>${l.id}</td>
        <td>${l.username || "—"}</td>
        <td><span class="badge badge-info">${l.action}</span></td>
        <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis">${l.details || "—"}</td>
        <td style="font-size:0.8rem;color:var(--text-muted)">${l.ip_address || "—"}</td>
        <td style="font-size:0.8rem;color:var(--text-muted)">${l.timestamp?.replace("T"," ").split(".")[0]}</td>
      </tr>`).join("")}
    </tbody>
  </table>`;
}

// ── Admin / User Management ───────────────────────────────────────────────────

async function loadUsers() {
  if (currentUser?.role !== "admin") return;
  const res = await API.get("/auth/users");
  if (!res?.success) return;

  document.getElementById("userTable").innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Created</th><th>Actions</th></tr></thead>
      <tbody>
        ${res.data.map(u => `<tr>
          <td>${u.id}</td>
          <td>${u.username}</td>
          <td><span class="badge ${u.role === 'admin' ? 'badge-danger' : 'badge-info'}">${u.role}</span></td>
          <td style="font-size:0.82rem;color:var(--text-muted)">${u.created_at?.split("T")[0] || "—"}</td>
          <td style="display:flex;gap:0.4rem">
            <button class="btn btn-outline btn-sm" onclick="resetPassword(${u.id}, '${u.username}')">Reset PW</button>
            ${u.id !== currentUser.id ? `<button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, '${u.username}')">Delete</button>` : ""}
          </td>
        </tr>`).join("")}
      </tbody>
    </table>`;
}

async function submitUser() {
  const body = {
    username: val("newUserName"),
    password: val("newUserPass"),
    role: val("newUserRole"),
  };
  if (!body.username || !body.password) return showToast("Username and password required", "error");

  const res = await API.post("/auth/users", body);
  if (!res?.success) return showToast(res?.message || "Error", "error");

  showToast("User created", "success");
  closeModal("modalUser");
  loadUsers();
}

async function resetPassword(uid, username) {
  const newPass = prompt(`New password for ${username}:`);
  if (!newPass) return;
  const res = await API.post(`/auth/users/${uid}/reset-password`, { new_password: newPass });
  if (res?.success) showToast(`Password reset for ${username}`, "success");
  else showToast(res?.message || "Error", "error");
}

async function deleteUser(uid, username) {
  if (!confirm(`Delete user "${username}"? This cannot be undone.`)) return;
  const res = await API.delete(`/auth/users/${uid}`);
  if (res?.success) { showToast("User deleted", "success"); loadUsers(); }
  else showToast(res?.message || "Error", "error");
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function val(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

function openModal(id) {
  document.getElementById(id)?.classList.add("open");
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove("open");
}

function showToast(msg, type = "info") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast show " + (type === "error" ? "error" : type === "success" ? "success" : "");
  setTimeout(() => t.classList.remove("show"), 3500);
}

function renderTable(data, keys, headers, _extraFn) {
  if (!data || data.length === 0) return `<div class="empty-state">No data.</div>`;
  return `<table>
    <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
    <tbody>
      ${data.map(row => `<tr>${keys.map(k => `<td>${row[k] ?? "—"}</td>`).join("")}</tr>`).join("")}
    </tbody>
  </table>`;
}
