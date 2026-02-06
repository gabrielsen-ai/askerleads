export function calculateScore(rating: number, reviewCount: number, hasWebsite: boolean): number {
  const ratingScore = (rating / 5) * 50;
  const reviewScore = Math.min(reviewCount / 5, 30);
  const noWebsiteBonus = hasWebsite ? 0 : 20;
  return Math.round(ratingScore + reviewScore + noWebsiteBonus);
}
