import { useState, useEffect } from "react";
import type { Lead } from "../types/Lead";
import { fetchLeadsFromGoogle } from "../services/googlePlaces";

export function useLeads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = () => setReloadKey((value) => value + 1);

  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_PLACES_API_KEY;

    setLeads([]);
    setLoading(true);

    if (!apiKey) {
      setLoading(false);
      return;
    }

    fetchLeadsFromGoogle(apiKey)
      .then((results) => {
        setLeads(results);
      })
      .catch(() => {
        setLeads([]);
      })
      .finally(() => setLoading(false));
  }, [reloadKey]);

  return { leads, loading, reload };
}
