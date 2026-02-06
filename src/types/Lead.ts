export interface Lead {
  id: string;
  name: string;
  address: string;
  rating: number;
  userRatingCount: number;
  industry: string;
  phone: string;
  hasWebsite: boolean;
  potentialScore: number;
}
