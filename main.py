import logging
import uuid
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="East Coast E-Bike Warranty Hub")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
CLAIMS_FILE = BASE_DIR / "claims.json"

# ── helpers ──────────────────────────────────────────────────────────────────

def load_claims():
    if CLAIMS_FILE.exists():
        return json.loads(CLAIMS_FILE.read_text())
    return []

def save_claims(claims):
    CLAIMS_FILE.write_text(json.dumps(claims, indent=2))

def generate_ref():
    """Generate a unique claim reference like CLM-20260416-A3F2"""
    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"CLM-{date_part}-{unique_part}"

# ── HTML (served inline so one file deploys cleanly) ─────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>East Coast E-Bike Warranty Center</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
    }
    header {
      background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
      border-bottom: 2px solid #22d3ee;
      padding: 20px 40px;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    header .logo { font-size: 2rem; }
    header h1 { font-size: 1.4rem; font-weight: 700; color: #22d3ee; }
    header p  { font-size: 0.85rem; color: #94a3b8; }
    main {
      max-width: 700px;
      margin: 40px auto;
      padding: 0 20px;
    }
    .card {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 32px;
      margin-bottom: 24px;
    }
    .card h2 { font-size: 1.2rem; color: #22d3ee; margin-bottom: 20px; }
    label { display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px; }
    input, select, textarea {
      width: 100%;
      padding: 10px 14px;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      color: #e2e8f0;
      font-size: 0.95rem;
      margin-bottom: 16px;
      outline: none;
      transition: border-color 0.2s;
    }
    input:focus, select:focus, textarea:focus { border-color: #22d3ee; }
    textarea { min-height: 100px; resize: vertical; }
    button {
      width: 100%;
      padding: 12px;
      background: #22d3ee;
      color: #0f172a;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s;
    }
    button:hover { background: #06b6d4; }
    button:disabled { background: #334155; color: #64748b; cursor: not-allowed; }
    .success {
      background: #064e3b;
      border: 1px solid #10b981;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      display: none;
    }
    .success h3 { color: #10b981; font-size: 1.1rem; margin-bottom: 8px; }
    .success .ref { font-size: 1.4rem; font-weight: 800; color: #34d399; letter-spacing: 2px; }
    .success p  { color: #94a3b8; font-size: 0.85rem; margin-top: 8px; }
    .error-msg  { color: #f87171; font-size: 0.85rem; margin-top: -10px; margin-bottom: 12px; display: none; }
    .spinner    { display: inline-block; width: 16px; height: 16px; border: 2px solid #0f172a; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; margin-right: 8px; }
    @keyframes spin { to { transform: rotate(360deg); } }
    footer { text-align: center; color: #475569; font-size: 0.8rem; padding: 32px 0; }
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
      <input id="name" type="text" placeholder="Jane Smith" />

      <label>Email Address *</label>
      <input id="email" type="email" placeholder="jane@example.com" />

      <label>Phone Number</label>
      <input id="phone" type="tel" placeholder="(555) 000-0000" />

      <label>Bike Model *</label>
      <input id="model" type="text" placeholder="e.g. Trek Powerfly 5" />

      <label>Purchase Date</label>
      <input id="purchase_date" type="date" />

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
  </main>

  <footer>East Coast E-Bike Warranty Claims &amp; Repair Center LLC &nbsp;|&nbsp; All rights reserved</footer>

  <script>
    async function submitClaim() {
      const name        = document.getElementById('name').value.trim();
      const email       = document.getElementById('email').value.trim();
      const phone       = document.getElementById('phone').value.trim();
      const model       = document.getElementById('model').value.trim();
      const purchase    = document.getElementById('purchase_date').value;
      const issue_type  = document.getElementById('issue_type').value;
      const details     = document.getElementById('details').value.trim();
      const errorMsg    = document.getElementById('errorMsg');
      const btn         = document.getElementById('submitBtn');

      // Basic validation
      if (!name || !email || !model || !issue_type || !details) {
        errorMsg.style.display = 'block';
        return;
      }
      errorMsg.style.display = 'none';

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>Submitting…';

      try {
        const res = await fetch('/submit-claim', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer_name: name, email, phone, bike_model: model, purchase_date: purchase, issue_type, claim_details: details })
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('formCard').style.display = 'none';
          document.getElementById('refId').textContent = data.reference_id;
          document.getElementById('successCard').style.display = 'block';
        } else {
          throw new Error(data.detail || 'Server error');
        }
      } catch (err) {
        errorMsg.textContent = 'Submission failed: ' + err.message;
        errorMsg.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = 'Submit Claim';
      }
    }
  </script>
</body>
</html>"""

# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Extended claim model
class ClaimRequest(BaseModel):
    customer_name: str  = Field(..., min_length=1, max_length=100)
    email:         str  = Field(..., min_length=3, max_length=200)
    phone:         str  = Field(default="", max_length=30)
    bike_model:    str  = Field(default="", max_length=100)
    purchase_date: str  = Field(default="")
    issue_type:    str  = Field(default="")
    claim_details: str  = Field(default="", max_length=2000)

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
        return {"status": "success", "reference_id": ref, "message": f"Claim received for {claim.customer_name}"}
    except Exception as e:
        logger.error(f"Error processing claim: {e}")
        raise HTTPException(status_code=500, detail="Error processing claim")

@app.get("/claims")
async def list_claims():
    """Admin endpoint — list all submitted claims."""
    return load_claims()
