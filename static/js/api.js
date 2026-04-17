/* ECIMS — API Client
   Auto-detects local vs Render production deployment
*/

const isLocal = window.location.hostname === "localhost" ||
                window.location.hostname === "127.0.0.1" ||
                window.location.protocol === "file:";

const BASE = isLocal
  ? "http://localhost:5000/api"
  : "https://ecims-jarsh-safety.onrender.com/api";

let authToken = localStorage.getItem("ecims_token") || null;

async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" }
  };
  if (authToken) opts.headers["Authorization"] = `Bearer ${authToken}`;
  if (body) opts.body = JSON.stringify(body);

  try {
    const res = await fetch(BASE + path, opts);
    const data = await res.json();

    if (res.status === 401) {
      authToken = null;
      localStorage.removeItem("ecims_token");
      showLogin();
      return null;
    }
    return data;
  } catch (e) {
    showToast("Network error — is the backend running?", "error");
    return null;
  }
}

const API = {
  get: (path) => api("GET", path),
  post: (path, body) => api("POST", path, body),
  put: (path, body) => api("PUT", path, body),
  delete: (path) => api("DELETE", path),
};
