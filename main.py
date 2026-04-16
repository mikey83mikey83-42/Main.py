import logging
import uuid
import json
import os
import httpx
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="East Coast E-Bike Warranty Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR   = Path(__file__).parent
CLAIMS_FILE = BASE_DIR / "claims.json"

# Admin credentials — set via environment variables on Render
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "ebike2024")

# Base44 function URL for email notifications
NOTIFY_URL = os.getenv(
    "NOTIFY_URL",
    "https://bo-c4ded59a.base44.app/functions/sendClaimNotification"
)

security = HTTPBasic()

# ── helpers ──────────────────────────────────────────────────────────────────

def load_claims():
    if CLAIMS_FILE.exists():
        return json.loads(CLAIMS_FILE.read_text())
    return []

def save_claims(claims):
    CLAIMS_FILE.write_text(json.dumps(claims, indent=2))

def generate_ref():
    date_part  = datetime.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"CLM-{date_part}-{unique_part}"

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    ok_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Unauthorized",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username

async def send_notification(record: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(NOTIFY_URL, json=record)
    except Exception as e:
        logger.warning(f"Email notification failed: {e}")

# ── HTML ──────────────────────────────────────────────────────────────────────

CLAIM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>East Coast E-Bike Warranty Center</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
    header{background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);border-bottom:2px solid #22d3ee;padding:20px 40px;display:flex;align-items:center;gap:16px}
    header .logo{font-size:2rem}
    header h1{font-size:1.4rem;font-weight:700;color:#22d3ee}
    header p{font-size:.85rem;color:#94a3b8}
    main{max-width:700px;margin:40px auto;padding:0 20px}
    .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:32px;margin-bottom:24px}
    .card h2{font-size:1.2rem;color:#22d3ee;margin-bottom:20px}
    label{display:block;font-size:.85rem;color:#94a3b8;margin-bottom:6px}
    input,select,textarea{width:100%;padding:10px 14px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:.95rem;margin-bottom:16px;outline:none;transition:border-color .2s}
    input:focus,select:focus,textarea:focus{border-color:#22d3ee}
    textarea{min-height:100px;resize:vertical}
    button{width:100%;padding:12px;background:#22d3ee;color:#0f172a;border:none;border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;transition:background .2s}
    button:hover{background:#06b6d4}
    button:disabled{background:#334155;color:#64748b;cursor:not-allowed}
    .success{background:#064e3b;border:1px solid #10b981;border-radius:8px;padding:20px;text-align:center;display:none}
    .success h3{color:#10b981;font-size:1.1rem;margin-bottom:8px}
    .success .ref{font-size:1.4rem;font-weight:800;color:#34d399;letter-spacing:2px}
    .success p{color:#94a3b8;font-size:.85rem;margin-top:8px}
    .error-msg{color:#f87171;font-size:.85rem;margin-top:-10px;margin-bottom:12px;display:none}
    .spinner{display:inline-block;width:16px;height:16px;border:2px solid #0f172a;border-top-color:transparent;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle;margin-right:8px}
    @keyframes spin{to{transform:rotate(360deg)}}
    footer{text-align:center;color:#475569;font-size:.8rem;padding:32px 0}
    .admin-link{text-align:center;margin-bottom:12px}
    .admin-link a{color:#475569;font-size:.8rem;text-decoration:none}
    .admin-link a:hover{color:#94a3b8}
  </style>
</head>
<body>
  <header>
    <div class="logo">🚲</div>
    <div>
      <h1>East Coast E-Bike Warranty Center</h1>
      <p>Submit your warranty claim — we'll take it from here.</p>
    </div>
  </header>
  <main>
    <div class="card" id="formCard">
      <h2>📋 Submit a Warranty Claim</h2>
      <label>Full Name *</label>
      <input id="name" type="text" placeholder="Jane Smith"/>
      <label>Email Address *</label>
      <input id="email" type="email" placeholder="jane@example.com"/>
      <label>Phone Number</label>
      <input id="phone" type="tel" placeholder="(555) 000-0000"/>
      <label>Bike Model *</label>
      <input id="model" type="text" placeholder="e.g. Trek Powerfly 5"/>
      <label>Purchase Date</label>
      <input id="purchase_date" type="date"/>
      <label>Issue Type *</label>
      <select id="issue_type">
        <option value="">— Select —</option>
        <option>Battery / Range</option>
        <option>Motor / Drive System</option>
        <option>Brakes</option>
        <option>Display / Electronics</option>
        <option>Frame / Structural</option>
        <option>Charging System</option>
        <option>Other</option>
      </select>
      <label>Describe the Issue *</label>
      <textarea id="details" placeholder="Please describe the problem in as much detail as possible…"></textarea>
      <div class="error-msg" id="errorMsg">Please fill in all required fields.</div>
      <button id="submitBtn" onclick="submitClaim()">Submit Claim</button>
    </div>
    <div class="success" id="successCard">
      <h3>✅ Claim Submitted!</h3>
      <div class="ref" id="refId"></div>
      <p>Save this reference number — you'll need it to track your claim.<br/>We'll be in touch within 1–2 business days.</p>
    </div>
    <div class="admin-link"><a href="/admin">Staff login →</a></div>
  </main>
  <footer>East Coast E-Bike Warranty Claims &amp; Repair Center LLC &nbsp;|&nbsp; All rights reserved</footer>
  <script>
    async function submitClaim(){
      const name=document.getElementById('name').value.trim();
      const email=document.getElementById('email').value.trim();
      const phone=document.getElementById('phone').value.trim();
      const model=document.getElementById('model').value.trim();
      const purchase=document.getElementById('purchase_date').value;
      const issue_type=document.getElementById('issue_type').value;
      const details=document.getElementById('details').value.trim();
      const errorMsg=document.getElementById('errorMsg');
      const btn=document.getElementById('submitBtn');
      if(!name||!email||!model||!issue_type||!details){errorMsg.style.display='block';return;}
      errorMsg.style.display='none';
      btn.disabled=true;
      btn.innerHTML='<span class="spinner"></span>Submitting…';
      try{
        const res=await fetch('/submit-claim',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer_name:name,email,phone,bike_model:model,purchase_date:purchase,issue_type,claim_details:details})});
        const data=await res.json();
        if(res.ok){
          document.getElementById('formCard').style.display='none';
          document.getElementById('refId').textContent=data.reference_id;
          document.getElementById('successCard').style.display='block';
        }else{throw new Error(data.detail||'Server error');}
      }catch(err){
        errorMsg.textContent='Submission failed: '+err.message;
        errorMsg.style.display='block';
        btn.disabled=false;
        btn.innerHTML='Submit Claim';
      }
    }
  </script>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Admin — Warranty Claims</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
    header{background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);border-bottom:2px solid #22d3ee;padding:16px 32px;display:flex;align-items:center;justify-content:space-between}
    header h1{font-size:1.2rem;font-weight:700;color:#22d3ee}
    header span{font-size:.8rem;color:#94a3b8}
    main{padding:32px}
    .stats{display:flex;gap:16px;margin-bottom:32px;flex-wrap:wrap}
    .stat{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:20px 28px;min-width:140px}
    .stat .num{font-size:2rem;font-weight:800;color:#22d3ee}
    .stat .lbl{font-size:.8rem;color:#94a3b8;margin-top:4px}
    .filters{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}
    .filters select,.filters input{padding:8px 12px;background:#1e293b;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:.9rem;outline:none}
    table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:12px;overflow:hidden}
    th{background:#0f172a;padding:12px 16px;text-align:left;font-size:.8rem;color:#64748b;text-transform:uppercase;letter-spacing:.05em}
    td{padding:12px 16px;border-bottom:1px solid #1e293b;font-size:.9rem;vertical-align:top}
    tr:hover td{background:#263348}
    .badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:600}
    .badge.pending{background:#422006;color:#fb923c}
    .badge.in-progress{background:#1e3a5f;color:#60a5fa}
    .badge.resolved{background:#064e3b;color:#34d399}
    select.status-select{padding:4px 8px;background:#0f172a;border:1px solid #334155;border-radius:6px;color:#e2e8f0;font-size:.8rem;cursor:pointer}
    .empty{text-align:center;color:#475569;padding:60px 0}
    @media(max-width:700px){table,thead,tbody,th,td,tr{display:block}th{display:none}td{padding:6px 12px}td:before{content:attr(data-label)': ';color:#64748b;font-size:.75rem}}
  </style>
</head>
<body>
  <header>
    <h1>🚲 Warranty Claims — Admin</h1>
    <span id="lastUpdate"></span>
  </header>
  <main>
    <div class="stats">
      <div class="stat"><div class="num" id="totalCount">—</div><div class="lbl">Total Claims</div></div>
      <div class="stat"><div class="num" id="pendingCount">—</div><div class="lbl">Pending</div></div>
      <div class="stat"><div class="num" id="progressCount">—</div><div class="lbl">In Progress</div></div>
      <div class="stat"><div class="num" id="resolvedCount">—</div><div class="lbl">Resolved</div></div>
    </div>
    <div class="filters">
      <select id="filterStatus" onchange="render()">
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="in-progress">In Progress</option>
        <option value="resolved">Resolved</option>
      </select>
      <input id="filterSearch" type="text" placeholder="Search name / email / ref…" oninput="render()"/>
    </div>
    <table id="claimsTable">
      <thead>
        <tr>
          <th>Ref ID</th><th>Date</th><th>Customer</th><th>Bike / Issue</th><th>Details</th><th>Status</th>
        </tr>
      </thead>
      <tbody id="tableBody"><tr><td colspan="6" class="empty">Loading…</td></tr></tbody>
    </table>
  </main>
  <script>
    let allClaims=[];
    async function load(){
      const res=await fetch('/claims');
      allClaims=await res.json();
      allClaims.sort((a,b)=>new Date(b.submitted_at)-new Date(a.submitted_at));
      updateStats();
      render();
      document.getElementById('lastUpdate').textContent='Last updated: '+new Date().toLocaleTimeString();
    }
    function updateStats(){
      document.getElementById('totalCount').textContent=allClaims.length;
      document.getElementById('pendingCount').textContent=allClaims.filter(c=>c.status==='pending').length;
      document.getElementById('progressCount').textContent=allClaims.filter(c=>c.status==='in-progress').length;
      document.getElementById('resolvedCount').textContent=allClaims.filter(c=>c.status==='resolved').length;
    }
    function render(){
      const status=document.getElementById('filterStatus').value;
      const search=document.getElementById('filterSearch').value.toLowerCase();
      let claims=allClaims;
      if(status) claims=claims.filter(c=>c.status===status);
      if(search) claims=claims.filter(c=>(c.customer_name+c.email+c.reference_id+c.bike_model).toLowerCase().includes(search));
      const tbody=document.getElementById('tableBody');
      if(!claims.length){tbody.innerHTML='<tr><td colspan="6" class="empty">No claims found.</td></tr>';return;}
      tbody.innerHTML=claims.map(c=>`
        <tr>
          <td data-label="Ref"><code>${c.reference_id}</code></td>
          <td data-label="Date">${new Date(c.submitted_at).toLocaleDateString()}</td>
          <td data-label="Customer"><strong>${c.customer_name}</strong><br/><small style="color:#94a3b8">${c.email}</small>${c.phone?'<br/><small style="color:#64748b">'+c.phone+'</small>':''}</td>
          <td data-label="Bike">${c.bike_model||'—'}<br/><small style="color:#94a3b8">${c.issue_type||'—'}</small></td>
          <td data-label="Details" style="max-width:220px;white-space:pre-wrap;font-size:.8rem;color:#94a3b8">${c.claim_details}</td>
          <td data-label="Status">
            <select class="status-select" onchange="updateStatus('${c.reference_id}',this.value)">
              <option value="pending" ${c.status==='pending'?'selected':''}>Pending</option>
              <option value="in-progress" ${c.status==='in-progress'?'selected':''}>In Progress</option>
              <option value="resolved" ${c.status==='resolved'?'selected':''}>Resolved</option>
            </select>
          </td>
        </tr>`).join('');
    }
    async function updateStatus(refId,newStatus){
      await fetch('/claims/'+refId+'/status',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:newStatus})});
      const c=allClaims.find(x=>x.reference_id===refId);
      if(c) c.status=newStatus;
      updateStats();
    }
    load();
    setInterval(load,30000);
  </script>
</body>
</html>"""

# ── models ────────────────────────────────────────────────────────────────────

class ClaimRequest(BaseModel):
    customer_name: str  = Field(..., min_length=1, max_length=100)
    email:         str  = Field(..., min_length=3, max_length=200)
    phone:         str  = Field(default="", max_length=30)
    bike_model:    str  = Field(default="", max_length=100)
    purchase_date: str  = Field(default="")
    issue_type:    str  = Field(default="")
    claim_details: str  = Field(default="", max_length=2000)

class StatusUpdate(BaseModel):
    status: str

# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return CLAIM_HTML

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/submit-claim")
async def submit_claim(claim: ClaimRequest):
    try:
        ref = generate_ref()
        record = {
            "reference_id":  ref,
            "submitted_at":  datetime.now().isoformat(),
            "customer_name": claim.customer_name,
            "email":         claim.email,
            "phone":         claim.phone,
            "bike_model":    claim.bike_model,
            "purchase_date": claim.purchase_date,
            "issue_type":    claim.issue_type,
            "claim_details": claim.claim_details,
            "status":        "pending",
        }
        claims = load_claims()
        claims.append(record)
        save_claims(claims)
        logger.info(f"Claim saved: {ref} for {claim.customer_name}")

        # Fire-and-forget email notification
        await send_notification(record)

        return {"status": "success", "reference_id": ref,
                "message": f"Claim received for {claim.customer_name}"}
    except Exception as e:
        logger.error(f"Error processing claim: {e}")
        raise HTTPException(status_code=500, detail="Error processing claim")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(username: str = Depends(verify_admin)):
    return ADMIN_HTML

@app.get("/claims")
async def list_claims(username: str = Depends(verify_admin)):
    return load_claims()

@app.patch("/claims/{ref_id}/status")
async def update_status(ref_id: str, update: StatusUpdate,
                         username: str = Depends(verify_admin)):
    claims = load_claims()
    for c in claims:
        if c["reference_id"] == ref_id:
            c["status"] = update.status
            save_claims(claims)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Claim not found")
