/**
 * BILLMASTER - FRONTEND APPLICATION JAVASCRIPT
 * Clean Enterprise UI, Currency Selector (Default INR ₹), Rich Toast Notifications & Custom Modals
 */

const state = {
  currency: localStorage.getItem('billmaster_currency') || '₹',
  settings: {},
  clients: [],
  products: [],
  invoices: [],
  payments: [],
  analytics: null,
  currentTab: 'dashboard',
  invoiceFilter: 'ALL',
  revenueChart: null,
  statusChart: null,
};

// Document Ready
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initCurrencySelector();
  setupEventListeners();
  await loadSettings();
  await refreshAllData();
  switchView('dashboard');
});

/* ==========================================================================
   CURRENCY MANAGEMENT (DEFAULT INR ₹)
   ========================================================================== */
function initCurrencySelector() {
  const saved = localStorage.getItem('billmaster_currency') || '₹';
  state.currency = saved;
  const select = document.getElementById('app-currency-selector');
  if (select) {
    select.value = saved;
  }
  updateCurrencyDisplay();
}

function changeCurrency(newCurrency) {
  state.currency = newCurrency;
  localStorage.setItem('billmaster_currency', newCurrency);
  updateCurrencyDisplay();
  
  // Re-render UI with new currency
  renderDashboard();
  renderInvoicesTable();
  renderClientsTable();
  renderProductsTable();
  renderPaymentsTable();
  calculateInvoiceModalTotals();

  showToast({
    title: 'Currency Updated',
    message: `Display currency set to ${newCurrency.trim()}`,
    type: 'info'
  });
}

function updateCurrencyDisplay() {
  document.querySelectorAll('.app-currency').forEach(el => {
    el.textContent = state.currency.trim();
  });
}

/* ==========================================================================
   THEME TOGGLE (CLEAN LIGHT DEFAULT)
   ========================================================================== */
function initTheme() {
  const saved = localStorage.getItem('billmaster_theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('billmaster_theme', next);
  updateThemeIcon(next);
  if (state.revenueChart) renderCharts();
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  }
}

/* ==========================================================================
   API & DATA FETCHING
   ========================================================================== */
async function apiRequest(endpoint, method = 'GET', data = null) {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (data) options.body = JSON.stringify(data);
    
    const response = await fetch(endpoint, options);
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Server Error' }));
      throw new Error(err.detail || `Request failed with status ${response.status}`);
    }
    if (response.status === 204) return null;
    return await response.json();
  } catch (error) {
    showToast({
      title: 'Action Failed',
      message: error.message,
      type: 'error'
    });
    throw error;
  }
}

async function loadSettings() {
  try {
    state.settings = await apiRequest('/api/settings');
    if (!localStorage.getItem('billmaster_currency') && state.settings.currency) {
      state.currency = state.settings.currency;
    }
    initCurrencySelector();
  } catch (e) {
    console.error('Failed to load settings', e);
  }
}

async function refreshAllData() {
  try {
    const [clients, products, invoices, payments, analytics] = await Promise.all([
      apiRequest('/api/clients'),
      apiRequest('/api/products'),
      apiRequest('/api/invoices'),
      apiRequest('/api/payments'),
      apiRequest('/api/analytics/summary'),
    ]);

    state.clients = clients;
    state.products = products;
    state.invoices = invoices;
    state.payments = payments;
    state.analytics = analytics;

    updateClientsDropdown();
    renderDashboard();
    renderInvoicesTable();
    renderClientsTable();
    renderProductsTable();
    renderPaymentsTable();
  } catch (err) {
    console.error('Error refreshing data:', err);
  }
}

/* ==========================================================================
   VIEW NAVIGATION
   ========================================================================== */
function switchView(viewId) {
  state.currentTab = viewId;
  
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-view') === viewId);
  });

  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });
  const target = document.getElementById(`view-${viewId}`);
  if (target) target.classList.add('active');

  const titleMap = {
    dashboard: { title: 'Financial Dashboard', sub: 'Overview of billing metrics, revenue, and active invoices' },
    invoices: { title: 'Invoices & Billing', sub: 'Manage, generate, and track invoices and receivables' },
    clients: { title: 'Client Directory', sub: 'Manage accounts, contact information, and billing balances' },
    products: { title: 'Products & Services', sub: 'Configure catalog rates, units, and taxation rules' },
    payments: { title: 'Payment History', sub: 'Record and track transaction receipts and settlements' }
  };

  const meta = titleMap[viewId] || { title: 'Billing System', sub: '' };
  document.getElementById('current-page-title').textContent = meta.title;
  document.getElementById('current-page-sub').textContent = meta.sub;

  if (viewId === 'dashboard') {
    renderDashboard();
  }
}

