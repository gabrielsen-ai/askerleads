#!/usr/bin/env python3
"""
Hent leads fra Google Places API (bedrifter uten nettside i Asker og Bærum),
verifiser via Google-søk, og skriv resultater til public/leads.json.

Svartelisting: Henter eksisterende lead-IDer fra Supabase og ekskluderer dem.
"""

import json
import os
import re
import time
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

try:
    from supabase import create_client
except ImportError:
    create_client = None

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Gemini-oppsett (REST API direkte for å støtte referrer-begrensede nøkler)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

API_URL = "https://places.googleapis.com/v1/places:searchText"

# Lokasjoner
LOCATIONS = {
    "ASKER": {"latitude": 59.9130155, "longitude": 10.5583176},
    "BÆRUM": {"latitude": 59.9186, "longitude": 10.5003},
}

INITIAL_RADIUS = 5000
MAX_RESULTS_PER_QUERY = 20

TARGET_RESULTS = 20  # per lokasjon
MAX_PAGES = 10
MAX_RADIUS = 50000
RADIUS_GROWTH = 2

SEARCH_QUERIES = [
    "frisor", "regnskapsforer", "bilverksted", "bilpleie",
    "rørlegger", "elektriker", "snekker", "tømrer",
    "maler", "renhold", "blomsterbutikk", "bakeri",
    "kafe", "restaurant", "dagligvare", "tannlege",
    "legekontor", "fysioterapi", "vaktmester", "glassmester",
    "rør", "taktekker", "møbelsnekker", "byggservice",
    "fotograf", "skredder", "hudpleie", "neglesalong",
    "barbershop", "dyrebutikk",
]

EXCLUDED_TYPES = {
    "airport", "bus_station", "bus_stop", "ferry_terminal",
    "light_rail_station", "subway_station", "train_station", "transit_station",
}

INDUSTRY_MAP = {
    "plumber": "Rørlegger",
    "electrician": "Elektriker",
    "painter": "Maler",
    "florist": "Blomsterbutikk",
    "cafe": "Kafé",
    "bakery": "Bakeri",
    "hair_care": "Frisør",
    "beauty_salon": "Frisør",
    "car_repair": "Bilverksted",
    "car_wash": "Bilverksted",
    "furniture_store": "Snekker",
    "home_improvement_store": "Snekker",
    "house_cleaning": "Renhold",
}

CATALOG_DOMAINS = {
    "gulesider.no", "proff.no", "1881.no", "facebook.com",
    "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "youtube.com", "tripadvisor.com", "tripadvisor.no",
    "yelp.com", "purehelp.no", "brreg.no", "finn.no",
    "google.com", "google.no", "kart.gulesider.no",
}


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


def generate_info_text(place: dict, industry: str) -> str:
    """Generer 2 setninger om bedriften for cold-call-kontekst."""
    if GEMINI_API_KEY:
        try:
            result = _generate_info_with_gemini(place, industry)
            if result:
                return result
        except Exception as e:
            print(f"    Gemini feilet for {(place.get('displayName') or {}).get('text', '?')}: {e}")
    return _generate_info_template(place, industry)


