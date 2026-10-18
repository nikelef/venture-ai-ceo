-- Apply to the dedicated, initially empty Venture project only.
CREATE TABLE IF NOT EXISTS validation_sessions (
  id text PRIMARY KEY,
  created_at bigint NOT NULL,
  source text NOT NULL,
  role text NOT NULL,
  measurement boolean NOT NULL,
  test boolean NOT NULL DEFAULT false,
  flags integer NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS validation_interest (
  email_hash text PRIMARY KEY,
  encrypted_contact text NOT NULL,
  receipt_hash text UNIQUE NOT NULL,
  created_at bigint NOT NULL,
  source text NOT NULL,
  role text NOT NULL,
  platform text NOT NULL,
  timing text NOT NULL,
  problem text NOT NULL,
  pilot boolean NOT NULL,
  willingness text NOT NULL,
  price_cents integer NOT NULL CHECK (price_cents = 900),
  currency text NOT NULL CHECK (currency = 'EUR'),
  consent_version text NOT NULL,
  test boolean NOT NULL DEFAULT false,
  independently_verified boolean NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS validation_limits (
  day text PRIMARY KEY,
  admissions integer NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS validation_sessions_date ON validation_sessions(created_at);
CREATE INDEX IF NOT EXISTS validation_interest_date ON validation_interest(created_at);
-- No orders, payments, catalog contents, names, store URLs, IPs or user agents.
