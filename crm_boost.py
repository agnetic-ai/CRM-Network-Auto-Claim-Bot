#!/usr/bin/env python3
"""CRM Network — Energy Boost Only (fast, light)"""
import json, subprocess, sys, os, time
from datetime import datetime

API_BASE = "https://crmnetwork.xyz"
DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(DIR, "accounts.local.json")
HASHES_FILE = os.path.join(DIR, "hashes.local.json")
HASHES_FALLBACK = os.path.join(DIR, "hashes.json")
FUNCTIONS = {}

def load_hashes():
    global FUNCTIONS
    path = HASHES_FILE if os.path.exists(HASHES_FILE) else HASHES_FALLBACK
    if not os.path.exists(path):
        print("Missing: hashes")
        sys.exit(1)
    with open(path) as f:
        FUNCTIONS = json.load(f)

def seroval_key(item):
    if isinstance(item, dict):
        return item.get("s", str(item))
    return str(item)

def seroval_value(obj):
    if not isinstance(obj, dict):
        return obj
    t = obj.get("t")
    if t == 10:
        p = obj.get("p", {})
        k_list, v_list = p.get("k", []), p.get("v", [])
        result = {}
        for i, k_item in enumerate(k_list):
            k = seroval_key(k_item)
            result[k] = seroval_value(v_list[i]) if i < len(v_list) else None
        return result
    elif t == 13:
        return [seroval_value(item) for item in obj.get("p", [])]
    elif t == 1: return obj.get("s", "")
    elif t == 0: return obj.get("s", 0)
    elif t == 2: return obj.get("s", False)
    elif t == 25:
        msg = obj.get("s", {})
        if isinstance(msg, dict):
            msg = msg.get("message", {}).get("s", str(msg))
        return {"_error": msg}
    return obj

def build_payload(init_data, extra=None):
    data = {"_initData": init_data}
    if extra: data.update(extra)
    keys = [{"t": 1, "s": k} for k in data]
    vals = []
    for k, v in data.items():
        if isinstance(v, bool): vals.append({"t": 2, "s": v})
        elif isinstance(v, (int, float)): vals.append({"t": 0, "s": v})
        else: vals.append({"t": 1, "s": str(v)})
    seroval = {"t": 10, "i": 0, "p": {"k": [{"t": 1, "s": "data"}], "v": [{"t": 10, "i": 1, "p": {"k": keys, "v": vals}, "o": 0}]}, "o": 0}
    return {"t": seroval, "f": 63, "m": []}

_last_call = 0
def call_fn(fn_name, init_data, extra=None):
    global _last_call
    now = time.time()
    wait = 3 - (now - _last_call)
    if wait > 0: time.sleep(wait)
    _last_call = time.time()
    h = FUNCTIONS.get(fn_name)
    if not h: return {"_error": f"Unknown: {fn_name}"}
    body = json.dumps(build_payload(init_data, extra))
    url = f"{API_BASE}/_serverFn/{h}"
    try:
        result = subprocess.run(["curl", "-s", url,
            "-H", "Content-Type: application/json",
            "-H", "x-tsr-serverFn: true",
            "-H", "Accept: application/x-tss-framed, application/x-ndjson, application/json",
            "-H", "User-Agent: Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 Chrome/125.0 Mobile Safari/537.36 Telegram-Android/11.14.2",
            "-H", "Origin: https://crmnetwork.xyz",
            "-H", "Referer: https://crmnetwork.xyz/",
            "-d", body], capture_output=True, text=True, timeout=30)
    except Exception as e:
        return {"_error": str(e)[:60]}
    try:
        resp = json.loads(result.stdout)
    except:
        return {"_error": f"Parse: {result.stdout[:60]}"}
    if not isinstance(resp, dict) or "p" not in resp:
        return {"_error": f"Bad resp"}

    p = resp["p"]
    k_list, v_list = p.get("k", []), p.get("v", [])
    err_val, res_val = None, None
    for i, k_item in enumerate(k_list):
        kn = seroval_key(k_item)
        if kn == "error" and i < len(v_list): err_val = v_list[i]
        elif kn == "result" and i < len(v_list): res_val = v_list[i]
    if err_val is not None:
        if isinstance(err_val, dict):
            if err_val.get("t") == 2: pass
            elif err_val.get("t") == 25:
                msg = err_val.get("s", {})
                if isinstance(msg, dict):
                    msg = msg.get("message", {}).get("s", str(msg))
                return {"_error": str(msg)}
            elif err_val.get("s"): return {"_error": str(err_val.get("s"))}
            else: return {"_error": str(err_val)}
        elif isinstance(err_val, (int, float)):
            if err_val != 0: return {"_error": f"Err {err_val}"}
        elif isinstance(err_val, str) and err_val: return {"_error": err_val}
    return seroval_value(res_val) if res_val is not None else {}

def load_accounts(path):
    if not os.path.exists(path): sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

FULL_MARKER = "/tmp/crm_boost_full.marker"
COOLDOWN = 600  # 10 minutes

def all_full(lines):
    """Check if every non-error line says 'full'"""
    return all("full" in l for l in lines if "ERROR" not in l)

def main():
    load_hashes()
    accounts = load_accounts(ACCOUNTS_FILE)
    lines = []

    for acct in accounts:
        name = acct.get("name", "?")
        init_data = acct["init_data"]
        try:
            p = call_fn("getProfile", init_data)
            if "_error" in p: continue
            energy = int(p.get("energy", 0) or 0)
            max_en = int(p.get("max_energy", 100) or 100)
            balance = float(p.get("balance", 0) or 0)
            if energy < max_en:
                # Need boost → clear cooldown marker
                if os.path.exists(FULL_MARKER):
                    os.remove(FULL_MARKER)
                r = call_fn("energyBoost", init_data)
                if "_error" not in r:
                    new_en = int(r.get("energy", energy) or energy)
                    lines.append(f"{name:10s} B:{balance:.2f}  E:{energy}→{new_en}  +{new_en-energy}en")
                else:
                    lines.append(f"{name:10s} B:{balance:.2f}  E:{energy}  boost fail")
            else:
                lines.append(f"{name:10s} B:{balance:.2f}  E:{energy}  full")
        except Exception as e:
            lines.append(f"{name:10s} ERROR: {str(e)[:40]}")

    if not lines:
        return

    # If ALL accounts full → throttle
    if all_full(lines):
        if os.path.exists(FULL_MARKER):
            age = time.time() - os.path.getmtime(FULL_MARKER)
            if age < COOLDOWN:
                # Silent — skip delivery
                return
        # Update marker and send summary
        with open(FULL_MARKER, "w") as f:
            f.write(datetime.now().isoformat())

    sep = "-" * 38
    print(f"\n{sep}")
    print("CRM Boost")
    print(sep)
    for l in lines:
        print(l)
    print(sep)

if __name__ == "__main__":
    main()
