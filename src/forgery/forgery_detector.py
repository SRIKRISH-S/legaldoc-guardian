# src/forgery/forgery_detector.py
import re, os, json, numpy as np, joblib
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "models/forgery_clf.pkl"

_re_account = re.compile(r"Account[:\s]*([0-9\-\s]{4,})", flags=re.IGNORECASE)
_re_date = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}$")

def normalize_amount_str(s):
    if not s:
        return None
    s = str(s)
    s = re.sub(r"[^\d,]", "", s)
    s = s.replace(",", "")
    if not s:
        return None
    try:
        return int(s)
    except:
        return None

def _is_potential_amount_token(tok_text):
    if not tok_text:
        return False
    tok = tok_text.strip()
    if _re_date.match(tok):
        return False
    if not re.search(r"\d", tok):
        return False
    digits_only = re.sub(r"[^\d]", "", tok)
    if len(digits_only) < 2:
        return False
    if len(digits_only) >= 8:
        return False
    return True

def _as_number(tok_text):
    return normalize_amount_str(tok_text)

def extract_fields_from_ocr(ocr_list):
    tokens = []
    raw_lines = []
    for it in ocr_list:
        t = (it.get("text") or "").strip()
        box = it.get("box") or []
        if box and isinstance(box, (list,tuple)) and len(box)>=1:
            xs = [p[0] for p in box if isinstance(p,(list,tuple))]
            ys = [p[1] for p in box if isinstance(p,(list,tuple))]
            if xs and ys:
                cx = sum(xs)/len(xs)
                cy = sum(ys)/len(ys)
            else:
                cx = cy = None
        else:
            cx = cy = None
        tokens.append({"text": t, "cx": cx, "cy": cy, "raw": it})
        raw_lines.append(t)
    raw_text = "\n".join([t for t in raw_lines if t])

    account = None
    for tok in tokens:
        txt = tok["text"].lower().rstrip(":")
        if txt == "account" or txt.startswith("account"):
            candidate=None; lx,ly = tok.get("cx"), tok.get("cy")
            best_dx=1e9
            for c in tokens:
                if c is tok or not c["text"].strip():
                    continue
                digits_only = re.sub(r"[^\d]","", c["text"])
                if len(digits_only) < 6:
                    continue
                if lx is None or c["cx"] is None:
                    continue
                dx = (c["cx"] or 0) - (lx or 0)
                dy = abs((c["cy"] or 0) - (ly or 0))
                if dx >= -10 and dx < best_dx and dy < 120:
                    best_dx=dx; candidate=c
            if candidate:
                account = re.sub(r"[^\d\-]","", candidate["text"]).replace(" ","")
                break
    if not account:
        m = _re_account.search(raw_text)
        if m:
            account = re.sub(r"[^\d\-]","", m.group(1)).replace(" ","")

    name = None
    for i,tok in enumerate(tokens):
        txt = tok["text"].lower()
        if txt.startswith("name"):
            parts = tok["text"].split(":",1)
            if len(parts)>1 and parts[1].strip():
                name = parts[1].strip()
            else:
                cy = tok.get("cy")
                best=None; best_dx=1e9
                for c in tokens:
                    if c is tok or not c["text"].strip():
                        continue
                    if c["cx"] is None or cy is None:
                        continue
                    dy = abs((c["cy"] or 0)-cy)
                    dx = (c["cx"] or 0) - (tok["cx"] or 0)
                    if dy<60 and dx>0 and dx<best_dx:
                        best_dx=dx; best=c
                if best:
                    name = best["text"]
            break
    if not name:
        nonnum = [t["text"] for t in tokens if t["text"] and not re.fullmatch(r"[\d,]+", t["text"])]
        if nonnum:
            name = max(nonnum, key=len)

    amounts = []
    # labeled Amount tokens
    for tok in tokens:
        if tok["text"].lower().startswith("amount"):
            lx,ly = tok.get("cx"), tok.get("cy")
            candidates=[]
            for c in tokens:
                if c is tok or not c["text"].strip():
                    continue
                if not re.search(r"\d", c["text"]):
                    continue
                if lx is None or c["cx"] is None:
                    continue
                dx = (c["cx"] or 0) - (lx or 0)
                dy = abs((c["cy"] or 0) - (ly or 0))
                if dx >= -10 and dx < 1500 and dy < 120:
                    candidates.append((dx,dy,c))
            candidates.sort(key=lambda x:(x[0],x[1]))
            for _,_,chosen in candidates[:3]:
                val = _as_number(chosen["text"])
                if val is not None:
                    amounts.append(val)
    # currency markers
    for i,tok in enumerate(tokens):
        txt = tok["text"].lower()
        if txt in ("rs","rs.","inr","₹"):
            lx,ly = tok.get("cx"), tok.get("cy")
            best=None; best_dx=1e9
            for c in tokens:
                if c is tok or not c["text"].strip():
                    continue
                if not re.search(r"\d", c["text"]):
                    continue
                if lx is None or c["cx"] is None:
                    continue
                dx = (c["cx"] or 0) - (lx or 0)
                dy = abs((c["cy"] or 0) - (ly or 0))
                if dx >= -10 and dy < 120 and dx < best_dx:
                    best_dx=dx; best=c
            if best:
                val = _as_number(best["text"])
                if val is not None:
                    amounts.append(val)
    # generic numeric tokens with filters
    for tok in tokens:
        if not _is_potential_amount_token(tok["text"]):
            continue
        if account and re.sub(r"[^\d]","", tok["text"]) in account:
            continue
        num = _as_number(tok["text"])
        if num is not None:
            amounts.append(num)

    cleaned_amounts = sorted(set([a for a in amounts if isinstance(a,int) and a>0]))
    final_amounts=[]
    for v in cleaned_amounts:
        if v<10: continue
        if 1900<=v<=2100: continue
        final_amounts.append(v)

    return {"name": name, "account": account, "amounts": final_amounts, "raw_text": raw_text}

