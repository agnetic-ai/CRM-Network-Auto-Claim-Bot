#!/usr/bin/env python3
"""
CRM Network Auto-Claim Bot v3 — Multi-Account
CUPANG AI AGENT
Usage:
  python3 crm_autoclaim.py                     # all accounts
  python3 crm_autoclaim.py --accounts custom.json
  python3 crm_autoclaim.py -t                   # test profile first account
  python3 crm_autoclaim.py --only ombengz       # specific account
"""

import json
import subprocess
import sys
import os
from datetime import datetime

API_BASE = "https://crmnetwork.xyz"
DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(DIR, "accounts.local.json")
TEMPLATE_FILE = os.path.join(DIR, "accounts.json")
HASHES_FILE = os.path.join(DIR, "hashes.local.json")
HASHES_FALLBACK = os.path.join(DIR, "hashes.json")

FUNCTIONS = {}


def load_hashes():
    global FUNCTIONS
    path = HASHES_FILE if os.path.exists(HASHES_FILE) else HASHES_FALLBACK
    if not os.path.exists(path):
        print("Missing: hashes.json or hashes.local.json")
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
        k_list = p.get("k", [])
        v_list = p.get("v", [])
        result = {}
        for i, k_item in enumerate(k_list):
            k = seroval_key(k_item)
            result[k] = seroval_value(v_list[i]) if i < len(v_list) else None
        return result
    elif t == 13:
        return [seroval_value(item) for item in obj.get("p", [])]
    elif t == 1:
        return obj.get("s", "")
    elif t == 0:
        return obj.get("s", 0)
    elif t == 2:
        return obj.get("s", False)
    elif t == 4:
        return None
    elif t == 25:
        msg = obj.get("s", {})
        if isinstance(msg, dict):
            msg = msg.get("message", {}).get("s", str(msg))
        return {"_error": msg}
    elif t == 9:
        return obj.get("s", 0)
    return obj


def build_payload(init_data, extra=None):
    data = {"_initData": init_data}
    if extra:
        data.update(extra)

    keys = [{"t": 1, "s": k} for k in data]
    vals = []
    for k, v in data.items():
        if isinstance(v, bool):
            vals.append({"t": 2, "s": v})
        elif isinstance(v, (int, float)):
            vals.append({"t": 0, "s": v})
        else:
            vals.append({"t": 1, "s": str(v)})

    seroval = {
        "t": 10, "i": 0,
        "p": {
            "k": [{"t": 1, "s": "data"}],
            "v": [{"t": 10, "i": 1, "p": {"k": keys, "v": vals}, "o": 0}]
        },
        "o": 0
    }
    return {"t": seroval, "f": 63, "m": []}


def call_fn(fn_name, init_data, extra=None):
    h = FUNCTIONS.get(fn_name)
    if not h:
        return {"_error": f"Unknown: {fn_name}"}

    body = json.dumps(build_payload(init_data, extra))
    url = f"{API_BASE}/_serverFn/{h}"

    result = subprocess.run([
        "curl", "-s", url,
        "-H", "Content-Type: application/json",
        "-H", "x-tsr-serverFn: true",
        "-H", "Accept: application/x-tss-framed, application/x-ndjson, application/json",
        "-H", "Origin: https://crmnetwork.xyz",
        "-H", "Referer: https://crmnetwork.xyz/",
        "-d", body
    ], capture_output=True, text=True, timeout=15)

    try:
        resp = json.loads(result.stdout)
    except Exception:
        return {"_error": f"Parse: {result.stdout[:100]}"}

    if not isinstance(resp, dict) or "p" not in resp:
        return {"_error": f"Bad response: {str(resp)[:100]}"}

    p = resp["p"]
    k_list = p.get("k", [])
    v_list = p.get("v", [])

    err_val = None
    res_val = None
    for i, k_item in enumerate(k_list):
        kn = seroval_key(k_item)
        if kn == "error" and i < len(v_list):
            err_val = v_list[i]
        elif kn == "result" and i < len(v_list):
            res_val = v_list[i]

    if err_val is not None:
        if isinstance(err_val, dict):
            if err_val.get("t") == 2:
                pass  # true = success
            elif err_val.get("t") == 25:
                msg = err_val.get("s", {})
                if isinstance(msg, dict):
                    msg = msg.get("message", {}).get("s", str(msg))
                return {"_error": str(msg)}
            elif err_val.get("s"):
                return {"_error": str(err_val.get("s"))}
            else:
                return {"_error": str(err_val)}
        elif isinstance(err_val, (int, float)):
            if err_val != 0:
                return {"_error": f"Error code {err_val}"}
        elif isinstance(err_val, str) and err_val:
            return {"_error": err_val}
        elif err_val is False:
            return {"_error": "Request failed"}

    return seroval_value(res_val) if res_val is not None else {}


def fmt(v, decimals=4):
    if isinstance(v, (int, float)):
        return f"{v:.{decimals}f}"
    return str(v)


