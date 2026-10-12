"""CRM Follow-up Automation."""
import argparse
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

import llm

STALE_DAYS = {"new lead": 2, "discovery call": 4, "proposal sent": 5, "negotiation": 3}
TEMPLATES = {
    "new lead": "Hi {contact}, following up on your enquiry about {topic}. When's a good time for a quick call?",
    "discovery call": "Hi {contact}, great speaking with you. As promised, here are next steps on {topic}. Shall I send a proposal?",
    "proposal sent": "Hi {contact}, checking you received the proposal for {topic}. Happy to walk through it or adjust scope.",
    "negotiation": "Hi {contact}, I wanted to close the loop on {topic}. Is there anything blocking a decision this week?",
}


def stale_deals(rows, today):
    out = []
    for r in rows:
        stage = r["stage"].lower()
        if stage not in STALE_DAYS:
            continue
        silent = (today - date.fromisoformat(r["last_contact"])).days
        if silent > STALE_DAYS[stage]:
            out.append({**r, "days_silent": silent,
                        "priority": float(r["value"]) * silent})
    return sorted(out, key=lambda d: -d["priority"])


def draft(d):
    base = TEMPLATES[d["stage"].lower()].format(contact=d["contact"], topic=d["topic"])
    better = llm.complete(f"Rewrite this sales follow-up in under 50 words, using this context "
                          f"from the last conversation: '{d['last_note']}'.\n{base}")
    return (better or base).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="sample_deals.csv")
    ap.add_argument("--today", default="2026-10-09")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.input, encoding="utf-8")))
    stale = stale_deals(rows, date.fromisoformat(a.today))
    per_rep = defaultdict(list)
    for d in stale:
        per_rep[d["owner"]].append(d)
    Path("output").mkdir(exist_ok=True)
    for rep, deals in per_rep.items():
        lines = [f"# Follow-ups for {rep} ({a.today})", ""]
        print(f"== {rep}: {len(deals)} deals to chase ==")
        for d in deals:
            msg = draft(d)
            print(f"  {d['company']:<20} {d['stage']:<15} NGN {float(d['value']):>11,.0f}  silent {d['days_silent']}d")
            print(f"     draft: {msg}")
            lines += [f"## {d['company']} ({d['stage']}, silent {d['days_silent']} days)",
                      f"Value: NGN {float(d['value']):,.0f}", "", msg, ""]
        Path(f"output/digest_{rep.lower()}.md").write_text("\n".join(lines))
        print()
    print(f"{len(stale)} stale of {len(rows)} deals. Digests saved in output/")


if __name__ == "__main__":
    main()
