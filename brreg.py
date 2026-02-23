#!/usr/bin/env python3
"""
Hent nylig registrerte bedrifter fra Brønnøysundregistrene (Brreg)
i Asker og Bærum kommuner.

Filtrerer på kontaktinfo (telefon/mobil/epost), ekskluderer de med hjemmeside,
scorer og rangerer – topp 20 skrives til public/leads-brreg.json.

API: https://data.brreg.no/enhetsregisteret/api/enheter (åpen, gratis, ingen auth)

Kjør:
    python brreg.py
"""

import json
import os
from datetime import datetime, timedelta

import requests

try:
    from supabase import create_client
except ImportError:
    create_client = None

from dotenv import load_dotenv

load_dotenv()

API_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"

# Kommunenumre
KOMMUNER = {
    "3203": "ASKER",
    "3024": "BÆRUM",
}

# NACE-koder som er relevante for lokale tjenestebedrifter
RELEVANTE_NACE = {
    "96.021", "96.022",  # Frisering
    "43.220",  # Rørlegger
    "43.210",  # Elektriker
    "43.341",  # Maler
    "41.200",  # Bygging
    "43.110",  # Riving
    "43.120",  # Grunnarbeid
    "43.310",  # Pussearbeid
    "43.320",  # Snekker
    "43.910",  # Takarbeid
    "43.990",  # Annet spesialisert bygge
    "45.200",  # Bilverksted
    "45.201",  # Bilpleie
    "47.761",  # Blomsterbutikk
    "10.710",  # Bakeri
    "56.101", "56.102",  # Restaurant/kafé
    "56.210",  # Catering
    "81.210",  # Rengjøring
    "81.220",  # Annen rengjøring
    "86.230",  # Tannlege
    "86.211", "86.212",  # Lege
    "86.909",  # Fysioterapi o.l.
    "74.201", "74.202",  # Fotograf
    "96.011", "96.012",  # Vaskeri
    "96.040",  # Hudpleie
    "96.090",  # Andre personlige tjenester
}

TOP_N = 20


def get_blacklisted_ids() -> set[str]:
    """Hent alle eksisterende lead-IDer fra Supabase for svartelisting."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key or not create_client:
        print("  Supabase ikke konfigurert – ingen svartelisting")
        return set()
    try:
        client = create_client(url, key)
        result = client.table("leads").select("id").execute()
        ids = {row["id"] for row in (result.data or [])}
        print(f"  Svarteliste: {len(ids)} eksisterende leads i Supabase")
        return ids
    except Exception as e:
        print(f"  Kunne ikke hente svarteliste: {e}")
        return set()


def format_address(adr: dict) -> str:
    """Formater Brreg-adresse til lesbar streng."""
    parts = []
    adresse = adr.get("adresse", [])
    if adresse:
        parts.append(", ".join(a for a in adresse if a))
    postnr = adr.get("postnummer", "")
    poststed = adr.get("poststed", "")
    if postnr or poststed:
        parts.append(f"{postnr} {poststed}".strip())
    return ", ".join(parts) if parts else ""


def format_date(date_str: str) -> str:
    """Formater ISO-dato til norsk format."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return date_str or ""


def calculate_score(enhet: dict, kommune_nr: str) -> int:
    """Beregn potensialscore for en Brreg-enhet (maks 100)."""
    score = 0

    # Har telefon/mobil: +40
    telefon = enhet.get("telefon") or enhet.get("mobil") or ""
    if telefon:
        score += 40

    # Har e-post: +20
    epost = enhet.get("epostadresse") or ""
    if epost:
        score += 20

    # Lokasjon
    if kommune_nr == "3203":
        score += 20  # Asker
    elif kommune_nr == "3024":
        score += 15  # Bærum

    # Registreringsdato
    reg_dato = enhet.get("registreringsdatoEnhetsregisteret", "")
    if reg_dato:
        try:
            reg = datetime.strptime(reg_dato, "%Y-%m-%d")
            dager = (datetime.now() - reg).days
            if dager <= 30:
                score += 10
            elif dager <= 90:
                score += 7
            elif dager <= 180:
                score += 5
        except ValueError:
            pass

    # Relevant NACE-kode
    nace = enhet.get("naeringskode1", {})
    nace_kode = nace.get("kode", "")
    if nace_kode in RELEVANTE_NACE:
        score += 10

    return min(score, 100)


def generate_info(enhet: dict) -> str:
    """Generer info-tekst for en Brreg-enhet."""
    navn = enhet.get("navn", "")
    org_form = enhet.get("organisasjonsform", {}).get("beskrivelse", "")
    stiftelse = enhet.get("stiftelsesdato", "")
    nace = enhet.get("naeringskode1", {})
    nace_beskrivelse = nace.get("beskrivelse", "")
    nace_kode = nace.get("kode", "")
    epost = enhet.get("epostadresse", "")

    parts = []

    # Setning 1: Organisasjonsform og stiftelsesdato
    if org_form and stiftelse:
        parts.append(f"{navn} er et {org_form.lower()} stiftet {format_date(stiftelse)}.")
    elif org_form:
        parts.append(f"{navn} er et {org_form.lower()}.")
    else:
        parts.append(f"{navn} er en nyregistrert bedrift.")

    # Setning 2: NACE-beskrivelse
    if nace_beskrivelse and nace_kode:
        parts.append(f"Virksomheten driver med {nace_beskrivelse.lower()} (NACE {nace_kode}).")
    elif nace_beskrivelse:
        parts.append(f"Virksomheten driver med {nace_beskrivelse.lower()}.")

    # Kontaktinfo
    if epost:
        parts.append(f"Kontakt: {epost}")

    return " ".join(parts)


