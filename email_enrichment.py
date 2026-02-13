"""
E-postberikelse for leads.

Finner e-postadresser via norske kataloger (gulesider, proff, 1881)
med Google Search + Gemini som fallback.
"""

from __future__ import annotations

import html as html_lib
import re
import time
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

# Gemini-oppsett
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# E-poster som skal ignoreres (katalogenes egne, noreply, osv.)
IGNORED_EMAIL_PATTERNS = {
    "noreply", "no-reply", "mailer-daemon", "postmaster",
    "webmaster", "hostmaster", "abuse", "example",
    "kundeservice", "support", "kontakt", "post",  # Generic prefixes often found on directory sites for the directory itself
}

IGNORED_EMAIL_DOMAINS = {
    "example.com", "example.no", "test.com", "sentry.io",
    "gulesider.no", "proff.no", "1881.no", "google.com",
    "facebook.com", "instagram.com", "twitter.com",
    "wixpress.com", "squarespace.com", "wordpress.com",
    "domene.no", "domeneshop.no", "registrator.no",
    "microsoft.com", "outlook.com", "hotmail.com", "gmail.com", # Generic domains require stricter validation
    "yahoo.com", "icloud.com", "online.no", "live.com", "live.no"
}

# Domains allowed even if generic, if we can verify the user part matches (not implemented yet, but good to have)
GENERIC_DOMAINS = {
    "outlook.com", "hotmail.com", "gmail.com", "yahoo.com", "icloud.com", "online.no", "live.com", "live.no",
    "vikenfiber.no", "altibox.no", "getmail.no", "c2i.net"
}

# Bildefiler som noen ganger dukker opp i mailto-lignende strenger
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def enrich_emails(leads: list[dict], location_name: str, gemini_api_key: str | None) -> None:
    """Berik leads med e-postadresser. Muterer listen in-place."""
    enriched = 0
    for i, lead in enumerate(leads):
        if lead.get("email"):
            continue

        name = lead.get("name", "")
        print(f"  [{i+1}/{len(leads)}] E-post-søk: {name}")

        # Tier 1: Norske kataloger (Stricter parsing)
        email = _scrape_directories(name, location_name)

        # Tier 2: Google + Gemini fallback
        if not email and gemini_api_key:
            email = _google_gemini_extract(name, location_name, gemini_api_key)

        if email:
            lead["email"] = email
            enriched += 1
            print(f"    -> Fant e-post: {email}")
        else:
            print(f"    -> Ingen e-post funnet")

        if i < len(leads) - 1:
            time.sleep(1)

    print(f"\nE-postberikelse ferdig: {enriched}/{len(leads)} leads fikk e-post")


def _scrape_directories(name: str, location_name: str) -> str:
    """Tier 1: Søk i norske kataloger etter e-post med spesifikk parsing."""
    encoded_name = quote_plus(name)
    encoded_name_loc = quote_plus(f"{name} {location_name}")
    
    # 1. Proff.no (High quality structured data)
    proff_url = f"https://www.proff.no/bransjes%C3%B8k?q={encoded_name}"
    email = _extract_from_proff(proff_url, name)
    if email:
        return email
    
    # 2. 1881.no
    g1881_url = f"https://www.1881.no/?query={encoded_name_loc}&type=business"
    email = _extract_from_1881(g1881_url, name)
    if email:
        return email

    # 3. Gulesider (Often requires JS or is blocked, but worth a try with specific targeting if possible)
    # Gulesider is hard to scrape reliably without JS, often returns 403 or captcha. 
    # Skipping aggressive scraping here to avoid IP bans, relying on Proff/1881/Google.
    
    return ""