def _generate_info_with_gemini(place: dict, industry: str) -> str:
    """Bruk Gemini til å generere en 2-setnings norsk bedriftsbeskrivelse."""
    name = (place.get("displayName") or {}).get("text", "")
    address = place.get("formattedAddress", "")
    primary_type = (place.get("primaryTypeDisplayName") or {}).get("text", "")
    editorial = (place.get("editorialSummary") or {}).get("text", "")
    rating = place.get("rating", 0)
    review_count = place.get("userRatingCount", 0)

    reviews = place.get("reviews") or []
    review_texts = []
    for review in reviews:
        text = (review.get("text") or {}).get("text", "")
        if len(text) > 20:
            review_texts.append(text[:300])
        if len(review_texts) >= 5:
            break

    context_parts = [f"Bedriftsnavn: {name}"]
    if industry and industry != "Annet":
        context_parts.append(f"Bransje: {industry}")
    if primary_type:
        context_parts.append(f"Type: {primary_type}")
    if address:
        context_parts.append(f"Adresse: {address}")
    if rating:
        context_parts.append(f"Rating: {rating}/5 ({review_count} anmeldelser)")
    if editorial:
        context_parts.append(f"Redaksjonelt sammendrag: {editorial}")
    if review_texts:
        context_parts.append(f"Kundeanmeldelser:\n" + "\n".join(f"- {r}" for r in review_texts))

    context = "\n".join(context_parts)

    if review_texts:
        sentence2_instruction = (
            "Setning 2: Oppsummer hva kundene sier basert på anmeldelsene.\n"
        )
    elif review_count > 0:
        sentence2_instruction = (
            "Setning 2: Beskriv bedriftens omdømme basert på rating og antall anmeldelser.\n"
        )
    else:
        sentence2_instruction = (
            "Setning 2: Beskriv kort hva slags tjenester bedriften tilbyr.\n"
            "IKKE nevn kundeanmeldelser, omdømme eller tilbakemeldinger når det ikke finnes anmeldelser.\n"
        )

    prompt = (
        "Du er en assistent som skriver korte bedriftsbeskrivelser for selgere som skal ringe kalde leads.\n"
        "Skriv NØYAKTIG 2 setninger på norsk basert KUN på informasjonen nedenfor.\n\n"
        "Setning 1: Beskriv hva bedriften driver med og hvor den holder til.\n"
        f"{sentence2_instruction}\n"
        "VIKTIGE REGLER:\n"
        "- IKKE dikt opp informasjon som ikke står i konteksten (alder, omsetning, antall ansatte osv.)\n"
        "- IKKE bruk anførselstegn eller sitér anmeldelser direkte\n"
        "- Hvis det finnes kundeanmeldelser KAN du oppsummere temaer (f.eks. «kundene fremhever god service»)\n"
        "- Hvis det IKKE finnes anmeldelser, IKKE skriv om kundeerfaringer eller omdømme\n"
        "- Skriv i tredjeperson (f.eks. «de tilbyr», IKKE «vi tilbyr»)\n"
        "- Svar KUN med de 2 setningene, ingen annen tekst\n\n"
        f"KONTEKST:\n{context}"
    )

    max_retries = 3
    delay = 1.0
    for attempt in range(max_retries + 1):
        time.sleep(delay)
        resp = requests.post(
            GEMINI_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
                "Referer": "http://localhost:5175",
            },
            json={
                "contents": [{"parts": [{"text": prompt}]}],
            },
        )
        if resp.status_code == 429 and attempt < max_retries:
            delay = min(delay * 2, 16)
            print(f"    Gemini rate limit, venter {delay}s (forsøk {attempt + 1}/{max_retries})...")
            continue
        break

    if resp.status_code != 200:
        print(f"    Gemini API error {resp.status_code}: {resp.text[:200]}")
        return ""

    data = resp.json()
    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
        .strip()
    )

    if len(text) < 10 or len(text) > 500:
        return ""
    return text


def _generate_info_template(place: dict, industry: str) -> str:
    """Malbasert reserve for generering av bedriftsinformasjon."""
    name = (place.get("displayName") or {}).get("text", "")
    editorial = (place.get("editorialSummary") or {}).get("text", "")
    if editorial:
        sentence1 = editorial.rstrip(".")
    elif industry and industry != "Annet":
        sentence1 = f"{name} er en {industry.lower()}-bedrift"
    else:
        primary_type = (place.get("primaryTypeDisplayName") or {}).get("text", "")
        if primary_type:
            sentence1 = f"{name} er en bedrift ({primary_type})"
        else:
            sentence1 = f"{name} er en lokal bedrift"

    rating = place.get("rating", 0)
    review_count = place.get("userRatingCount", 0)
    if rating >= 4.0 and review_count > 0:
        sentence2 = f"Bedriften har et godt omdømme med {rating} av 5 stjerner basert på {review_count} anmeldelser"
    elif rating and review_count:
        sentence2 = f"Har {rating} av 5 stjerner basert på {review_count} vurderinger på Google"
    else:
        sentence2 = ""

    if sentence2:
        return f"{sentence1}. {sentence2}."
    return f"{sentence1}."