def process_account(acct):
    name = acct.get("name", "?")
    init_data = acct["init_data"]
    steps = []
    errors = []

    profile = call_fn("getProfile", init_data)
    if "_error" in profile:
        return {
            "name": name, "ok": False,
            "errors": [f"Profile: {profile['_error'][:60]}"],
            "steps": [], "balance": 0, "rate": 0,
            "energy": 0, "max_energy": 100, "power": 0, "earned": 0,
        }

    bal = float(profile.get("balance", 0) or 0)
    rate = float(profile.get("mining_rate", 0) or 0)
    energy = int(profile.get("energy", 0) or 0)
    max_en = int(profile.get("max_energy", 100) or 100)
    pending = float(profile.get("live_earned", 0) or 0)
    power = int(profile.get("mining_power", 0) or 0)
    balance = bal

    # Energy boost FIRST
    if energy < max_en:
        r = call_fn("energyBoost", init_data)
        if "_error" not in r:
            new_en = int(r.get("energy", energy) or energy)
            gained = new_en - energy
            steps.append(("boost", f"+{gained} energy ({new_en}/{max_en})"))
            energy = new_en
        else:
            steps.append(("boost", f"skip ({r['_error'][:30]})"))
    else:
        steps.append(("boost", "full"))

    # Claim
    earned = 0
    if pending >= 0.01:
        r = call_fn("claimMining", init_data)
        if "_error" not in r:
            earned = float(r.get("earned", 0) or 0)
            balance = float(r.get("balance", 0) or 0)
            steps.append(("claim", f"+{fmt(earned)} CRM"))
        else:
            err_msg = r["_error"]
            if "No energy" in err_msg or "energy" in err_msg.lower():
                steps.append(("claim", "no energy (skip)"))
            else:
                steps.append(("claim", f"err: {err_msg[:30]}"))
                errors.append(f"Claim: {err_msg[:40]}")
    else:
        steps.append(("claim", f"pending {fmt(pending)} < 0.01"))

    if balance == 0:
        profile = call_fn("getProfile", init_data)
        if "_error" not in profile:
            balance = float(profile.get("balance", 0) or 0)

    # Restart mining
    r = call_fn("startMining", init_data)
    if "_error" not in r:
        steps.append(("mining", "started"))
    else:
        err_msg = r["_error"]
        if "Already" in err_msg and "mining" in err_msg:
            steps.append(("mining", "running"))
        else:
            steps.append(("mining", f"err: {err_msg[:30]}"))
            errors.append(f"Mining: {err_msg[:40]}")

    # Stakes
    stakes = call_fn("listMyStakes", init_data)
    if "_error" not in stakes:
        sl = stakes if isinstance(stakes, list) else []
        if sl:
            r = call_fn("claimStakeRewards", init_data)
            if "_error" not in r:
                steps.append(("stake", "rewards claimed"))
            else:
                steps.append(("stake", f"err: {r['_error'][:30]}"))
                errors.append(f"Stake: {r['_error'][:40]}")
        else:
            steps.append(("stake", "none"))

    return {
        "name": name, "ok": len(errors) == 0, "errors": errors, "steps": steps,
        "balance": balance, "rate": rate, "energy": energy, "max_energy": max_en,
        "power": power, "earned": earned,
    }


def load_accounts(path):
    if not os.path.exists(path):
        fallback = TEMPLATE_FILE
        if os.path.exists(fallback):
            with open(fallback) as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]
            return data
        print(f"File not found: {path}")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    return data


def main():
    load_hashes()
    acct_path = ACCOUNTS_FILE
    only_name = None

    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--accounts" and i + 1 < len(args):
            acct_path = args[i + 1]
        elif a == "--only" and i + 1 < len(args):
            only_name = args[i + 1]
        elif a in ("-t", "--test"):
            accounts = load_accounts(acct_path)
            r = call_fn("getProfile", accounts[0]["init_data"])
            print(json.dumps(r, indent=2)[:800])
            return

    accounts = load_accounts(acct_path)
    if only_name:
        accounts = [a for a in accounts if a.get("name") == only_name]
        if not accounts:
            print(f"No account: {only_name}")
            sys.exit(1)

    ts = datetime.now().strftime("%H:%M:%S")
    results = []

    for acct in accounts:
        r = process_account(acct)
        results.append(r)

    total_ok = sum(1 for r in results if r["ok"])
    total_fail = len(results) - total_ok

    W = 56

    def line(c="-"):
        return "+" + c * (W - 2) + "+"

    def row(text):
        pad = W - 2 - len(text)
        if pad < 0:
            pad = 0
        return "| " + text + " " * pad + "|"

    print(line())
    print(row(f"CRM Auto-Claim  {ts}  {len(results)} akun"))
    print(line())

    for r in results:
        icon = "+" if r["ok"] else "!"
        nm = r["name"]
        print(row(f"[{icon}] {nm}"))
        print(row(
            f"  Bal: {fmt(r['balance'])}  Rate: {fmt(r['rate'])}/hr"
            f"  E:{r['energy']}/{r['max_energy']}  P:{r['power']}"
        ))
        for step, detail in r.get("steps", []):
            print(row(f"  {step:8s} {detail}"))
        if r["errors"]:
            for e in r["errors"]:
                print(row(f"  ! {e}"))
        print(line())

    status = f"{total_ok} OK"
    if total_fail:
        status += f" / {total_fail} FAIL"
    print(row(status))
    print(line())
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