def _extract_from_proff(url: str, business_name: str) -> str:
    """Extract email specifically from Proff search results or detailed page."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        if resp.status_code != 200:
            return ""
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Proff usually lists companies. We need to find the specific company entry.
        # This approach looks for mailto links within the result list, verifying the company name.
        # Note: Proff structure changes, but 'mailto:' links are standard.
        
        # Look for the specific company listing if possible (simple heuristic: name match in link text or nearby)
        # For now, let's look for any mailto link that looks valid and is NOT a generic Proff/ad link.
        
        candidates = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:'):
                email = href.replace('mailto:', '').split('?')[0].strip()
                if _is_valid_email(email) and _is_safe_email(email, business_name):
                    candidates.append(email)
        
        return _pick_best_email(candidates, business_name, strict=True)

    except Exception:
        return ""


def _extract_from_1881(url: str, business_name: str) -> str:
    """Extract email from 1881.no."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        if resp.status_code != 200:
            return ""
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1881 result list. Key is to find the row corresponding to the company name.
        # But for robustness, we just grab valid emails and STRICTLY validate them against the company name.
        
        candidates = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:'):
                email = href.replace('mailto:', '').split('?')[0].strip()
                if _is_valid_email(email) and _is_safe_email(email, business_name):
                    candidates.append(email)
        
        return _pick_best_email(candidates, business_name, strict=True)

    except Exception:
        return ""


def _google_gemini_extract(name: str, location_name: str, gemini_api_key: str) -> str:
    """Tier 2: Google-søk + regex/Gemini-ekstraksjon."""
    if google_search is None:
        return ""

    query = f'"{name}" {location_name} epost kontakt'
    try:
        search_results = list(google_search(query, num_results=5))
    except Exception as e:
        print(f"    Google-søk feilet: {e}")
        return ""

    for url in search_results:
        try:
            # Skip catalogs in Google results if we already checked them naturally
            domain = urlparse(url).hostname or ""
            if any(c in domain for c in ["proff.no", "1881.no", "gulesider.no"]):
               continue

            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )
            if resp.status_code != 200:
                continue

            # 1. Strict Regex match first
            emails = _extract_emails_from_text(resp.text)
            best = _pick_best_email(emails, name, strict=True)
            if best:
                print(f"    Fant via Web/Regex: {best}")
                return best

            # 2. Gemini fallback (more expensive, so do it if strict regex failed)
            # Use BeautifulSoup to get clean text
            soup = BeautifulSoup(resp.text, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)
            
            if len(page_text) > 100:
                email = _gemini_extract_email(page_text[:8000], name, gemini_api_key) # Increased context limit slightly
                if email:
                    print(f"    Fant via Gemini: {email}")
                    return email

        except requests.RequestException:
            continue

        time.sleep(1)

    return ""


def _extract_emails_from_text(text: str) -> list[str]:
    """Ekstraher e-postadresser fra tekst med regex + filtrering."""
    raw = EMAIL_REGEX.findall(text)
    valid = []
    seen = set()
    for email in raw:
        email = email.lower().strip(".")
        if email in seen:
            continue
        seen.add(email)
        if _is_valid_email(email):
            valid.append(email)
    return valid


def _is_safe_email(email: str, business_name: str) -> bool:
    """
    Check if email is 'safe' to associate with the business.
    Filters out obvious catalog/competitor emails.
    """
    local, _, domain = email.rpartition("@")
    
    # 1. Check if domain is in ignored list (e.g. facebook.com, 1881.no)
    if domain in IGNORED_EMAIL_DOMAINS:
        # Special case: Generic domains (gmail, etc) ARE checked later in _pick_best_email
        # But catalog domains like proff.no are strictly forbidden here
        if domain not in GENERIC_DOMAINS:
            return False

    return True


def _is_valid_email(email: str) -> bool:
    """Strukturell validering av e-post."""
    if len(email) < 5 or len(email) > 254:
        return False
    if ".." in email:
        return False

    local, _, domain = email.rpartition("@")
    if not local or not domain:
        return False

    # Sjekk TLD
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) < 2:
        return False

    # Ignorer bildefiler
    for ext in IMAGE_EXTENSIONS:
        if email.endswith(ext):
            return False

    # Ignorer kjente uønskede prefikser som "noreply" etc.
    local_lower = local.lower()
    for pattern in ["noreply", "no-reply", "mailer-daemon", "abuse"]:
        if local_lower.startswith(pattern):
            return False

    return True


