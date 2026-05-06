"""
KrushiYantra — agriculture intelligence MVP (Flask).
Multi-page app with in-memory profile and ClaimSure uploads.
"""

import os
import uuid
from datetime import datetime

from flask import Flask, redirect, render_template, request, send_file, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from geo_exif import analyze_field_image
from i18n import LANGS, LANG_LABELS, translate

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "krushiyantra-dev-secret-change-me")
# Phone camera JPEGs (especially geotagged / high-res) often exceed 8 MB
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB
UPLOAD_DIR = os.path.join(app.static_folder or "static", "uploads")
REPORTS_DIR = os.path.join(app.static_folder or "static", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(_e):
    return (
        "<h1>File too large</h1><p>Your photo must be under 32 MB. Try a slightly smaller image or lower camera resolution.</p>"
        '<p><a href="/claimsure">Back to ClaimSure</a></p>',
        413,
    )


ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

# In-memory farmer profile + history (demo)
PROFILE = {
    "name": "Ramesh Patil",
    "phone": "+91 98765 43210",
    "village": "Sonwadi, Pune",
    "acres": 4.5,
    "primary_crop": "sugarcane",
}
HISTORY = [
    {"ts": "2026-03-12", "action": "ClaimSure draft saved", "module": "ClaimSure"},
    {"ts": "2026-03-18", "action": "Loan pre-check — High band", "module": "Loan"},
    {"ts": "2026-03-28", "action": "PM-KISAN match confirmed", "module": "Scheme"},
]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def get_lang() -> str:
    lang = session.get("lang", "en")
    return lang if lang in LANGS else "en"


@app.context_processor
def inject_i18n():
    lang = get_lang()

    def t(key: str) -> str:
        return translate(lang, key)

    return dict(t=t, current_lang=lang, lang_labels=LANG_LABELS, langs=LANGS)


@app.route("/set-lang", methods=["POST"])
def set_lang():
    lang = request.form.get("lang", "en")
    if lang in LANGS:
        session["lang"] = lang
    next_url = request.form.get("next") or request.referrer or url_for("home")
    return redirect(next_url)


def nav_active(endpoint: str) -> str:
    return "active" if request.endpoint == endpoint else ""


# --- Pages ---


@app.route("/")
def home():
    return render_template("home.html", nav_active=nav_active)


def _claimsure_reference() -> str:
    return f"KY-CS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


@app.route("/claimsure", methods=["GET", "POST"])
def claimsure():
    result = None
    escalation_sent = session.pop("iarda_report_id", None)
    if request.method == "POST":
        crop = request.form.get("crop_type", "")
        try:
            land = float(request.form.get("land_size") or 0)
        except ValueError:
            land = 0.0
        damage = request.form.get("damage_type", "none")
        damage_date = request.form.get("damage_date", "")
        loc_mode = request.form.get("location_mode", "manual")
        location = request.form.get("location", "").strip()
        if loc_mode == "auto":
            location = location or "Auto: 18.52°N, 73.86°E · Maharashtra (simulated)"

        file = request.files.get("photo")
        rel_path = None
        abs_upload = None
        ext = ""
        img_analysis = {
            "geo_verified": False,
            "gps": None,
            "width": None,
            "height": None,
            "resolution_ok": False,
            "evidence_ok": False,
            "detail": "no_file",
        }

        if file and file.filename and allowed_file(file.filename):
            ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
            name = f"{uuid.uuid4().hex}.{ext}"
            path = os.path.join(UPLOAD_DIR, name)
            file.save(path)
            abs_upload = path
            rel_path = f"uploads/{name}"
            preview_url = url_for("static", filename=rel_path)
            img_analysis = analyze_field_image(path, ext)
        else:
            preview_url = None

        has_damage = damage and damage != "none"
        photo_ok = bool(rel_path)
        evidence_ok = bool(photo_ok and img_analysis.get("evidence_ok"))
        show_amount = bool(has_damage and evidence_ok)
        claim_amount = round(land * 2000, 2) if show_amount else 0.0

        conf_base = 55
        if photo_ok:
            conf_base += 8
        if img_analysis.get("geo_verified"):
            conf_base += 18
        if img_analysis.get("resolution_ok"):
            conf_base += 6
        if location:
            conf_base += 6
        if has_damage:
            conf_base += 8
        if evidence_ok:
            conf_base += 12
        confidence = min(97, conf_base)

        if not photo_ok:
            status_key = "status_photo_required"
        elif not img_analysis.get("geo_verified"):
            status_key = "status_geo_missing"
        elif not img_analysis.get("resolution_ok"):
            status_key = "status_evidence_weak"
        elif not has_damage:
            status_key = "status_review"
        else:
            status_key = "status_eligible"

        eligible = status_key == "status_eligible"
        rec_upload = bool(show_amount)
        rec_priority = bool(show_amount and confidence >= 88)

        reference_id = _claimsure_reference()
        gps = img_analysis.get("gps") or {}
        gps_line = ""
        if gps:
            gps_line = f"{gps.get('lat')}, {gps.get('lon')}"

        result = {
            "reference_id": reference_id,
            "eligible": eligible,
            "show_amount": show_amount,
            "status_key": status_key,
            "claim_amount": claim_amount,
            "confidence": confidence,
            "rec_upload": rec_upload,
            "rec_priority": rec_priority,
            "crop": crop,
            "damage": damage,
            "damage_date": damage_date,
            "location": location,
            "preview": preview_url,
            "geo_verified": bool(img_analysis.get("geo_verified")),
            "evidence_ok": evidence_ok,
            "resolution_ok": bool(img_analysis.get("resolution_ok")),
            "img_w": img_analysis.get("width"),
            "img_h": img_analysis.get("height"),
            "verification_detail": img_analysis.get("detail", ""),
            "gps_line": gps_line,
        }

        if show_amount:
            session["claimsure_escalation"] = {
                "reference_id": reference_id,
                "crop": crop,
                "land": land,
                "claim_amount": claim_amount,
                "damage": damage,
                "damage_date": damage_date,
                "location": location,
                "gps_line": gps_line,
                "farmer_name": PROFILE.get("name", ""),
                "farmer_phone": PROFILE.get("phone", ""),
                "village": PROFILE.get("village", ""),
            }
        else:
            session.pop("claimsure_escalation", None)

    escalation_available = bool(session.get("claimsure_escalation"))

    return render_template(
        "claimsure.html",
        nav_active=nav_active,
        result=result,
        escalation_sent=escalation_sent,
        escalation_available=escalation_available,
    )


@app.route("/claimsure/escalate", methods=["POST"])
def claimsure_escalate():
    payload = session.get("claimsure_escalation")
    if not payload:
        return redirect(url_for("claimsure"))

    try:
        wait_days = int(request.form.get("wait_days") or "0")
    except ValueError:
        wait_days = 0
    allowed_days = (3, 4, 5, 7, 10, 14, 21, 30, 45, 60)
    if wait_days not in allowed_days:
        wait_days = 7

    office_informed = bool(request.form.get("office_informed"))
    notes = (request.form.get("farmer_notes") or "").strip()[:2000]

    report_id = f"IARDA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:10].upper()}"
    lines = [
        "=" * 72,
        "IARDA — Indian Agricultural Redressal & Disputes Authority",
        "ClaimSure non-payment / non-response escalation (official intake log)",
        "=" * 72,
        f"Report ID:        {report_id}",
        f"Claim reference:  {payload.get('reference_id', '')}",
        f"Generated (UTC):  {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "",
        "— Farmer & contact —",
        f"Name:             {payload.get('farmer_name', '')}",
        f"Phone:            {payload.get('farmer_phone', '')}",
        f"Village / area:   {payload.get('village', '')}",
        "",
        "— Claim summary —",
        f"Crop:             {payload.get('crop', '')}",
        f"Land (acres):     {payload.get('land', '')}",
        f"Declared damage:  {payload.get('damage', '')}",
        f"Damage date:      {payload.get('damage_date', '')}",
        f"Location text:    {payload.get('location', '')}",
        f"GPS (EXIF):       {payload.get('gps_line') or 'N/A'}",
        f"Estimated claim:  ₹ {payload.get('claim_amount', 0):,.2f}",
        "",
        "— Grievance statement (farmer attestation) —",
        f"Expected bank credit within: {wait_days} days from filing / intimation.",
        f"Farmer states they informed agriculture / insurance office: {'YES' if office_informed else 'NO'}",
        f"Additional notes: {notes or '—'}",
        "",
        "— System routing —",
        "This report is queued for the IARDA agricultural escalation desk for follow-up",
        "with the concerned insurance provider / state agriculture authority.",
        "(Demo build: stored as file + session confirmation — connect SMTP/API in production.)",
        "=" * 72,
    ]
    body = "\n".join(lines) + "\n"
    fpath = os.path.join(REPORTS_DIR, f"{report_id}.txt")
    with open(fpath, "w", encoding="utf-8") as fh:
        fh.write(body)

    session["iarda_report_id"] = report_id
    session["iarda_last_report_id"] = report_id
    session.pop("claimsure_escalation", None)
    return redirect(url_for("claimsure"))


@app.route("/claimsure/report/<report_id>")
def claimsure_report_download(report_id: str):
    if report_id != session.get("iarda_last_report_id"):
        return redirect(url_for("claimsure"))
    safe_id = secure_filename(report_id)
    fpath = os.path.join(REPORTS_DIR, f"{safe_id}.txt")
    if not os.path.isfile(fpath):
        return redirect(url_for("claimsure"))
    return send_file(
        fpath,
        as_attachment=True,
        download_name=f"{safe_id}.txt",
        mimetype="text/plain",
    )


@app.route("/loan", methods=["GET", "POST"])
def loan():
    result = None
    if request.method == "POST":
        try:
            land = float(request.form.get("land_size") or 0)
        except ValueError:
            land = 0.0
        try:
            income = float(request.form.get("annual_income") or 0)
        except ValueError:
            income = 0.0
        crop = request.form.get("crop_type", "")

        docs = {
            "aadhaar": bool(request.form.get("doc_aadhaar")),
            "land": bool(request.form.get("doc_land")),
            "bank": bool(request.form.get("doc_bank")),
            "credit": bool(request.form.get("doc_credit")),
        }
        doc_count = sum(1 for v in docs.values() if v)
        base = land * 50000
        conf_factor = 0.55 + 0.11 * doc_count  # 0.55 .. 0.99
        amount = round(base * min(1.0, conf_factor) * (0.9 + min(income, 500000) / 5_000_000), 2)

        if doc_count >= 4:
            band_key = "elig_high"
            band_pct = 92
        elif doc_count >= 2:
            band_key = "elig_medium"
            band_pct = 72
        else:
            band_key = "elig_low"
            band_pct = 48

        missing_keys = []
        if not docs["aadhaar"]:
            missing_keys.append("doc_aadhaar")
        if not docs["land"]:
            missing_keys.append("doc_land")
        if not docs["bank"]:
            missing_keys.append("doc_bank")
        if not docs["credit"]:
            missing_keys.append("doc_credit")

        result = {
            "amount": amount,
            "band_key": band_key,
            "band_pct": band_pct,
            "missing_keys": missing_keys,
            "crop": crop,
            "land": land,
            "income": income,
        }

    return render_template("loan.html", nav_active=nav_active, result=result)


# Static scheme catalog for demo
SCHEMES = [
    {"id": "pmkisan"},
    {"id": "pmfby"},
    {"id": "kcc"},
    {"id": "soil"},
    {"id": "micro_irrigation"},
]


@app.route("/scheme", methods=["GET", "POST"])
def scheme():
    result = None
    if request.method == "POST":
        try:
            income = float(request.form.get("income") or 0)
        except ValueError:
            income = 0.0
        try:
            land = float(request.form.get("land_size") or 0)
        except ValueError:
            land = 0.0
        category = request.form.get("farmer_category", "small")

        eligible = []
        priority_id = "pmkisan"

        if land > 0 and income < 1_500_000:
            eligible.append(SCHEMES[0])
        if land >= 0.5:
            eligible.append(SCHEMES[1])
        if land > 0:
            eligible.append(SCHEMES[2])
        if category in ("small", "marginal"):
            eligible.append(SCHEMES[3])
        if land >= 1:
            eligible.append(SCHEMES[4])

        # Dedupe by id
        seen = set()
        unique = []
        for s in eligible:
            if s["id"] not in seen:
                seen.add(s["id"])
                unique.append(s)

        if category == "marginal" and any(s["id"] == "pmkisan" for s in unique):
            priority_id = "pmkisan"
        elif unique:
            priority_id = unique[0]["id"]

        result = {
            "schemes": unique,
            "priority_id": priority_id,
            "income": income,
            "land": land,
            "category": category,
        }

    return render_template("scheme.html", nav_active=nav_active, result=result)


@app.route("/land_intel", methods=["GET", "POST"])
def land_intel():
    result = None
    if request.method == "POST":
        state = request.form.get("state", "").strip()
        district = request.form.get("district", "").strip()
        try:
            land = float(request.form.get("land_size") or 0)
        except ValueError:
            land = 0.0

        value = round(land * 300_000, 2)
        if land >= 5:
            trend_t = "land_trend_up"
            insight_t = "land_insight_invest"
        elif land >= 2:
            trend_t = "land_trend_stable"
            insight_t = "land_insight_hold"
        else:
            trend_t = "land_trend_watch"
            insight_t = "land_insight_hold"

        result = {
            "value": value,
            "trend_t": trend_t,
            "insight_t": insight_t,
            "state": state,
            "district": district,
            "land": land,
        }

    return render_template("land_intel.html", nav_active=nav_active, result=result)


@app.route("/contracts", methods=["GET", "POST"])
def contracts():
    result = None
    if request.method == "POST":
        crop = request.form.get("crop_type", "")
        try:
            yield_q = float(request.form.get("expected_yield") or 0)
        except ValueError:
            yield_q = 0.0
        try:
            land = float(request.form.get("land_size") or 0)
        except ValueError:
            land = 0.0

        benchmark = round(land * 15000, 2)
        contract_value = round(benchmark * (0.85 + min(yield_q, 200) / 400), 2)

        result = {
            "benchmark": benchmark,
            "contract_value": contract_value,
            "crop": crop,
            "yield_q": yield_q,
            "land": land,
        }

    return render_template("contracts.html", nav_active=nav_active, result=result)


@app.route("/profile")
def profile():
    trust = 62
    trust += min(20, int(PROFILE["acres"] * 2))
    trust = min(96, trust)
    return render_template(
        "profile.html",
        nav_active=nav_active,
        profile=PROFILE,
        history=HISTORY,
        trust_score=trust,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
