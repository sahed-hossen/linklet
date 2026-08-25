const API_BASE = window.location.origin;

let linksCache = [];
let lastCreatedShortUrl = "";

document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("linklet_theme") || "dark";
    setTheme(savedTheme);
    fetchLinks();

    const urlInput = document.getElementById("long-url-input");
    const autoPasteToggle = document.getElementById("auto-paste-toggle");

    urlInput.addEventListener("focus", async () => {
        if (!autoPasteToggle.checked || urlInput.value) return;
        try {
            const text = await navigator.clipboard.readText();
            if (text && /^https?:\/\//i.test(text.trim())) {
                urlInput.value = text.trim();
                showToast("Pasted link from clipboard");
            }
        } catch {
            // Clipboard permission denied or unavailable
        }
    });
});

async function fetchLinks() {
    const tbody = document.getElementById("links-tbody");
    try {
        const res = await fetch(`${API_BASE}/api/links`);
        if (!res.ok) throw new Error();
        linksCache = await res.json();
        renderLinks(linksCache);
    } catch {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center; color: #ef4444; padding: 24px;">
                    Failed to load links from server.
                </td>
            </tr>
        `;
    }
}

function renderLinks(links) {
    const tbody = document.getElementById("links-tbody");
    const countBadge = document.getElementById("links-count-badge");
    if (countBadge) {
        countBadge.innerText = `${links.length} link${links.length === 1 ? '' : 's'}`;
    }

    if (!links.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="table-loading">
                    No links yet. Shorten your first link above.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = links.map(link => {
        const domain = getDomain(link.long_url);
        const favicon = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;
        const statusBadge = link.is_active
            ? `<span class="status-pill active">Active</span>`
            : `<span class="status-pill inactive">Inactive</span>`;

        return `
            <tr>
                <td>
                    <div class="short-link-cell">
                        <a href="${link.short_url}" target="_blank" class="short-link-anchor">${link.short_url}</a>
                        <button class="btn-icon-copy" title="Copy" onclick="copyToClipboard('${link.short_url}')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        </button>
                    </div>
                </td>
                <td>
                    <div class="orig-link-cell">
                        <img src="${favicon}" class="site-favicon" alt="" onerror="this.style.display='none'">
                        <a href="${link.long_url}" target="_blank" class="orig-link-text" title="${link.long_url}">${link.long_url}</a>
                    </div>
                </td>
                <td>
                    <button class="qr-icon-btn" title="QR Code" onclick="openQrModal('${link.short_url}')">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                    </button>
                </td>
                <td><span class="clicks-count">${link.click_count.toLocaleString()}</span></td>
                <td>${statusBadge}</td>
                <td class="date-cell">${formatDate(link.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn-action-stats" onclick="openAnalyticsModal('${link.short_code}')">Stats</button>
                        ${link.is_active ? `<button class="btn-action-del" title="Deactivate" onclick="deleteLink('${link.short_code}')">🗑️</button>` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

async function handleShorten(event) {
    event.preventDefault();
    const urlInput = document.getElementById("long-url-input");
    const aliasInput = document.getElementById("custom-alias-input");
    const expiryInput = document.getElementById("expiry-date-input");
    const submitBtn = document.getElementById("shorten-btn");

    const long_url = urlInput.value.trim();
    if (!long_url) return;

    const payload = { long_url };
    if (aliasInput.value.trim()) payload.custom_alias = aliasInput.value.trim();
    if (expiryInput.value) payload.expires_at = new Date(expiryInput.value).toISOString();

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Shortening...</span>`;

        const res = await fetch(`${API_BASE}/shorten`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.status === 201) {
            lastCreatedShortUrl = data.short_url;
            document.getElementById("result-short-url").innerText = data.short_url;
            document.getElementById("result-banner").classList.add("active");
            urlInput.value = "";
            aliasInput.value = "";
            expiryInput.value = "";
            showToast("Short link created");
            fetchLinks();
        } else {
            showToast(data.detail || "Failed to shorten URL");
        }
    } catch {
        showToast("Network error. Backend unreachable.");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Shorten</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>`;
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast("Copied to clipboard");
    }).catch(() => {
        showToast("Could not copy link");
    });
}

function copyResultLink() {
    if (lastCreatedShortUrl) copyToClipboard(lastCreatedShortUrl);
}

async function deleteLink(code) {
    if (!confirm(`Deactivate /${code}?`)) return;

    try {
        const res = await fetch(`${API_BASE}/api/links/${code}`, { method: "DELETE" });
        if (res.ok) {
            showToast(`/${code} deactivated`);
            fetchLinks();
        } else {
            showToast("Failed to deactivate");
        }
    } catch {
        showToast("Network error");
    }
}

function openQrModal(url) {
    document.getElementById("qr-modal-url").innerText = url;
    const canvas = document.getElementById("qr-code-canvas");
    canvas.innerHTML = "";
    new QRCode(canvas, {
        text: url,
        width: 180,
        height: 180,
        colorDark: "#0B101B",
        colorLight: "#FFFFFF",
        correctLevel: QRCode.CorrectLevel.H
    });
    document.getElementById("qr-modal").classList.add("open");
}

function openQrModalFromResult() {
    if (lastCreatedShortUrl) openQrModal(lastCreatedShortUrl);
}

function closeQrModal() {
    document.getElementById("qr-modal").classList.remove("open");
}

async function openAnalyticsModal(code) {
    try {
        const res = await fetch(`${API_BASE}/api/links/${code}/stats`);
        if (!res.ok) throw new Error();
        const stats = await res.json();

        document.getElementById("stats-short-code").innerText = `/${stats.short_code} Analytics`;
        document.getElementById("stats-long-url").innerText = stats.long_url;
        document.getElementById("stats-total-clicks").innerText = stats.click_count.toLocaleString();
        document.getElementById("stats-status").innerHTML = stats.is_active
            ? `<span style="color:#10b981;">Active</span>`
            : `<span style="color:#ef4444;">Deactivated</span>`;
        document.getElementById("stats-created-at").innerText = formatDate(stats.created_at);

        const logs = document.getElementById("stats-click-logs");
        if (stats.recent_clicks && stats.recent_clicks.length) {
            logs.innerHTML = stats.recent_clicks.map(c => `
                <div class="log-row">
                    <span class="log-time">${formatDate(c.clicked_at)}</span>
                    <span class="log-ref">${c.referrer || 'Direct Visit'}</span>
                </div>
            `).join("");
        } else {
            logs.innerHTML = `<div class="log-empty">No clicks recorded yet.</div>`;
        }

        document.getElementById("analytics-modal").classList.add("open");
    } catch {
        showToast("Failed to load statistics");
    }
}

function closeAnalyticsModal() {
    document.getElementById("analytics-modal").classList.remove("open");
}

function filterLinks(query) {
    const q = query.toLowerCase().trim();
    if (!q) return renderLinks(linksCache);

    const filtered = linksCache.filter(l =>
        l.short_code.toLowerCase().includes(q) ||
        l.long_url.toLowerCase().includes(q) ||
        l.short_url.toLowerCase().includes(q)
    );
    renderLinks(filtered);
}

function toggleExtraOptions() {
    document.getElementById("extra-options-panel").classList.toggle("open");
}

function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("linklet_theme", theme);
    const lightBtn = document.getElementById("btn-theme-light");
    const darkBtn = document.getElementById("btn-theme-dark");
    if (lightBtn) lightBtn.classList.toggle("active", theme === "light");
    if (darkBtn) darkBtn.classList.toggle("active", theme === "dark");
}

let toastTimer = null;
function showToast(msg) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function getDomain(urlStr) {
    try {
        return new URL(urlStr).hostname;
    } catch {
        return "example.com";
    }
}

function formatDate(isoStr) {
    if (!isoStr) return "-";
    const d = new Date(isoStr);
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return `${months[d.getUTCMonth()]} ${String(d.getUTCDate()).padStart(2, "0")}, ${d.getUTCFullYear()}`;
}