/* ==========================================================================
   DASHBOARD RENDERING (CLEAN AESTHETICS)
   ========================================================================== */
function renderDashboard() {
  if (!state.analytics) return;
  const a = state.analytics;

  document.getElementById('kpi-revenue').textContent = formatCurrency(a.total_revenue);
  document.getElementById('kpi-invoiced').textContent = formatCurrency(a.total_invoiced);
  document.getElementById('kpi-due').textContent = formatCurrency(a.outstanding_receivables);
  document.getElementById('kpi-overdue').textContent = formatCurrency(a.overdue_amount);

  renderCharts();
  renderRecentInvoices(a.recent_invoices);
}

function renderCharts() {
  if (!state.analytics) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#9ca3af' : '#64748b';
  const gridColor = isDark ? '#1f2937' : '#f1f5f9';

  // 1. Monthly Revenue Chart
  const revCtx = document.getElementById('revenueChart');
  if (revCtx) {
    if (state.revenueChart) state.revenueChart.destroy();
    
    const labels = state.analytics.monthly_trend.map(m => m.month);
    const billedData = state.analytics.monthly_trend.map(m => m.billed);
    const receivedData = state.analytics.monthly_trend.map(m => m.received);

    state.revenueChart = new Chart(revCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Invoiced',
            data: billedData,
            backgroundColor: '#2563eb',
            borderRadius: 4,
            barPercentage: 0.6,
          },
          {
            label: 'Received',
            data: receivedData,
            backgroundColor: '#16a34a',
            borderRadius: 4,
            barPercentage: 0.6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            position: 'top',
            labels: { color: textColor, font: { family: 'Inter', size: 12 }, boxWidth: 12 }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
            }
          }
        },
        scales: {
          x: { ticks: { color: textColor, font: { size: 12 } }, grid: { display: false } },
          y: { 
            ticks: { color: textColor, font: { size: 12 }, callback: (v) => `${state.currency} ${v}` }, 
            grid: { color: gridColor } 
          }
        }
      }
    });
  }

  // 2. Invoice Status Distribution Chart
  const statCtx = document.getElementById('statusChart');
  if (statCtx) {
    if (state.statusChart) state.statusChart.destroy();
    
    const statuses = state.analytics.invoices_by_status;
    const labels = Object.keys(statuses);
    const data = Object.values(statuses);

    const colors = {
      PAID: '#16a34a',
      PARTIAL: '#d97706',
      SENT: '#2563eb',
      OVERDUE: '#dc2626',
      DRAFT: '#64748b'
    };

    state.statusChart = new Chart(statCtx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: labels.map(l => colors[l] || '#94a3b8'),
          borderWidth: 2,
          borderColor: isDark ? '#111827' : '#ffffff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { position: 'bottom', labels: { color: textColor, boxWidth: 10, padding: 12, font: { size: 11 } } }
        }
      }
    });
  }
}

