import type { Lead } from "../types/Lead";

export function filterLeads(leads: Lead[], industries: string[], search: string): Lead[] {
  let result = leads;
  if (industries.length > 0) {
    result = result.filter((l) => industries.includes(l.industry));
  }
  if (search.trim()) {
    const q = search.toLowerCase();
    result = result.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.address.toLowerCase().includes(q) ||
        l.industry.toLowerCase().includes(q)
    );
  }
  return result;
}

export function sortLeadsByScore(leads: Lead[]): Lead[] {
  return [...leads].sort((a, b) => b.potentialScore - a.potentialScore);
}