def guess_industry(types: list[str]) -> str:
    for t in types:
        if t in INDUSTRY_MAP:
            return INDUSTRY_MAP[t]
    return "Annet"


def calculate_score(rating: float, review_count: int, has_website: bool) -> int:
    rating_score = (rating / 5) * 50
    review_score = min(review_count / 5, 30)
    no_website_bonus = 0 if has_website else 20
    return round(rating_score + review_score + no_website_bonus)


def is_valid_website(value) -> bool:
    if not isinstance(value, str):
        return False
    trimmed = value.strip()
    if not trimmed:
        return False
    try:
        parsed = urlparse(trimmed)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.hostname or "." not in parsed.hostname:
            return False
        return True
    except Exception:
        return False


def fetch_places(sted: str, location: dict, blacklisted_ids: set[str]) -> list[dict]:
    """Hent bedrifter uten nettside fra Google Places API for en gitt lokasjon."""
    if not API_KEY:
        print("FEIL: GOOGLE_PLACES_API_KEY ikke funnet i .env")
        return []

    results = []
    seen_ids = set()
    radius = INITIAL_RADIUS

    while len(results) < TARGET_RESULTS and radius <= MAX_RADIUS:
        for query in SEARCH_QUERIES:
            if len(results) >= TARGET_RESULTS:
                break

            next_page_token = None
            page_count = 0

            while len(results) < TARGET_RESULTS and page_count < MAX_PAGES:
                body = {
                    "textQuery": f"{query} {sted}",
                    "maxResultCount": MAX_RESULTS_PER_QUERY,
                    "locationBias": {
                        "circle": {
                            "center": location,
                            "radius": radius,
                        }
                    },
                }
                if next_page_token:
                    body["pageToken"] = next_page_token

                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": API_KEY,
                    "X-Goog-FieldMask": (
                        "places.displayName,places.formattedAddress,"
                        "places.rating,places.userRatingCount,places.types,"
                        "places.nationalPhoneNumber,places.websiteUri,places.id,"
                        "places.editorialSummary,places.reviews,places.primaryTypeDisplayName"
                    ),
                    "Referer": "http://localhost:5175",
                }

                resp = requests.post(API_URL, json=body, headers=headers)
                if resp.status_code != 200:
                    print(f"  API error {resp.status_code} for query '{query}': {resp.text[:200]}")
                    break

                data = resp.json()
                places = data.get("places", [])
                next_page_token = data.get("nextPageToken")
                page_count += 1

                for i, p in enumerate(places):
                    if is_valid_website(p.get("websiteUri")):
                        continue
                    types = p.get("types", [])
                    if not types or any(t in EXCLUDED_TYPES for t in types):
                        continue

                    place_id = p.get("id", f"goog-{radius}-{query}-{page_count}-{i}")
                    if place_id in seen_ids or place_id in blacklisted_ids:
                        continue
                    seen_ids.add(place_id)

                    rating = p.get("rating", 0)
                    review_count = p.get("userRatingCount", 0)
                    has_website = False
                    industry = guess_industry(types)

                    results.append({
                        "id": place_id,
                        "name": (p.get("displayName") or {}).get("text", "Unknown"),
                        "address": p.get("formattedAddress", ""),
                        "rating": rating,
                        "userRatingCount": review_count,
                        "industry": industry,
                        "phone": p.get("nationalPhoneNumber", ""),
                        "sted": sted,
                        "hasWebsite": has_website,
                        "potentialScore": calculate_score(rating, review_count, has_website),
                        "info": generate_info_text(p, industry),
                    })

                if not next_page_token:
                    break

        if len(results) < TARGET_RESULTS:
            radius *= RADIUS_GROWTH

    print(f"  Fant {len(results)} leads for {sted}")
    return results