function renderRecentInvoices(invoices) {
  const tbody = document.getElementById('recent-invoices-tbody');
  if (!tbody) return;
  if (!invoices || invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted);">No invoices generated yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices.map(inv => `
    <tr>
      <td><strong>${inv.invoice_number}</strong></td>
      <td>${escapeHtml(inv.client_name)}</td>
      <td>${formatDate(inv.issue_date)}</td>
      <td><strong>${formatCurrency(inv.total_amount)}</strong></td>
      <td>${getStatusBadge(inv.status)}</td>
      <td style="text-align: right;">
        <button class="btn btn-secondary btn-sm" onclick="viewInvoiceDetails(${inv.id})"><i class="fas fa-eye"></i></button>
        <a href="/invoices/${inv.id}/print?currency=${encodeURIComponent(state.currency)}" target="_blank" class="btn btn-secondary btn-sm"><i class="fas fa-print"></i></a>
      </td>
    </tr>
  `).join('');
}

/* ==========================================================================
   INVOICES VIEW & TABLE
   ========================================================================== */
function filterInvoices(statusFilter) {
  state.invoiceFilter = statusFilter;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-status') === statusFilter);
  });
  renderInvoicesTable();
}

function renderInvoicesTable() {
  const tbody = document.getElementById('invoices-table-tbody');
  if (!tbody) return;

  const search = (document.getElementById('invoice-search-input')?.value || '').toLowerCase();
  
  let list = state.invoices;
  if (state.invoiceFilter !== 'ALL') {
    list = list.filter(i => i.status === state.invoiceFilter);
  }
  if (search) {
    list = list.filter(i => 
      i.invoice_number.toLowerCase().includes(search) ||
      (i.client_name && i.client_name.toLowerCase().includes(search)) ||
      (i.client_company && i.client_company.toLowerCase().includes(search))
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-muted);">No invoices match your filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(inv => `
    <tr>
      <td><strong>${inv.invoice_number}</strong></td>
      <td>
        <div style="font-weight:600;">${escapeHtml(inv.client_name)}</div>
        <div style="font-size:12px;color:var(--text-muted);">${escapeHtml(inv.client_company || '')}</div>
      </td>
      <td>${formatDate(inv.issue_date)}</td>
      <td>${formatDate(inv.due_date)}</td>
      <td><strong>${formatCurrency(inv.total_amount)}</strong></td>
      <td style="color:${inv.balance_due > 0 ? 'var(--warning-text)' : 'var(--success-text)'};font-weight:600;">
        ${formatCurrency(inv.balance_due)}
      </td>
      <td>${getStatusBadge(inv.status)}</td>
      <td>
        <div style="display:flex;gap:6px;justify-content:flex-end;">
          <button class="btn btn-secondary btn-sm" title="View Details" onclick="viewInvoiceDetails(${inv.id})">
            <i class="fas fa-eye"></i>
          </button>
          <a href="/invoices/${inv.id}/print?currency=${encodeURIComponent(state.currency)}" target="_blank" class="btn btn-secondary btn-sm" title="Print / PDF">
            <i class="fas fa-print"></i>
          </a>
          ${inv.balance_due > 0 && inv.status !== 'CANCELLED' ? `
            <button class="btn btn-success btn-sm" title="Record Payment" onclick="openPaymentModalForInvoice(${inv.id})">
              <i class="fas fa-check"></i> Pay
            </button>
          ` : ''}
          <button class="btn btn-danger btn-sm" title="Delete" onclick="deleteInvoice(${inv.id})">
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

/* ==========================================================================
   CLIENTS VIEW
   ========================================================================== */
function renderClientsTable() {
  const tbody = document.getElementById('clients-table-tbody');
  if (!tbody) return;

  const search = (document.getElementById('client-search-input')?.value || '').toLowerCase();
  let list = state.clients;
  if (search) {
    list = list.filter(c => 
      c.name.toLowerCase().includes(search) ||
      (c.company && c.company.toLowerCase().includes(search)) ||
      (c.email && c.email.toLowerCase().includes(search))
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--text-muted);">No clients found. Click "+ Add Client" to create one.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(c => `
    <tr>
      <td>
        <div style="font-weight:600;">${escapeHtml(c.name)}</div>
        <div style="font-size:12px;color:var(--text-muted);">${escapeHtml(c.company || 'Individual')}</div>
      </td>
      <td>${escapeHtml(c.email || '-')}</td>
      <td>${escapeHtml(c.phone || '-')}</td>
      <td><strong>${formatCurrency(c.total_invoiced || 0)}</strong></td>
      <td style="color:var(--success-text);font-weight:600;">${formatCurrency(c.total_paid || 0)}</td>
      <td style="color:${(c.balance_due || 0) > 0 ? 'var(--danger-text)' : 'var(--text-muted)'};font-weight:600;">
        ${formatCurrency(c.balance_due || 0)}
      </td>
      <td style="text-align:right;">
        <button class="btn btn-secondary btn-sm" onclick="filterInvoicesByClient(${c.id})" title="View Invoices">
          Invoices (${c.invoice_count || 0})
        </button>
        <button class="btn btn-danger btn-sm" onclick="deleteClient(${c.id})" title="Delete Client">
          <i class="fas fa-trash-alt"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

function filterInvoicesByClient(clientId) {
  switchView('invoices');
  const client = state.clients.find(c => c.id === clientId);
  if (client) {
    const searchInput = document.getElementById('invoice-search-input');
    if (searchInput) searchInput.value = client.name;
    renderInvoicesTable();
  }
}

/* ==========================================================================
   PRODUCTS VIEW
   ========================================================================== */
function renderProductsTable() {
  const tbody = document.getElementById('products-table-tbody');
  if (!tbody) return;

  const search = (document.getElementById('product-search-input')?.value || '').toLowerCase();
  let list = state.products;
  if (search) {
    list = list.filter(p => 
      p.name.toLowerCase().includes(search) ||
      (p.sku && p.sku.toLowerCase().includes(search)) ||
      (p.description && p.description.toLowerCase().includes(search))
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-muted);">No products or services found.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(p => `
    <tr>
      <td><code>${escapeHtml(p.sku || '-')}</code></td>
      <td>
        <div style="font-weight:600;">${escapeHtml(p.name)}</div>
        <div style="font-size:12px;color:var(--text-muted);">${escapeHtml(p.description || '')}</div>
      </td>
      <td><span class="badge" style="background:var(--bg-muted);">${escapeHtml(p.unit)}</span></td>
      <td><strong>${formatCurrency(p.unit_price)}</strong></td>
      <td>${p.tax_rate}%</td>
      <td style="text-align:right;">
        <button class="btn btn-danger btn-sm" onclick="deleteProduct(${p.id})">
          <i class="fas fa-trash-alt"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

/* ==========================================================================
   PAYMENTS VIEW
   ========================================================================== */
function renderPaymentsTable() {
  const tbody = document.getElementById('payments-table-tbody');
  if (!tbody) return;

  if (state.payments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--text-muted);">No payments recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.payments.map(pay => `
    <tr>
      <td>${formatDate(pay.payment_date)}</td>
      <td><strong>${pay.invoice_number}</strong></td>
      <td>${escapeHtml(pay.client_name)}</td>
      <td><span class="badge" style="background:var(--bg-muted);">${pay.payment_method.replace('_', ' ')}</span></td>
      <td><code>${escapeHtml(pay.reference_number || '-')}</code></td>
      <td><span style="font-size:12px;color:var(--text-muted);">${escapeHtml(pay.notes || '-')}</span></td>
      <td style="color:var(--success-text);font-weight:700;text-align:right;">+${formatCurrency(pay.amount)}</td>
    </tr>
  `).join('');
}

/* ==========================================================================
   INVOICE BUILDER (MODAL & LIVE CALCULATIONS)
   ========================================================================== */
function openNewInvoiceModal() {
  document.getElementById('form-new-invoice').reset();
  
  const today = new Date().toISOString().split('T')[0];
  const due = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0];
  document.getElementById('inv-issue-date').value = today;
  document.getElementById('inv-due-date').value = due;

  const container = document.getElementById('invoice-items-tbody');
  container.innerHTML = '';
  addInvoiceLineItem();

  calculateInvoiceModalTotals();
  openModal('modal-invoice');
}

function updateClientsDropdown() {
  const select = document.getElementById('inv-client-select');
  if (!select) return;
  select.innerHTML = '<option value="">-- Select Client --</option>' + 
    state.clients.map(c => `
      <option value="${c.id}">${escapeHtml(c.name)} ${c.company ? `(${escapeHtml(c.company)})` : ''}</option>
    `).join('');
}

function addInvoiceLineItem(productId = null) {
  const container = document.getElementById('invoice-items-tbody');
  const rowId = 'row-' + Date.now() + '-' + Math.random().toString(36).substring(2, 5);

  const tr = document.createElement('tr');
  tr.id = rowId;
  tr.className = 'invoice-line-row';

  tr.innerHTML = `
    <td>
      <select class="input-field line-product-select" onchange="onProductSelected('${rowId}')">
        <option value="">-- Custom Item --</option>
        ${state.products.map(p => `<option value="${p.id}" ${productId == p.id ? 'selected' : ''}>${escapeHtml(p.name)} (${formatCurrency(p.unit_price)})</option>`).join('')}
      </select>
      <input type="text" class="input-field line-description" placeholder="Description of service/product" style="margin-top:6px;" required>
    </td>
    <td style="width: 85px;">
      <input type="number" class="input-field line-qty" value="1" min="0.01" step="any" oninput="calculateInvoiceModalTotals()" required>
    </td>
    <td style="width: 110px;">
      <input type="number" class="input-field line-price" value="0.00" min="0" step="any" oninput="calculateInvoiceModalTotals()" required>
    </td>
    <td style="width: 85px;">
      <input type="number" class="input-field line-tax" value="${state.settings.default_tax_rate || 18}" min="0" max="100" step="any" oninput="calculateInvoiceModalTotals()">
    </td>
    <td style="width: 85px;">
      <input type="number" class="input-field line-disc" value="0" min="0" max="100" step="any" oninput="calculateInvoiceModalTotals()">
    </td>
    <td style="width: 110px; font-weight: 600; text-align: right;" class="line-total-cell">
      ${state.currency} 0.00
    </td>
    <td style="width: 36px; text-align: center;">
      <button type="button" class="btn btn-danger btn-sm" onclick="removeInvoiceLineItem('${rowId}')"><i class="fas fa-times"></i></button>
    </td>
  `;

  container.appendChild(tr);

  if (productId) {
    onProductSelected(rowId);
  }
}

function removeInvoiceLineItem(rowId) {
  const row = document.getElementById(rowId);
  if (row) {
    row.remove();
    calculateInvoiceModalTotals();
  }
}

function onProductSelected(rowId) {
  const row = document.getElementById(rowId);
  if (!row) return;

  const select = row.querySelector('.line-product-select');
  const prodId = select.value;
  if (!prodId) return;

  const product = state.products.find(p => p.id == prodId);
  if (product) {
    row.querySelector('.line-description').value = product.name + (product.description ? ` - ${product.description}` : '');
    row.querySelector('.line-price').value = product.unit_price.toFixed(2);
    row.querySelector('.line-tax').value = product.tax_rate;
    calculateInvoiceModalTotals();
  }
}

function calculateInvoiceModalTotals() {
  const rows = document.querySelectorAll('.invoice-line-row');
  let subtotal = 0;
  let totalTax = 0;

  rows.forEach(row => {
    const qty = parseFloat(row.querySelector('.line-qty').value) || 0;
    const price = parseFloat(row.querySelector('.line-price').value) || 0;
    const taxRate = parseFloat(row.querySelector('.line-tax').value) || 0;
    const discRate = parseFloat(row.querySelector('.line-disc').value) || 0;

    const raw = qty * price;
    const itemDisc = raw * (discRate / 100);
    const taxable = Math.max(0, raw - itemDisc);
    const itemTax = taxable * (taxRate / 100);
    const lineTotal = taxable + itemTax;

    row.querySelector('.line-total-cell').textContent = formatCurrency(lineTotal);
    subtotal += raw;
    totalTax += itemTax;
  });

  const discType = document.getElementById('inv-discount-type')?.value || 'PERCENTAGE';
  const discVal = parseFloat(document.getElementById('inv-discount-val')?.value) || 0;

  let overallDisc = 0;
  if (discType === 'PERCENTAGE') {
    overallDisc = subtotal * (discVal / 100);
  } else {
    overallDisc = Math.min(discVal, subtotal);
  }

  const grandTotal = Math.max(0, subtotal - overallDisc + totalTax);

  document.getElementById('modal-calc-subtotal').textContent = formatCurrency(subtotal);
  document.getElementById('modal-calc-tax').textContent = formatCurrency(totalTax);
  document.getElementById('modal-calc-discount').textContent = formatCurrency(overallDisc);
  document.getElementById('modal-calc-total').textContent = formatCurrency(grandTotal);
}

async function handleCreateInvoice(e) {
  e.preventDefault();

  const clientId = document.getElementById('inv-client-select').value;
  if (!clientId) {
    showToast({ title: 'Validation Error', message: 'Please select a client', type: 'warning' });
    return;
  }

  const rows = document.querySelectorAll('.invoice-line-row');
  if (rows.length === 0) {
    showToast({ title: 'Validation Error', message: 'Please add at least one line item', type: 'warning' });
    return;
  }

  const items = [];
  for (const row of rows) {
    const desc = row.querySelector('.line-description').value.trim();
    if (!desc) {
      showToast({ title: 'Validation Error', message: 'Each line item must have a description', type: 'warning' });
      return;
    }
    items.push({
      product_id: parseInt(row.querySelector('.line-product-select').value) || null,
      description: desc,
      quantity: parseFloat(row.querySelector('.line-qty').value) || 1,
      unit_price: parseFloat(row.querySelector('.line-price').value) || 0,
      tax_rate: parseFloat(row.querySelector('.line-tax').value) || 0,
      discount: parseFloat(row.querySelector('.line-disc').value) || 0,
    });
  }

  const payload = {
    client_id: parseInt(clientId),
    issue_date: document.getElementById('inv-issue-date').value,
    due_date: document.getElementById('inv-due-date').value,
    discount_type: document.getElementById('inv-discount-type').value,
    discount_value: parseFloat(document.getElementById('inv-discount-val').value) || 0,
    payment_terms: document.getElementById('inv-payment-terms').value,
    notes: document.getElementById('inv-notes').value,
    items: items,
  };

  try {
    const created = await apiRequest('/api/invoices', 'POST', payload);
    showToast({
      title: 'Invoice Generated',
      message: `Invoice ${created.invoice_number} created with total of ${formatCurrency(created.total_amount)}`,
      type: 'success'
    });
    closeModal('modal-invoice');
    await refreshAllData();
    switchView('invoices');
  } catch (err) {
    console.error(err);
  }
}

/* ==========================================================================
   PAYMENT MODAL & RECORDING
   ========================================================================== */
function openPaymentModalForInvoice(invoiceId) {
  const inv = state.invoices.find(i => i.id === invoiceId);
  if (!inv) return;

  document.getElementById('pay-invoice-id').value = inv.id;
  document.getElementById('pay-invoice-number').value = inv.invoice_number;
  document.getElementById('pay-client-name').value = inv.client_name;
  document.getElementById('pay-balance-due-text').textContent = formatCurrency(inv.balance_due);
  document.getElementById('pay-amount').value = inv.balance_due.toFixed(2);
  document.getElementById('pay-amount').max = inv.balance_due;
  document.getElementById('pay-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('pay-ref').value = '';
  document.getElementById('pay-notes').value = '';

  openModal('modal-payment');
}

async function handleRecordPayment(e) {
  e.preventDefault();

  const invoiceId = parseInt(document.getElementById('pay-invoice-id').value);
  const amount = parseFloat(document.getElementById('pay-amount').value);

  const payload = {
    invoice_id: invoiceId,
    amount: amount,
    payment_date: document.getElementById('pay-date').value,
    payment_method: document.getElementById('pay-method').value,
    reference_number: document.getElementById('pay-ref').value.trim() || null,
    notes: document.getElementById('pay-notes').value.trim() || null,
  };

  try {
    const res = await apiRequest('/api/payments', 'POST', payload);
    showToast({
      title: 'Payment Recorded',
      message: `Received ${formatCurrency(res.amount)} via ${res.payment_method.replace('_', ' ')}`,
      type: 'success'
    });
    closeModal('modal-payment');
    await refreshAllData();
  } catch (err) {
    console.error(err);
  }
}

/* ==========================================================================
   CLIENT & PRODUCT CREATION MODALS
   ========================================================================== */
async function handleCreateClient(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('client-name').value.trim(),
    company: document.getElementById('client-company').value.trim() || null,
    email: document.getElementById('client-email').value.trim() || null,
    phone: document.getElementById('client-phone').value.trim() || null,
    address: document.getElementById('client-address').value.trim() || null,
    tax_id: document.getElementById('client-tax-id').value.trim() || null,
  };

  try {
    const client = await apiRequest('/api/clients', 'POST', payload);
    showToast({
      title: 'Client Added',
      message: `"${client.name}" registered to client directory`,
      type: 'success'
    });
    closeModal('modal-client');
    await refreshAllData();
  } catch (err) {
    console.error(err);
  }
}

async function handleCreateProduct(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('prod-name').value.trim(),
    sku: document.getElementById('prod-sku').value.trim() || null,
    unit_price: parseFloat(document.getElementById('prod-price').value) || 0,
    tax_rate: parseFloat(document.getElementById('prod-tax').value) || 0,
    unit: document.getElementById('prod-unit').value.trim() || 'item',
    description: document.getElementById('prod-desc').value.trim() || null,
  };

  try {
    const prod = await apiRequest('/api/products', 'POST', payload);
    showToast({
      title: 'Product Saved',
      message: `"${prod.name}" added to catalog (${formatCurrency(prod.unit_price)})`,
      type: 'success'
    });
    closeModal('modal-product');
    await refreshAllData();
  } catch (err) {
    console.error(err);
  }
}

/* ==========================================================================
   INVOICE DETAILS MODAL
   ========================================================================== */
async function viewInvoiceDetails(invoiceId) {
  try {
    const inv = await apiRequest(`/api/invoices/${invoiceId}`);
    
    document.getElementById('detail-inv-num').textContent = inv.invoice_number;
    document.getElementById('detail-status-badge').innerHTML = getStatusBadge(inv.status);
    document.getElementById('detail-client-name').textContent = inv.client.name;
    document.getElementById('detail-client-comp').textContent = inv.client.company || '';
    document.getElementById('detail-client-email').textContent = inv.client.email || '';
    document.getElementById('detail-issue-date').textContent = formatDate(inv.issue_date);
    document.getElementById('detail-due-date').textContent = formatDate(inv.due_date);
    document.getElementById('detail-terms').textContent = inv.payment_terms;

    const tbody = document.getElementById('detail-items-tbody');
    tbody.innerHTML = inv.items.map(item => `
      <tr>
        <td>${escapeHtml(item.description)}</td>
        <td>${item.quantity}</td>
        <td>${formatCurrency(item.unit_price)}</td>
        <td>${item.tax_rate}%</td>
        <td>${item.discount}%</td>
        <td style="text-align:right;font-weight:600;">${formatCurrency(item.line_total)}</td>
      </tr>
    `).join('');

    document.getElementById('detail-subtotal').textContent = formatCurrency(inv.subtotal);
    document.getElementById('detail-discount').textContent = formatCurrency(inv.discount_amount);
    document.getElementById('detail-tax').textContent = formatCurrency(inv.tax_amount);
    document.getElementById('detail-total').textContent = formatCurrency(inv.total_amount);
    document.getElementById('detail-paid').textContent = formatCurrency(inv.paid_amount);
    document.getElementById('detail-balance').textContent = formatCurrency(inv.balance_due);

    const payContainer = document.getElementById('detail-payments-container');
    if (inv.payments && inv.payments.length > 0) {
      payContainer.innerHTML = inv.payments.map(p => `
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-color);font-size:13px;">
          <span>${formatDate(p.payment_date)} via <strong>${p.payment_method.replace('_', ' ')}</strong> ${p.reference_number ? `(${p.reference_number})` : ''}</span>
          <span style="color:var(--success-text);font-weight:600;">+${formatCurrency(p.amount)}</span>
        </div>
      `).join('');
    } else {
      payContainer.innerHTML = `<p style="font-size:13px;color:var(--text-muted);padding:4px 0;">No payments recorded yet.</p>`;
    }

    document.getElementById('detail-print-btn').href = `/invoices/${inv.id}/print?currency=${encodeURIComponent(state.currency)}`;

    openModal('modal-invoice-details');
  } catch (err) {
    console.error(err);
  }
}

/* ==========================================================================
   DELETIONS & DEMO SEED WITH IN-APP CONFIRMATION MODAL
   ========================================================================== */
function deleteInvoice(invoiceId) {
  const inv = state.invoices.find(i => i.id === invoiceId);
  const invNum = inv ? inv.invoice_number : `#${invoiceId}`;

  showConfirmDialog({
    title: `Delete Invoice ${invNum}?`,
    message: 'Are you sure you want to delete this invoice? All recorded line items and payments will be permanently removed.',
    confirmText: 'Delete Invoice',
    confirmClass: 'btn-danger',
    icon: 'fa-trash-alt',
    iconType: 'danger',
    onConfirm: async () => {
      try {
        await apiRequest(`/api/invoices/${invoiceId}`, 'DELETE');
        showToast({
          title: 'Invoice Deleted',
          message: `Invoice ${invNum} has been permanently deleted`,
          type: 'delete'
        });
        await refreshAllData();
      } catch (err) {
        console.error(err);
      }
    }
  });
}

function deleteClient(clientId) {
  const client = state.clients.find(c => c.id === clientId);
  const clientName = client ? client.name : 'this client';

  showConfirmDialog({
    title: `Delete Client "${clientName}"?`,
    message: 'Are you sure? Deleting this client will also delete all of their past invoices, line items, and recorded payments.',
    confirmText: 'Delete Client',
    confirmClass: 'btn-danger',
    icon: 'fa-user-slash',
    iconType: 'danger',
    onConfirm: async () => {
      try {
        await apiRequest(`/api/clients/${clientId}`, 'DELETE');
        showToast({
          title: 'Client Deleted',
          message: `Client "${clientName}" and billing history removed`,
          type: 'delete'
        });
        await refreshAllData();
      } catch (err) {
        console.error(err);
      }
    }
  });
}

function deleteProduct(productId) {
  const prod = state.products.find(p => p.id === productId);
  const prodName = prod ? prod.name : 'this product';

  showConfirmDialog({
    title: `Deactivate "${prodName}"?`,
    message: 'This item or service will be deactivated and removed from future invoice selection.',
    confirmText: 'Deactivate Item',
    confirmClass: 'btn-danger',
    icon: 'fa-archive',
    iconType: 'warning',
    onConfirm: async () => {
      try {
        await apiRequest(`/api/products/${productId}`, 'DELETE');
        showToast({
          title: 'Product Deactivated',
          message: `"${prodName}" has been deactivated from active catalog`,
          type: 'delete'
        });
        await refreshAllData();
      } catch (err) {
        console.error(err);
      }
    }
  });
}

function triggerDatabaseSeed() {
  showConfirmDialog({
    title: 'Seed Sample Data?',
    message: 'This will populate realistic demo clients, catalog services, invoices, and payments directly into PostgreSQL.',
    confirmText: 'Seed Records',
    confirmClass: 'btn-primary',
    icon: 'fa-database',
    iconType: 'warning',
    onConfirm: async () => {
      try {
        const res = await apiRequest('/api/seed', 'POST');
        showToast({
          title: 'Database Seeded',
          message: res.message,
          type: 'success'
        });
        await refreshAllData();
      } catch (err) {
        console.error(err);
      }
    }
  });
}

/* ==========================================================================
   CUSTOM IN-APP CONFIRMATION DIALOG CONTROLLER
   ========================================================================== */
function showConfirmDialog({ title, message, confirmText = 'Confirm', confirmClass = 'btn-danger', icon = 'fa-trash-alt', iconType = 'danger', onConfirm }) {
  const modal = document.getElementById('modal-confirm');
  const titleEl = document.getElementById('confirm-title');
  const msgEl = document.getElementById('confirm-message');
  const iconBoxEl = document.getElementById('confirm-icon-box');
  const iconEl = document.getElementById('confirm-icon');
  const btnEl = document.getElementById('confirm-action-btn');

  if (titleEl) titleEl.textContent = title;
  if (msgEl) msgEl.textContent = message;
  if (btnEl) {
    btnEl.textContent = confirmText;
    btnEl.className = `btn ${confirmClass}`;
  }
  if (iconEl) iconEl.className = `fas ${icon}`;
  if (iconBoxEl) iconBoxEl.className = `confirm-icon-wrap confirm-icon-${iconType}`;

  if (btnEl) {
    btnEl.onclick = async () => {
      closeModal('modal-confirm');
      if (onConfirm) await onConfirm();
    };
  }

  openModal('modal-confirm');
}

/* ==========================================================================
   MODAL UTILITIES & EVENT LISTENERS
   ========================================================================== */
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('active');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
}

function setupEventListeners() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const view = item.getAttribute('data-view');
      if (view) switchView(view);
    });
  });

  document.getElementById('form-new-invoice')?.addEventListener('submit', handleCreateInvoice);
  document.getElementById('form-record-payment')?.addEventListener('submit', handleRecordPayment);
  document.getElementById('form-new-client')?.addEventListener('submit', handleCreateClient);
  document.getElementById('form-new-product')?.addEventListener('submit', handleCreateProduct);

  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  });

  document.getElementById('invoice-search-input')?.addEventListener('input', renderInvoicesTable);
  document.getElementById('client-search-input')?.addEventListener('input', renderClientsTable);
  document.getElementById('product-search-input')?.addEventListener('input', renderProductsTable);
}

