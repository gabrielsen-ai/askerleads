import { useState, useEffect } from "react";
import type { Lead } from "../types/Lead";
import { supabase } from "../lib/supabaseClient";

// Konverterer database-feltnavn (snake_case) til TypeScript (camelCase)
function mapDbLeadToLead(dbLead: any): Lead {
  return {
    id: dbLead.id,
    name: dbLead.name,
    address: dbLead.address,
    rating: dbLead.rating,
    userRatingCount: dbLead.user_rating_count,
    industry: dbLead.industry,
    phone: dbLead.phone,
    sted: dbLead.email,
    hasWebsite: dbLead.has_website,
    potentialScore: dbLead.potential_score,
    info: dbLead.info,
    source: dbLead.source || "google_places",
    status: dbLead.status,
    last_called_at: dbLead.last_called_at,
    last_called_by: dbLead.last_called_by,
    notes: dbLead.notes,
    created_at: dbLead.created_at,
    updated_at: dbLead.updated_at,
  };
}

export function useLeads(source: string = "/leads.json") {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeads = async () => {
      setLoading(true);
      try {
        const { data, error } = await supabase
          .from("leads")
          .select("*")
          .order("potential_score", { ascending: false });

        if (error) {
          console.error("Feil ved henting av leads:", error);
          setLeads([]);
        } else {
          // Konverter database-format til TypeScript-format
          const mappedLeads = (data || []).map(mapDbLeadToLead);
          setLeads(mappedLeads);
        }
      } catch (err) {
        console.error("Feil ved henting av leads:", err);
        setLeads([]);
      } finally {
        setLoading(false);
      }
    };

    fetchLeads();
  }, [source]);

  return { leads, loading };
}