def fetch_brreg_enheter(blacklisted_ids: set[str]) -> list[dict]:
    """Hent enheter fra Brreg API for Asker og Bærum, registrert siste 6 mnd."""
    fra_dato = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    all_leads = []

    for kommune_nr, kommune_navn in KOMMUNER.items():
        print(f"\n  --- {kommune_navn} (kommune {kommune_nr}) ---")

        page = 0
        total_fetched = 0

        while True:
            params = {
                "kommunenummer": kommune_nr,
                "fraRegistreringsdatoEnhetsregisteret": fra_dato,
                "size": 100,
                "page": page,
            }

            resp = requests.get(API_URL, params=params)
            if resp.status_code != 200:
                print(f"  API error {resp.status_code}: {resp.text[:200]}")
                break

            data = resp.json()
            enheter = data.get("_embedded", {}).get("enheter", [])

            if not enheter:
                break

            total_fetched += len(enheter)

            for enhet in enheter:
                org_nr = str(enhet.get("organisasjonsnummer", ""))

                # Skip svartelistede
                if org_nr in blacklisted_ids:
                    continue

                # Må ha kontaktinfo (telefon/mobil/epost)
                telefon = enhet.get("telefon") or enhet.get("mobil") or ""
                epost = enhet.get("epostadresse") or ""
                if not telefon and not epost:
                    continue

                # Ekskluder de med hjemmeside
                if enhet.get("hjemmeside"):
                    continue

                # Formater adresse
                forretningsadresse = enhet.get("forretningsadresse", {})
                adresse = format_address(forretningsadresse)

                # NACE/bransje
                nace = enhet.get("naeringskode1", {})
                industry = nace.get("beskrivelse", "Annet")

                # Score
                score = calculate_score(enhet, kommune_nr)

                lead = {
                    "id": org_nr,
                    "name": enhet.get("navn", ""),
                    "address": adresse,
                    "rating": 0,
                    "userRatingCount": 0,
                    "industry": industry,
                    "phone": telefon,
                    "sted": kommune_navn,
                    "hasWebsite": False,
                    "potentialScore": score,
                    "info": generate_info(enhet),
                    "source": "brreg",
                    "status": "pending",
                    "notes": epost if epost else "",
                }

                all_leads.append(lead)

            # Sjekk om det finnes flere sider
            total_pages = data.get("page", {}).get("totalPages", 1)
            page += 1
            if page >= total_pages:
                break

        print(f"  Hentet {total_fetched} enheter, {len([l for l in all_leads if KOMMUNER.get(kommune_nr, '') == l.get('sted')])} kvalifiserte leads for {kommune_navn}")

    return all_leads


def main():
    print("=== Brreg Leads Generator (Asker + Bærum) ===\n")

    # Steg 1: Svartelisting fra Supabase
    print("Steg 1: Henter svarteliste fra Supabase...")
    blacklisted_ids = get_blacklisted_ids()

    # Steg 2: Hent leads fra Brreg
    print(f"\nSteg 2: Henter nye bedrifter fra Brønnøysundregistrene...")
    all_leads = fetch_brreg_enheter(blacklisted_ids)

    if not all_leads:
        print("\nIngen kvalifiserte leads funnet.")
        write_results([])
        return

    print(f"\nFant totalt {len(all_leads)} kvalifiserte leads")

    # Steg 3: Sorter etter score og ta topp N
    all_leads.sort(key=lambda l: -l["potentialScore"])
    top_leads = all_leads[:TOP_N]

    print(f"Topp {len(top_leads)} leads valgt (score {top_leads[0]['potentialScore']}–{top_leads[-1]['potentialScore']})")

    # Steg 4: Skriv til JSON
    write_results(top_leads)

    # Steg 5: Importer direkte til Supabase
    import_to_supabase(top_leads)


def write_results(leads: list[dict]):
    out_path = os.path.join(os.path.dirname(__file__), "public", "leads-brreg.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    print(f"\nSkrev {len(leads)} leads til {out_path}")


def import_to_supabase(leads: list[dict]):
    """Importer leads direkte til Supabase."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key or not create_client:
        print("\n⚠️  Supabase ikke konfigurert – hopper over import")
        return

    client = create_client(url, key)

    # Hent eksisterende leads for å unngå duplikater
    FINAL_STATUSES = {"accepted", "rejected"}
    result = client.table("leads").select("id, status").execute()
    existing = {row["id"]: (row.get("status") or "pending") for row in (result.data or [])}

    # Konverter feltnavn til snake_case for DB
    to_insert = []
    skipped = 0
    for lead in leads:
        if lead["id"] in existing:
            skipped += 1
            continue

        db_lead = {
            "id": lead["id"],
            "name": lead["name"],
            "address": lead["address"],
            "rating": lead["rating"],
            "user_rating_count": lead["userRatingCount"],
            "industry": lead["industry"],
            "phone": lead["phone"],
            "email": lead["sted"],
            "has_website": lead["hasWebsite"],
            "potential_score": lead["potentialScore"],
            "info": lead["info"],
            "source": lead["source"],
            "status": lead["status"],
            "notes": lead.get("notes", ""),
        }
        to_insert.append(db_lead)

    if skipped:
        print(f"\n⏭️  Hoppet over {skipped} leads som allerede finnes i Supabase")

    if not to_insert:
        print("📭 Ingen nye leads å importere til Supabase")
        return

    print(f"\n📤 Importerer {len(to_insert)} nye leads til Supabase...")
    batch_size = 100
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i:i + batch_size]
        client.table("leads").insert(batch).execute()
        print(f"   ✓ La til {len(batch)} leads (batch {i // batch_size + 1})")

    print(f"✅ {len(to_insert)} nye brreg-leads importert til Supabase!")


if __name__ == "__main__":
    main()
