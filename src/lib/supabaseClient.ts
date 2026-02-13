import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Mangler Supabase-miljøvariabler. Sjekk at VITE_SUPABASE_URL og VITE_SUPABASE_ANON_KEY er satt i .env");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
