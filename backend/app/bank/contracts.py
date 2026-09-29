"""JWT claim contract required from the authentication provider for Bank Portal access."""
BANK_PORTAL_ROLES = frozenset({"bank_admin", "bank_risk_analyst", "bank_integration_engineer"})
REQUIRED_BANK_CLAIMS = frozenset({"sub", "role", "bank_id", "permissions"})
