CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT gen_random_uuid(),

    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    user_type VARCHAR(50) NOT NULL DEFAULT 'teacher',
    first_name text NOT NULL,
	last_name text NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    recovery_code_hash TEXT NULL,
    recovery_code_expires_at TIMESTAMPTZ NULL,
    recovery_code_attempts INTEGER NOT NULL DEFAULT 0,

    last_login_at TIMESTAMPTZ NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ null,
    
    CONSTRAINT chk_users_recovery_code_attempts CHECK (recovery_code_attempts >= 0),
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_uuid ON public.users (uuid);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (email);
CREATE INDEX IF NOT EXISTS idx_users_active ON public.users (active);
CREATE INDEX IF NOT EXISTS idx_users_recovery_code_expires_at ON public.users (recovery_code_expires_at);

-- ============================================
-- TRIGGER: updated_at automático
-- ============================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();
