# Sim_eco_bank

Standalone simulated-bank demo for the Sura hackathon walkthrough.

It reads only the seeded Amara customer’s approved Score and Lock records through
a server-side proxy. The browser never receives the Sura sandbox API key.

## Vercel configuration

Set the Vercel project root directory to sim-eco-bank, then add:

~~~
SURA_API_BASE_URL=https://sura-3y09.onrender.com
SURA_DEMO_API_KEY=<sandbox key>
~~~

Do not use a NEXT_PUBLIC_ prefix for the API key.
