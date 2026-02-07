#!/usr/bin/env python3
"""
Hent leads fra Google Places API (bedrifter uten nettside i Asker),
verifiser via Google-søk, og skriv resultater til public/leads.json.
"""

import json
import os
import re
import time
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Gemini-oppsett
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None
if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.0-flash")

API_URL = "https://places.googleapis.com/v1/places:searchText"

ASKER_LOCATION = {"latitude": 59.9130155, "longitude": 10.5583176}
INITIAL_RADIUS = 5000
MAX_RESULTS_PER_QUERY = 20

TARGET_RESULTS = 20  # fetch more, filter down after verification
FINAL_RESULTS = None  # output all verified leads
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


def generate_info_text(place: dict, industry: str) -> str:
    """Generer 2 setninger om bedriften for cold-call-kontekst.
    Prøver Gemini først, faller tilbake til malbasert generering."""
    if gemini_model:
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

    # Hent topp 2 nyttige anmeldelser (>20 tegn)
    reviews = place.get("reviews") or []
    review_texts = []
    for review in reviews:
        text = (review.get("text") or {}).get("text", "")
        if len(text) > 20:
            review_texts.append(text[:200])
        if len(review_texts) >= 2:
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
        context_parts.append(f"Kundeanmeldelser: {' | '.join(review_texts)}")

    context = "\n".join(context_parts)

    prompt = (
        "Skriv 2 korte introduserende setninger på norsk om denne bedriften. "
        "Setningene skal gi en selger kontekst ved cold calling. "
        "Fokuser på hva bedriften driver med og hvor den holder til. "
        "Ikke nevn anmeldelser, rating eller stjerner direkte. "
        "Ikke bruk anførselstegn. Svar kun med de 2 setningene.\n\n"
        f"{context}"
    )

    response = gemini_model.generate_content(prompt)
    text = response.text.strip()

    if len(text) < 10 or len(text) > 500:
        return ""
    return text


def _generate_info_template(place: dict, industry: str) -> str:
    """Malbasert reserve for generering av bedriftsinformasjon."""
    # Setning 1: Hva bedriften er
    editorial = (place.get("editorialSummary") or {}).get("text", "")
    if editorial:
        sentence1 = editorial.rstrip(".")
    else:
        primary_type = (place.get("primaryTypeDisplayName") or {}).get("text", "")
        if primary_type:
            sentence1 = f"{primary_type} i Asker"
        else:
            sentence1 = f"{industry} i Asker"

    # Setning 2: Kundesignal (beste anmeldelsesutdrag eller vurderingssammendrag)
    reviews = place.get("reviews") or []
    best_snippet = ""
    for review in reviews:
        text = (review.get("text") or {}).get("text", "")
        if text and len(text) > len(best_snippet):
            best_snippet = text

    if best_snippet:
        if len(best_snippet) > 120:
            best_snippet = best_snippet[:117].rstrip() + "..."
        sentence2 = f'"{best_snippet}"'
    else:
        rating = place.get("rating", 0)
        review_count = place.get("userRatingCount", 0)
        if rating and review_count:
            sentence2 = f"Har {rating} stjerner basert på {review_count} anmeldelser"
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


def fetch_places() -> list[dict]:
    """Hent bedrifter uten nettside fra Google Places API."""
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
                    "textQuery": f"{query} Asker",
                    "maxResultCount": MAX_RESULTS_PER_QUERY,
                    "locationBias": {
                        "circle": {
                            "center": ASKER_LOCATION,
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
                    # Hopp over hvis har nettside
                    if is_valid_website(p.get("websiteUri")):
                        continue
                    # Hopp over ekskluderte typer
                    types = p.get("types", [])
                    if not types or any(t in EXCLUDED_TYPES for t in types):
                        continue

                    place_id = p.get("id", f"goog-{radius}-{query}-{page_count}-{i}")
                    if place_id in seen_ids:
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
                        "hasWebsite": has_website,
                        "potentialScore": calculate_score(rating, review_count, has_website),
                        "info": generate_info_text(p, industry),
                    })

                if not next_page_token:
                    break

        if len(results) < TARGET_RESULTS:
            radius *= RADIUS_GROWTH

    print(f"Fant {len(results)} leads uten nettside (Google Places)")
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
    for tld in (".no", ".com"):
        url = f"https://www.{slug}{tld}"
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                print(f"    Domenegjetting traff: {url}")
                return True
        except requests.RequestException:
            pass
    return False


def verify_no_website(lead: dict) -> bool:
    """
    Verifiser at en bedrift IKKE har en nettside.
    Returnerer True hvis ingen nettside ble funnet (behold leadet).
    Returnerer False hvis en nettside ble funnet (fjern leadet).
    """
    name = lead["name"]

    # Steg 1: Google-søk
    if google_search is not None:
        try:
            query = f'"{name}" Asker'
            search_results = list(google_search(query, num_results=5))

            for url in search_results:
                try:
                    domain = urlparse(url).hostname or ""
                except Exception:
                    continue

                if is_catalog_domain(domain):
                    continue

                # Sjekk om bedriftsnavnet finnes i domenet
                norm_name = normalize_name(name)
                norm_domain = re.sub(r"[^a-z0-9]", "", domain.lower())
                if norm_name and norm_name in norm_domain:
                    print(f"    Fant nettside via søk: {url}")
                    return False

        except Exception as e:
            print(f"    Google-søk feilet for '{name}': {e}")

    # Steg 2: Direkte domenegjetting
    if check_domain_guess(name):
        return False

    return True


def main():
    print("=== AskerLeads Generator ===\n")

    # Steg 1: Hent fra Google Places
    print("Steg 1: Henter leads fra Google Places API...")
    leads = fetch_places()

    if not leads:
        print("Ingen leads funnet. Sjekk API-nøkkelen og prøv igjen.")
        write_results([])
        return

    # Steg 2: Nettside-verifisering
    print(f"\nSteg 2: Verifiserer at {len(leads)} leads ikke har nettside...")
    verified = []
    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] Sjekker: {lead['name']}")
        if verify_no_website(lead):
            verified.append(lead)
            print(f"    -> Ingen nettside funnet (beholdes)")
        else:
            print(f"    -> Nettside funnet (fjernes)")

        if i < len(leads) - 1:
            time.sleep(1.5)

    print(f"\nVerifisering fullført: {len(verified)}/{len(leads)} leads beholdt")

    # Steg 3: Sorter etter vurdering/anmeldelser
    verified.sort(key=lambda l: (-l["rating"], -l["userRatingCount"]))

    # Steg 4: Skriv resultater
    write_results(verified)


def write_results(leads: list[dict]):
    out_path = os.path.join(os.path.dirname(__file__), "public", "leads.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    print(f"\nSkrev {len(leads)} leads til {out_path}")


if __name__ == "__main__":
    main()