/* ==========================================================================
   ENHANCED TOAST COMPONENT (LINEAR / SONNER STYLE)
   ========================================================================== */
function showToast(options, fallbackType = 'success') {
  let title = 'Notification';
  let message = '';
  let type = 'success';

  if (typeof options === 'string') {
    message = options;
    type = fallbackType;
    title = type === 'success' ? 'Success' : 
            (type === 'delete' || type === 'danger' || type === 'error') ? 'Notice' : 
            type === 'info' ? 'Information' : 'Alert';
  } else if (typeof options === 'object') {
    title = options.title || 'Notification';
    message = options.message || '';
    type = options.type || 'success';
  }

  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';

  const iconMap = {
    success: 'check-circle',
    delete: 'trash-alt',
    danger: 'exclamation-circle',
    error: 'times-circle',
    info: 'info-circle',
    warning: 'exclamation-triangle'
  };

  const icon = iconMap[type] || 'check-circle';
  const iconBoxClass = `toast-icon-${type}`;

  toast.innerHTML = `
    <div class="toast-icon-box ${iconBoxClass}">
      <i class="fas fa-${icon}"></i>
    </div>
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
    <button class="toast-close-btn" onclick="this.parentElement.remove()" title="Dismiss">&times;</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

/* ==========================================================================
   FORMATTERS & HELPERS (CURRENCY AWARE)
   ========================================================================== */
function formatCurrency(amount) {
  const cur = state.currency.trim();
  const num = Number(amount || 0);
  
  const locale = (cur === '₹' || cur.includes('INR')) ? 'en-IN' : 'en-US';
  const formattedNumber = num.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  return `${cur} ${formattedNumber}`;
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getStatusBadge(status) {
  const s = (status || '').toUpperCase();
  const map = {
    PAID: 'badge-paid',
    SENT: 'badge-sent',
    PARTIAL: 'badge-partial',
    OVERDUE: 'badge-overdue',
    DRAFT: 'badge-draft',
  };
  return `<span class="badge ${map[s] || 'badge-draft'}">${s}</span>`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
