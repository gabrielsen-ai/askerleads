"""
Importerer leads fra JSON-filer til Supabase.

Kjør dette skriptet én gang for å få eksisterende data inn i Supabase:
    python import_to_supabase.py
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

def import_leads(json_file: str):
    """Importerer leads fra en JSON-fil til Supabase."""
    print(f"📂 Leser {json_file}...")
    
    with open(json_file, "r", encoding="utf-8") as f:
        leads = json.load(f)
    
    print(f"✅ Fant {len(leads)} leads")
    
    # Konverter camelCase til snake_case for databasefelter
    for lead in leads:
        # Behold eksisterende felter som de er
        # Legg til default status hvis det ikke finnes
        if "status" not in lead:
            lead["status"] = "pending"
        
        # Konverter hasWebsite -> has_website
        if "hasWebsite" in lead:
            lead["has_website"] = lead.pop("hasWebsite")
        
        # Konverter userRatingCount -> user_rating_count
        if "userRatingCount" in lead:
            lead["user_rating_count"] = lead.pop("userRatingCount")
        
        # Konverter potentialScore -> potential_score
        if "potentialScore" in lead:
            lead["potential_score"] = lead.pop("potentialScore")
    
    print(f"📤 Importerer til Supabase...")
    
    # Importer i batches (Supabase har grense på hvor mange man kan legge inn samtidig)
    batch_size = 100
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]
        result = supabase.table("leads").upsert(batch).execute()
        print(f"   ✓ Importerte {len(batch)} leads (batch {i // batch_size + 1})")
    
    print(f"✅ Ferdig! {len(leads)} leads importert fra {json_file}\n")

if __name__ == "__main__":
    print("🚀 Starter import til Supabase...\n")
    
    # Importer begge JSON-filene
    import_leads("public/leads.json")
    import_leads("public/leads-baerum.json")
    
    print("🎉 Alle leads er importert til Supabase!")
    print("\nNeste steg:")
    print("  1. Restart dev-serveren (npm run dev)")
    print("  2. Appen vil nå hente data fra Supabase i stedet for JSON-filer")
