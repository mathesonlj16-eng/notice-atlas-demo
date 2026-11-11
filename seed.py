"""Produce deterministic FICTIONAL procurement notices; no public/live data is imported."""
from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path

AS_OF = date(2026, 11, 11)
PROJECTS = [
    ("Digital resource directory and accessibility refresh", "Hearthview Community Network", "Web & CMS", "Ontario", 19500),
    ("Operations reporting dashboard", "Northfield Programs Office", "Data & BI", "Ontario", 27800),
    ("Internal document approval automation", "Cedarbrook Association", "Workflow", "Atlantic", 15400),
    ("Volunteer sign-up and scheduling portal", "Beacon Community Partners", "Web & CMS", "British Columbia", 32000),
    ("Digital evidence review prototype", "Fictional Civic Data Lab", "AI & Governance", "Ontario", 47000),
    ("Content-management migration and training", "Silverplain Learning Centre", "Web & CMS", "Prairies", 22800),
    ("Data quality and reporting study", "Coastal Research Collective", "Data & BI", "Atlantic", 14500),
    ("Workflow integration discovery", "Maplebridge Collaborative", "Workflow", "Ontario", 12000),
    ("Searchable grant directory", "Bluefield Regional Forum", "Web & CMS", "Quebec", 38000),
    ("AI system inventory assessment", "Newbridge Model Research Unit", "AI & Governance", "Quebec", 55000),
    ("Accessible program registration flow", "Harbourpoint Skills Network", "Web & CMS", "Atlantic", 26000),
    ("Performance metric data pipeline", "Lakepath Community Office", "Data & BI", "Ontario", 42000),
    ("Service desk automation pilot", "Westfield Support Alliance", "Workflow", "Prairies", 29900),
    ("Public content taxonomy review", "Fictional Valley Library", "Web & CMS", "Ontario", 8200),
    ("Reporting template modernization", "Parkridge Health Studies Unit", "Data & BI", "British Columbia", 17400),
    ("Risk-register reporting prototype", "Limestone Audit Lab", "AI & Governance", "Ontario", 72000),
    ("Community event calendar improvement", "Sunridge Volunteer Group", "Web & CMS", "Prairies", 13300),
    ("API data validation and transformation", "Ridgecrest Public Data Office", "Data & BI", "Quebec", 33500),
]

def generate() -> dict:
    notices = []
    for i, (title, buyer, category, region, budget) in enumerate(PROJECTS, start=1):
        published = AS_OF - timedelta(days=3 + i % 9)
        deadline = AS_OF + timedelta(days=2 + i * 2)
        status = "Open" if i not in (4, 9, 15) else ("Amended" if i == 9 else "Closed")
        history = [{"date": published.isoformat(), "event": "First observed", "detail": "Fictional initial notice"}]
        deadline_evidence = []
        confidence = "Review needed"
        if i in (5, 9, 16):
            history.append({"date": (published + timedelta(days=2)).isoformat(), "event": "Data conflict", "detail": "Two fictional snapshots report different dates; awaiting source verification"})
            deadline_evidence = [
                {"source": "Fictional notice snapshot", "observed": published.isoformat(),
                 "deadline": deadline.isoformat()},
                {"source": "Fictional bulletin snapshot", "observed": (published + timedelta(days=2)).isoformat(),
                 "deadline": (deadline + timedelta(days=7)).isoformat()},
            ]
            confidence = "Conflicting source"
        elif i in (2, 12):
            history.append({"date": (published + timedelta(days=2)).isoformat(), "event": "Amendment observed", "detail": "Fictional scope clarification logged"})
        notices.append({
            "id": f"DEMO-{i:04d}", "title": title, "buyer": buyer,
            "category": category, "region": region,
            "published": published.isoformat(), "deadline": None if deadline_evidence else deadline.isoformat(),
            "deadline_evidence": deadline_evidence,
            "budget_cad": budget, "status": status, "confidence": confidence,
            "eligibility": "Not assessed", "history": history,
            "summary": f"Fictional example of a {category.lower()} engagement. Review original scope and mandatory qualifications before drawing any procurement conclusion.",
        })
    return {"metadata": {"fictional": True, "as_of": AS_OF.isoformat(), "description": "DEMONSTRATION ONLY â€” not live tenders or purchasable work", "schema_version": 2}, "notices": notices}

if __name__ == '__main__':
    output = Path(__file__).resolve().parent / 'data' / 'sample_notices.json'
    output.write_text(json.dumps(generate(), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {output} ({len(generate()["notices"])} fictional notices)')
