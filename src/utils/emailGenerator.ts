import type { Lead } from "../types/Lead";

export function generateEmail(lead: Lead): string {
  return `Hei ${lead.name},

Jeg kom over bedriften deres da jeg søkte etter ${lead.industry.toLowerCase()}-tjenester i Asker-området, og jeg ble imponert over den flotte vurderingen deres på ${lead.rating} stjerner basert på ${lead.userRatingCount} anmeldelser — det er tydelig at kundene deres setter pris på arbeidet dere gjør!

Jeg la merke til at dere for øyeblikket ikke har en nettside, og jeg tror det er en stor mulighet for dere. En profesjonell nettside kan hjelpe nye kunder med å finne dere lettere og vise frem det gode arbeidet som allerede gjenspeiles i anmeldelsene deres.

Jeg driver et digitalt byrå som spesialiserer seg på å bygge nettsider for lokale bedrifter som deres. Jeg vil gjerne vise dere noen eksempler på hva vi har gjort for lignende bedrifter i området.

Har dere tid til en kort, uforpliktende samtale denne uken?

Med vennlig hilsen,
[Ditt navn]
[Ditt byrå]`;
}
