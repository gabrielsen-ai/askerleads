import type { Lead } from "../types/Lead";
import { ASKER_LOCATION, SEARCH_CONFIG, INDUSTRIES } from "../config/constants";
import { calculateScore } from "../utils/scoreCalculator";

const DIRECT_API_URL = "https://places.googleapis.com/v1/places:searchNearby";
const PROXY_API_URL = "/api/places";
const API_URL = import.meta.env.DEV ? PROXY_API_URL : DIRECT_API_URL;

function guessIndustry(types: string[]): string {
  const map: Record<string, string> = {
    plumber: "Plumber",
    electrician: "Electrician",
    painter: "Painter",
    florist: "Florist",
    cafe: "Cafe",
    bakery: "Bakery",
    hair_care: "Hair Salon",
    beauty_salon: "Hair Salon",
    car_repair: "Auto Repair",
    car_wash: "Auto Repair",
    furniture_store: "Carpenter",
    home_improvement_store: "Carpenter",
    house_cleaning: "Cleaning Service",
  };
  for (const t of types) {
    if (map[t]) return map[t];
  }
  return INDUSTRIES[Math.floor(Math.random() * INDUSTRIES.length)];
}

function isValidWebsiteUri(value: unknown): boolean {
  if (typeof value !== "string") return false;
  const trimmed = value.trim();
  if (!trimmed) return false;
  try {
    const url = new URL(trimmed);
    if (url.protocol !== "http:" && url.protocol !== "https:") return false;
    if (!url.hostname || !url.hostname.includes(".")) return false;
    return true;
  } catch {
    return false;
  }
}

export async function fetchLeadsFromGoogle(apiKey: string): Promise<Lead[]> {
  const TARGET_RESULTS = 1000;
  const MAX_PAGES = 50;
  const MAX_RADIUS = 50000;
  const RADIUS_GROWTH = 2;
  const EXCLUDED_TYPES = new Set([
    "airport",
    "bus_station",
    "bus_stop",
    "ferry_terminal",
    "light_rail_station",
    "park",
    "parking",
    "point_of_interest",
    "premise",
    "route",
    "street_address",
    "subway_station",
    "train_station",
    "transit_station",
  ]);
  const results: Lead[] = [];
  const seenIds = new Set<string>();
  let radius = SEARCH_CONFIG.radius;

  while (results.length < TARGET_RESULTS && radius <= MAX_RADIUS) {
    let nextPageToken: string | undefined;
    let pageCount = 0;

    while (results.length < TARGET_RESULTS && pageCount < MAX_PAGES) {
      const body = {
        maxResultCount: SEARCH_CONFIG.maxResults,
        locationRestriction: {
          circle: {
            center: ASKER_LOCATION,
            radius,
          },
        },
        ...(nextPageToken ? { pageToken: nextPageToken } : {}),
      };

      const res = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Goog-Api-Key": apiKey,
          "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.types,places.nationalPhoneNumber,places.websiteUri,places.id",
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`Google Places API error: ${res.status}`);

      const data = await res.json();
      const places: any[] = data.places ?? [];
      nextPageToken = data.nextPageToken;
      pageCount += 1;

      const pageLeads = places
        .filter((p: any) => {
          const types: string[] = p.types ?? [];
          if (types.length === 0) return false;
          return !types.some((t) => EXCLUDED_TYPES.has(t));
        })
        .map((p: any, i: number): Lead => {
          const hasWebsite = isValidWebsiteUri(p.websiteUri);
          const rating = p.rating ?? 0;
          const userRatingCount = p.userRatingCount ?? 0;
          return {
            id: p.id ?? `goog-${radius}-${pageCount}-${i}`,
            name: p.displayName?.text ?? "Unknown",
            address: p.formattedAddress ?? "",
            rating,
            userRatingCount,
            industry: guessIndustry(p.types ?? []),
            phone: p.nationalPhoneNumber ?? "",
            hasWebsite,
            potentialScore: calculateScore(rating, userRatingCount, hasWebsite),
          };
        });

      for (const lead of pageLeads) {
        if (!seenIds.has(lead.id)) {
          seenIds.add(lead.id);
          results.push(lead);
        }
      }

      if (!nextPageToken) break;
    }

    if (results.length < TARGET_RESULTS) {
      radius *= RADIUS_GROWTH;
    }
  }

  return results
    .sort((a, b) => {
      if (a.hasWebsite !== b.hasWebsite) {
        return a.hasWebsite ? 1 : -1;
      }
      return b.rating !== a.rating
        ? b.rating - a.rating
        : b.userRatingCount - a.userRatingCount;
    })
    .slice(0, TARGET_RESULTS);
}
