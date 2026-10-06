const CUSTOMER_ID = "usr_demo_amara";
const BASE_URL = process.env.SURA_API_BASE_URL || "https://sura-3y09.onrender.com";

export default async function handler(request, response) {
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    return response.status(405).json({ error: "Method not allowed." });
  }

  const apiKey = process.env.SURA_DEMO_API_KEY;
  if (!apiKey) return response.status(503).json({ error: "Demo API is not configured." });

  try {
    const headers = { "X-Sura-API-Key": apiKey, accept: "application/json" };
    const [scoreResult, commitmentsResult] = await Promise.all([
      fetch(BASE_URL + "/v1/integrations/customers/" + CUSTOMER_ID + "/score", { headers }),
      fetch(BASE_URL + "/v1/integrations/customers/" + CUSTOMER_ID + "/commitments", { headers }),
    ]);
    if (!scoreResult.ok || !commitmentsResult.ok) {
      return response.status(502).json({ error: "Sura API request failed." });
    }
    const [score, commitments] = await Promise.all([scoreResult.json(), commitmentsResult.json()]);
    return response.status(200).json({
      score,
      active_commitment: commitments.find((commitment) => commitment.status === "active") || null,
    });
  } catch {
    return response.status(502).json({ error: "Sura API is unavailable." });
  }
}
