export interface Lead {
  id: string;
  name: string;
  address: string;
  rating: number;
  userRatingCount: number;
  industry: string;
  phone: string;
  email: string;
  hasWebsite: boolean;
  potentialScore: number;
  info: string;
  
  // Supabase-felter
  status?: "pending" | "accepted" | "rejected" | "no_answer" | "call_later";
  last_called_at?: string;
  last_called_by?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}
