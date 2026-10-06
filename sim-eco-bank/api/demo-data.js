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
    const [profileResult, scoreResult, commitmentsResult] = await Promise.all([
      fetch(BASE_URL + "/v1/integrations/customers/" + CUSTOMER_ID, { headers }),
      fetch(BASE_URL + "/v1/integrations/customers/" + CUSTOMER_ID + "/score", { headers }),
      fetch(BASE_URL + "/v1/integrations/customers/" + CUSTOMER_ID + "/commitments", { headers }),
    ]);
    if (!profileResult.ok || !scoreResult.ok || !commitmentsResult.ok) {
      return response.status(502).json({ error: "Sura API request failed." });
    }
    const [profile, score, commitments] = await Promise.all([
      profileResult.json(),
      scoreResult.json(),
      commitmentsResult.json(),
    ]);
    const activeCommitment = commitments.find((commitment) => commitment.status === "active") || null;
    const detailResult = activeCommitment
      ? await fetch(
        BASE_URL + "/v1/integrations/customers/" + CUSTOMER_ID + "/commitments/" + activeCommitment.commitment_id,
        { headers },
      )
      : null;
    const commitmentDetail = detailResult && detailResult.ok ? await detailResult.json() : null;
    return response.status(200).json({
      profile,
      score,
      commitments,
      active_commitment: activeCommitment,
      active_commitment_detail: commitmentDetail,
      fetched_at: new Date().toISOString(),
    });
  } catch {
    return response.status(502).json({ error: "Sura API is unavailable." });
  }
}