# simple features + dummy ML fallback
def simple_features_from_ocr(ocr):
    text = " ".join([x.get("text","") for x in ocr])
    char_count = len(text)
    digits = sum(c.isdigit() for c in text)
    has_amount = int(bool(re.search(r"amount", text, flags=re.I)))
    return np.array([char_count, digits, has_amount]).reshape(1, -1)

def train_dummy():
    X = np.array([[100,10,1],[500,50,1],[120,1,0],[80,2,1],[200,20,0]])
    y = np.array([0,1,1,0,0])
    clf = RandomForestClassifier(n_estimators=10, random_state=0)
    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    return clf

def predict(ocr):
    if not ocr:
        return {"label":"POSSIBLE","score":0.5,"fields":{},"evidence":["no_text_detected"]}
    fields = extract_fields_from_ocr(ocr)
    evidence = []
    score = 0.1
    amounts = fields.get("amounts", [])
    if len(amounts) >= 2:
        unique_amounts = sorted(set(amounts))
        if len(unique_amounts) >= 2:
            evidence.append(f"multiple_amounts_detected:{unique_amounts}")
            score = 0.9
            return {"label":"FORGED","score":score,"fields":fields,"evidence":evidence}
    if not fields.get("account"):
        evidence.append("account_missing")
        score = max(score, 0.45)
    if os.path.exists(MODEL_PATH):
        clf = joblib.load(MODEL_PATH)
    else:
        clf = train_dummy()
    f = simple_features_from_ocr(ocr)
    ml_prob = float(clf.predict_proba(f)[0][1])
    score = max(score, 0.3*ml_prob + 0.2*score)
    label = "FORGED" if score>0.6 else "POSSIBLE" if score>0.35 else "CLEAN"
    if score > 0.6:
        evidence.append("ml_high_score")
    return {"label": label, "score": round(float(score),3), "fields": fields, "evidence": evidence}
