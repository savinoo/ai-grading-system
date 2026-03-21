CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.auth_refresh_tokens (
    id BIGSERIAL PRIMARY KEY,

    -- Identificador único do token (claim jti)
    jti UUID NOT NULL,

    -- Subject do token (referência ao usuário, ex: users.uuid)
    subject UUID NOT NULL,

    -- Versão do token (útil para invalidação em massa)
    token_version INTEGER NOT NULL DEFAULT 1,

    -- Tipo do token (fixo como REFRESH)
    token_type VARCHAR(20) NOT NULL DEFAULT 'REFRESH',

    -- Claims temporais
    issued_at TIMESTAMPTZ NOT NULL,
    not_before TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,

    -- Estado do token
    key_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    -- Escopos associados ao token
    scopes TEXT[] NOT NULL,

    -- IP de emissão do token
    issued_ip INET NULL,

    -- Data de revogação (quando aplicável)
    revoked_at TIMESTAMPTZ NULL,

    -- Auditoria
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Garantias básicas de integridade
    CONSTRAINT chk_token_type
        CHECK (token_type = 'REFRESH'),

    CONSTRAINT chk_key_status
        CHECK (key_status IN ('ACTIVE', 'ROTATED', 'REVOKED', 'EXPIRED')),

    CONSTRAINT chk_token_dates
        CHECK (
            issued_at <= not_before
            AND not_before < expires_at
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_refresh_tokens_jti
ON public.auth_refresh_tokens (jti);

CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_subject
ON public.auth_refresh_tokens (subject);

CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_valid
ON public.auth_refresh_tokens (subject, expires_at)
WHERE revoked_at IS NULL AND key_status = 'ACTIVE';

ALTER TABLE public.auth_refresh_tokens
ADD CONSTRAINT fk_auth_refresh_tokens_user
FOREIGN KEY (subject)
REFERENCES public.users(uuid)
ON UPDATE CASCADE
ON DELETE CASCADE;

