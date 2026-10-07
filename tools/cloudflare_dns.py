#!/usr/bin/env python3
"""Apply the DNS setup for jmrludan.com and its redirect domains on Cloudflare.

Declarative and idempotent: run it as often as you like, it only changes what
differs. Reads the API token from the CLOUDFLARE_API_TOKEN environment variable.

    python3 tools/cloudflare_dns.py --check           # show current records, change nothing
    python3 tools/cloudflare_dns.py --dry-run         # print the planned changes
    python3 tools/cloudflare_dns.py                   # apply
    python3 tools/cloudflare_dns.py --zone joshludan.com   # limit to one zone

Token permissions needed (scoped to the zones below):
    Zone > Zone > Read, Zone > DNS > Edit, Zone > Dynamic Redirect > Edit
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"

PRIMARY = "jmrludan.com"
GITHUB_PAGES_CNAME = "jmrludan.github.io"
GITHUB_A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
GITHUB_AAAA = ["2606:50c0:8000::153", "2606:50c0:8001::153", "2606:50c0:8002::153", "2606:50c0:8003::153"]

# Domains that should 301 to the primary site, keeping the path and query.
REDIRECT_ZONES = ["joshludan.com", "raccoon.baby"]
# Cloudflare needs a proxied record to exist before a redirect rule can fire.
# 192.0.2.1 is a reserved documentation address and never receives traffic.
PLACEHOLDER_IP = "192.0.2.1"

# Record types this script never creates, edits or deletes.
PROTECTED_TYPES = {"MX", "TXT", "SRV", "CAA", "NS", "SOA"}


def desired_records(zone):
    """Return the list of records (type, name, content, proxied) a zone should have."""
    if zone == PRIMARY:
        recs = [("A", zone, ip, False) for ip in GITHUB_A]
        recs += [("AAAA", zone, ip, False) for ip in GITHUB_AAAA]
        recs.append(("CNAME", "www." + zone, GITHUB_PAGES_CNAME, False))
        return recs
    return [("A", zone, PLACEHOLDER_IP, True), ("A", "www." + zone, PLACEHOLDER_IP, True)]


class CF:
    def __init__(self, token, dry_run):
        self.token = token
        self.dry_run = dry_run

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(API + path, data=data, method=method)
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                out = json.load(resp)
        except urllib.error.HTTPError as e:
            try:
                out = json.load(e)
            except Exception:
                sys.exit(f"{method} {path} failed: HTTP {e.code}")
        if not out.get("success"):
            sys.exit(f"{method} {path} failed: {json.dumps(out.get('errors'))}")
        return out["result"]

    def write(self, method, path, body=None, what=""):
        print(("  [dry-run] " if self.dry_run else "  ") + what)
        if not self.dry_run:
            return self.call(method, path, body)

    def zone_id(self, name):
        zones = self.call("GET", f"/zones?name={name}")
        if not zones:
            return None
        return zones[0]["id"], zones[0]["status"], zones[0].get("name_servers", [])

    def records(self, zid):
        return self.call("GET", f"/zones/{zid}/dns_records?per_page=500")


def sync_records(cf, zone, zid):
    current = cf.records(zid)
    wanted = desired_records(zone)
    wanted_names = {name for _, name, _, _ in wanted}
    wanted_proxied = {(t, n, c): p for t, n, c, p in wanted}
    wanted_keys = set(wanted_proxied)

    # Delete address records on the names we own that are not wanted
    # (e.g. the old Squarespace A record or the Google Sites CNAME).
    for r in current:
        if r["type"] in PROTECTED_TYPES or r["name"] not in wanted_names:
            continue
        if r["type"] not in {"A", "AAAA", "CNAME"}:
            continue
        key = (r["type"], r["name"], r["content"])
        if key not in wanted_keys:
            cf.write("DELETE", f"/zones/{zid}/dns_records/{r['id']}", None,
                     f"delete {r['type']} {r['name']} -> {r['content']}")
        elif bool(r.get("proxied")) != wanted_proxied[key]:
            want_proxied = wanted_proxied[key]
            cf.write("PATCH", f"/zones/{zid}/dns_records/{r['id']}", {"proxied": want_proxied},
                     f"set proxied={want_proxied} on {r['type']} {r['name']} -> {r['content']}")

    existing = {(r["type"], r["name"], r["content"]) for r in current}
    for t, n, c, p in wanted:
        if (t, n, c) in existing:
            print(f"  ok     {t} {n} -> {c}")
            continue
        cf.write("POST", f"/zones/{zid}/dns_records",
                 {"type": t, "name": n, "content": c, "ttl": 1, "proxied": p},
                 f"create {t} {n} -> {c} (proxied={p})")


def sync_redirect(cf, zone, zid):
    """Make the zone's dynamic-redirect phase contain one rule: 301 everything to the primary site."""
    target = f'concat("https://{PRIMARY}", http.request.uri.path)'
    rule = {
        "description": f"Redirect {zone} to {PRIMARY}",
        "expression": "true",
        "action": "redirect",
        "action_parameters": {
            "from_value": {
                "status_code": 301,
                "preserve_query_string": True,
                "target_url": {"expression": target},
            }
        },
        "enabled": True,
    }
    phase = "http_request_dynamic_redirect"
    try:
        current = cf.call("GET", f"/zones/{zid}/rulesets/phases/{phase}/entrypoint")
        rules = current.get("rules", [])
    except SystemExit:
        rules = []  # no ruleset in this phase yet
    for r in rules:
        ap = r.get("action_parameters", {}).get("from_value", {})
        if (r.get("action") == "redirect" and r.get("expression") == "true"
                and ap.get("target_url", {}).get("expression") == target
                and ap.get("status_code") == 301):
            print(f"  ok     redirect rule -> https://{PRIMARY}")
            return
    cf.write("PUT", f"/zones/{zid}/rulesets/phases/{phase}/entrypoint", {"rules": [rule]},
             f"set redirect rule: * -> https://{PRIMARY}/<path> (301)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="print current records only")
    ap.add_argument("--dry-run", action="store_true", help="print planned changes without applying")
    ap.add_argument("--zone", help="limit to one zone")
    args = ap.parse_args()

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        sys.exit("CLOUDFLARE_API_TOKEN is not set")
    cf = CF(token, dry_run=args.dry_run or args.check)
    try:
        cf.call("GET", "/user/tokens/verify")
    except SystemExit as e:
        sys.exit(
            f"{e}\n\nCloudflare rejected the credential. This script needs an *API Token* "
            "(Cloudflare dashboard > My Profile > API Tokens > Create Token), not the "
            "account's Global API Key. Make sure the full token was copied and that it has "
            "Zone:Read, DNS:Edit and Dynamic Redirect:Edit on the three zones."
        )

    zones = [PRIMARY] + REDIRECT_ZONES
    if args.zone:
        zones = [args.zone]
    for zone in zones:
        print(f"\n== {zone}")
        info = cf.zone_id(zone)
        if not info:
            print("  not found on this Cloudflare account; add it as a site first")
            continue
        zid, status, ns = info
        print(f"  status: {status}  nameservers: {', '.join(ns)}")
        if args.check:
            for r in cf.records(zid):
                flag = " (proxied)" if r.get("proxied") else ""
                print(f"  {r['type']:<6} {r['name']:<28} {r['content']}{flag}")
            continue
        sync_records(cf, zone, zid)
        if zone in REDIRECT_ZONES:
            sync_redirect(cf, zone, zid)
    print()


if __name__ == "__main__":
    main()