def is_catalog_domain(domain: str) -> bool:
    """Sjekk om et domene er en kjent katalog-/oppslagsside."""
    domain = domain.lower()
    for catalog in CATALOG_DOMAINS:
        if domain == catalog or domain.endswith("." + catalog):
            return True
    return False


def normalize_name(name: str) -> str:
    """Normaliser et bedriftsnavn for domene-matching."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def check_domain_guess(name: str) -> bool:
    """Prøv å gjette domenet (name.no, name.com) med en HEAD-forespørsel."""
    slug = normalize_name(name)
    if not slug:
        return False
    if len(slug) > 60:
        return False
    for tld in (".no", ".com"):
        url = f"https://www.{slug}{tld}"
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                print(f"    Domenegjetting traff: {url}")
                return True
        except (requests.RequestException, UnicodeError):
            pass
    return False


def verify_no_website(lead: dict) -> bool:
    """
    Verifiser at en bedrift IKKE har en nettside.
    Returnerer True hvis ingen nettside ble funnet (behold leadet).
    """
    name = lead["name"]
    sted = lead.get("sted", "")

    if google_search is not None:
        try:
            query = f'"{name}" {sted}'
            search_results = list(google_search(query, num_results=5))

            for url in search_results:
                try:
                    domain = urlparse(url).hostname or ""
                except Exception:
                    continue

                if is_catalog_domain(domain):
                    continue

                norm_name = normalize_name(name)
                norm_domain = re.sub(r"[^a-z0-9]", "", domain.lower())
                if norm_name and norm_name in norm_domain:
                    print(f"    Fant nettside via søk: {url}")
                    return False

        except Exception as e:
            print(f"    Google-søk feilet for '{name}': {e}")

    if check_domain_guess(name):
        return False

    return True


def main():
    print("=== AskerLeads Generator (Asker + Bærum) ===\n")

    # Steg 1: Svartelisting fra Supabase
    print("Steg 1: Henter svarteliste fra Supabase...")
    blacklisted_ids = get_blacklisted_ids()

    # Steg 2: Hent leads for alle lokasjoner
    print(f"\nSteg 2: Henter leads fra Google Places API...")
    all_leads = []
    for sted, location in LOCATIONS.items():
        print(f"\n  --- {sted} ---")
        leads = fetch_places(sted, location, blacklisted_ids)
        all_leads.extend(leads)

    if not all_leads:
        print("Ingen leads funnet. Sjekk API-nøkkelen og prøv igjen.")
        write_results([])
        return

    # Steg 3: Nettside-verifisering
    print(f"\nSteg 3: Verifiserer at {len(all_leads)} leads ikke har nettside...")
    verified = []
    for i, lead in enumerate(all_leads):
        print(f"  [{i+1}/{len(all_leads)}] Sjekker: {lead['name']} ({lead['sted']})")
        if verify_no_website(lead):
            verified.append(lead)
            print(f"    -> Ingen nettside funnet (beholdes)")
        else:
            print(f"    -> Nettside funnet (fjernes)")

        if i < len(all_leads) - 1:
            time.sleep(1.5)

    print(f"\nVerifisering fullført: {len(verified)}/{len(all_leads)} leads beholdt")

    # Steg 4: Sorter etter vurdering/anmeldelser
    verified.sort(key=lambda l: (-l["rating"], -l["userRatingCount"]))

    # Steg 5: Skriv resultater
    write_results(verified)


def write_results(leads: list[dict]):
    out_path = os.path.join(os.path.dirname(__file__), "public", "leads.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    print(f"\nSkrev {len(leads)} leads til {out_path}")


if __name__ == "__main__":
    main()
