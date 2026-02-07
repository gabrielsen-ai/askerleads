#!/usr/bin/env python3
"""
Fetch leads from Google Places API (businesses without websites in Asker),
verify via Google Search, and write results to public/leads.json.
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

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
API_URL = "https://places.googleapis.com/v1/places:searchText"

ASKER_LOCATION = {"latitude": 59.9130155, "longitude": 10.5583176}
INITIAL_RADIUS = 5000
MAX_RESULTS_PER_QUERY = 20

TARGET_RESULTS = 20  # fetch more, filter down after verification
FINAL_RESULTS = 10
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
    "plumber": "Plumber",
    "electrician": "Electrician",
    "painter": "Painter",
    "florist": "Florist",
    "cafe": "Cafe",
    "bakery": "Bakery",
    "hair_care": "Hair Salon",
    "beauty_salon": "Hair Salon",
    "car_repair": "Auto Repair",
    "car_wash": "Auto Repair",
    "furniture_store": "Carpenter",
    "home_improvement_store": "Carpenter",
    "house_cleaning": "Cleaning Service",
}

CATALOG_DOMAINS = {
    "gulesider.no", "proff.no", "1881.no", "facebook.com",
    "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "youtube.com", "tripadvisor.com", "tripadvisor.no",
    "yelp.com", "purehelp.no", "brreg.no", "finn.no",
    "google.com", "google.no", "kart.gulesider.no",
}


def generate_info_text(place: dict, industry: str) -> str:
    """Generate 2 sentences about the business for cold-call context."""
    # Sentence 1: What the business is
    editorial = (place.get("editorialSummary") or {}).get("text", "")
    if editorial:
        sentence1 = editorial.rstrip(".")
    else:
        primary_type = (place.get("primaryTypeDisplayName") or {}).get("text", "")
        if primary_type:
            sentence1 = f"{primary_type} i Asker"
        else:
            sentence1 = f"{industry} i Asker"

    # Sentence 2: Customer signal (best review snippet or rating summary)
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
    return "Other"


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
    """Fetch businesses without websites from Google Places API."""
    if not API_KEY:
        print("ERROR: GOOGLE_PLACES_API_KEY not found in .env")
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
                    # Skip if has website
                    if is_valid_website(p.get("websiteUri")):
                        continue
                    # Skip excluded types
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

    print(f"Found {len(results)} leads without website (Google Places)")
    return results


def is_catalog_domain(domain: str) -> bool:
    """Check if a domain is a known catalog/directory site."""
    domain = domain.lower()
    for catalog in CATALOG_DOMAINS:
        if domain == catalog or domain.endswith("." + catalog):
            return True
    return False


def normalize_name(name: str) -> str:
    """Normalize a business name for domain matching."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def check_domain_guess(name: str) -> bool:
    """Try guessing the domain (name.no, name.com) with a HEAD request."""
    slug = normalize_name(name)
    if not slug:
        return False
    for tld in (".no", ".com"):
        url = f"https://www.{slug}{tld}"
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                print(f"    Domain guess hit: {url}")
                return True
        except requests.RequestException:
            pass
    return False


def verify_no_website(lead: dict) -> bool:
    """
    Verify that a business does NOT have a website.
    Returns True if no website was found (keep the lead).
    Returns False if a website was found (remove the lead).
    """
    name = lead["name"]

    # Step 1: Google search
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

                # Check if business name appears in domain
                norm_name = normalize_name(name)
                norm_domain = re.sub(r"[^a-z0-9]", "", domain.lower())
                if norm_name and norm_name in norm_domain:
                    print(f"    Found website via search: {url}")
                    return False

        except Exception as e:
            print(f"    Google search failed for '{name}': {e}")

    # Step 2: Direct domain guessing
    if check_domain_guess(name):
        return False

    return True


def main():
    print("=== AskerLeads Generator ===\n")

    # Step 1: Fetch from Google Places
    print("Step 1: Fetching leads from Google Places API...")
    leads = fetch_places()

    if not leads:
        print("No leads found. Check your API key and try again.")
        write_results([])
        return

    # Step 2: Web verification
    print(f"\nStep 2: Verifying {len(leads)} leads have no website...")
    verified = []
    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] Checking: {lead['name']}")
        if verify_no_website(lead):
            verified.append(lead)
            print(f"    -> No website found (keeping)")
        else:
            print(f"    -> Website found (removing)")

        if i < len(leads) - 1:
            time.sleep(1.5)

    print(f"\nVerification complete: {len(verified)}/{len(leads)} leads kept")

    # Step 3: Sort and limit
    verified.sort(key=lambda l: (-l["rating"], -l["userRatingCount"]))
    final = verified[:FINAL_RESULTS]

    # Step 4: Write results
    write_results(final)


def write_results(leads: list[dict]):
    out_path = os.path.join(os.path.dirname(__file__), "public", "leads.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(leads)} leads to {out_path}")


if __name__ == "__main__":
    main()
