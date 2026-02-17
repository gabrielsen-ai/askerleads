"""
Importerer leads fra JSON-fil til Supabase.

Kun nye leads legges til – eksisterende fjernes ikke.
Leads som allerede finnes med status godtatt (accepted) eller avslått (rejected)
hoppes over og legges ikke til på nytt.

Kjør:
    1. python leads.py               # Henter nye leads (Asker + Bærum)
    2. python import_to_supabase.py  # Legger kun til nye i Supabase
"""

import json
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Hent Supabase-credentials fra .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Feil: SUPABASE_URL og SUPABASE_SERVICE_ROLE_KEY må være satt i .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Status som betyr at leadet ikke skal legges til igjen
FINAL_STATUSES = {"accepted", "rejected"}  # godtatt, avslått


def get_existing_leads() -> dict[str, str]:
    """Henter alle eksisterende lead-ider og deres status fra Supabase."""
    print("📥 Henter eksisterende leads fra Supabase...")
    result = supabase.table("leads").select("id, status").execute()
    return {row["id"]: (row.get("status") or "pending") for row in (result.data or [])}


def import_leads(json_file: str, existing: dict[str, str]) -> dict[str, str]:
    """
    Importerer kun NYE leads fra en JSON-fil til Supabase.
    Hopper over leads som allerede finnes, spesielt de med godtatt/avslått.
    Oppdaterer existing-dict med nye leads som legges til.
    """
    print(f"\n📂 Leser {json_file}...")
    
    with open(json_file, "r", encoding="utf-8") as f:
        leads = json.load(f)
    
    print(f"   Fant {len(leads)} leads i filen")
    
    # Filtrer ut leads som allerede finnes (spesielt godtatt/avslått)
    to_insert = []
    skipped_existing = 0
    skipped_final = 0
    
    for lead in leads:
        lead_id = lead.get("id")
        if not lead_id:
            continue
        if lead_id in existing:
            status = existing[lead_id]
            if status in FINAL_STATUSES:
                skipped_final += 1
            else:
                skipped_existing += 1
            continue
        to_insert.append(lead)
    
    if skipped_final or skipped_existing:
        print(f"   ⏭️  Hoppet over {skipped_existing} som allerede finnes (pending)")
        print(f"   ⏭️  Hoppet over {skipped_final} som allerede er godtatt/avslått")
    
    if not to_insert:
        print(f"   Ingen nye leads å legge til fra {json_file}")
        return existing
    
    # Konverter camelCase til snake_case for databasefelter
    for lead in to_insert:
        if "status" not in lead:
            lead["status"] = "pending"
        if "sted" in lead:
            lead["email"] = lead.pop("sted")
        if "hasWebsite" in lead:
            lead["has_website"] = lead.pop("hasWebsite")
        if "userRatingCount" in lead:
            lead["user_rating_count"] = lead.pop("userRatingCount")
        if "potentialScore" in lead:
            lead["potential_score"] = lead.pop("potentialScore")
    
    print(f"📤 Legger til {len(to_insert)} nye leads...")
    
    batch_size = 100
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i:i + batch_size]
        supabase.table("leads").insert(batch).execute()
        for lead in batch:
            existing[lead["id"]] = lead.get("status", "pending")
        print(f"   ✓ La til {len(batch)} leads (batch {i // batch_size + 1})")
    
    print(f"✅ Ferdig! {len(to_insert)} nye leads lagt til fra {json_file}")
    return existing

if __name__ == "__main__":
    print("🚀 Starter import til Supabase...")
    print("   (Kun nye leads legges til. Godtatt/avslått overskrives ikke.)\n")
    
    existing = get_existing_leads()
    print(f"   {len(existing)} leads finnes allerede i databasen\n")
    
    existing = import_leads("public/leads.json", existing)
    
    print("\n🎉 Import fullført!")
    print(f"   Totalt {len(existing)} leads i databasen nå.")