def _pick_best_email(emails: list[str], business_name: str, strict: bool = False) -> str:
    """
    Velg beste e-post.
    STRICT MODE: Only accepts emails where:
    1. The domain strictly matches the business name (fuzzy match).
    2. OR matches specific reliable patterns.
    """
    if not emails:
        return ""

    norm_name = re.sub(r"[^a-z0-9]", "", business_name.lower())
    
    # Pre-calculate normalized domains
    candidates = []
    for email in emails:
        _, _, domain = email.rpartition("@")
        norm_domain = re.sub(r"[^a-z0-9]", "", domain.lower().split('.')[0]) # Match 'askerbil' in 'askerbil.no'
        candidates.append({'email': email, 'domain': domain, 'norm_domain': norm_domain})

    # Strategy 1: Exact/Strong Partial Domain Match
    # If the company name is "Asker Bilverksted", look for "@askerbilverksted.no" or "@askerbil.no"
    for cand in candidates:
        # Check if business name is contained in domain OR domain is contained in business name
        # But we need to be careful. 'asker' is in 'askerbilverksted', but 'asker' shouldn't match 'askerfrisor.no'
        
        # 1. Domain is substring of Company Name (e.g. Company: "Asker Bil", Domain: "askerbil.no")
        # 2. Company Name is substring of Domain (e.g. "Asker Bil", "askerbilverksted.no")
        
        # To be safe: Normalized domain should be inside normalized name, OR normalized name inside normalized domain
        # AND length match should be significant.
        
        # Allow generic domains to be skipped in this step
        if cand['domain'] in GENERIC_DOMAINS:
            continue
            
        if norm_name and (norm_name in cand['norm_domain'] or cand['norm_domain'] in norm_name):
             # Ensure the match is substantial (e.g. > 4 chars) to avoid matching "as" in "atlas"
             if len(cand['norm_domain']) > 3:
                 return cand['email']

    # Strategy 2: Relaxed Match (only if not strict)
    # If strict is True (default for this new version), we return "" if no strong match found.
    # The user complained about bad matches, so we want to be strict.
    
    # Exception: If we have a generic domain (gmail), check if local part matches company name significantly.
    # e.g. "Asker Bil" -> "askerbil@gmail.com"
    for cand in candidates:
        if cand['domain'] in GENERIC_DOMAINS:
            local = cand['email'].split('@')[0]
            norm_local = re.sub(r"[^a-z0-9]", "", local.lower())
            
            # Check if local part is in company name OR company name is in local part
            # e.g. local="omegavvs", name="omegavvsberger" -> Match!
            # e.g. local="askerbilservice", name="askerbil" -> Match!
            
            if len(norm_local) < 4: # innovative short emails like "avb@gmail.com" for "Asker..." risky
                continue

            if norm_name and (norm_name in norm_local or norm_local in norm_name):
                 return cand['email']

    return ""


def _gemini_extract_email(page_text: str, business_name: str, api_key: str) -> str:
    """Bruk Gemini til å ekstrahere e-post fra sidetekst med streng instruks."""
    prompt = (
        f"Finn e-postadressen til bedriften «{business_name}» fra teksten nedenfor.\n"
        "VIKTIG: Svar KUN med e-postadressen til DENNE bedriften.\n"
        "Hvis du er usikker, eller hvis e-posten tilhører en annen bedrift/katalogtjeneste, svar «INGEN».\n"
        "Svar KUN med e-postadressen, ingen annen tekst.\n\n"
        f"TEKST:\n{page_text}"
    )

    max_retries = 2
    delay = 1.0
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                GEMINI_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                    "Referer": "http://localhost:5175",
                },
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                },
                timeout=15,
            )
            if resp.status_code == 429 and attempt < max_retries:
                delay = min(delay * 2, 16)
                print(f"    Gemini rate limit, venter {delay}s...")
                time.sleep(delay)
                continue

            if resp.status_code != 200:
                return ""

            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )

            if "INGEN" in text.upper() or not text:
                return ""

            # Ekstraher e-post fra svaret
            match = EMAIL_REGEX.search(text)
            if match:
                email = match.group(0).lower()
                if _is_valid_email(email):
                    # We can trust Gemini a bit more, but still apply strict safety check for domains
                    if _is_safe_email(email, business_name):
                        return email

            return ""

        except requests.RequestException:
            return ""

    return ""
