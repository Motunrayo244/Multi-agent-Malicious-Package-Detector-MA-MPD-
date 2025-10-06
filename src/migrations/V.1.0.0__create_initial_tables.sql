CREATE SCHEMA IF NOT EXISTS EXPERIMENTS;
SET search_path TO EXPERIMENTS;

CREATE EXTENSION IF NOT EXISTS pgcrypto;


CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();         
  RETURN NEW;
END;
$$;

-- Evaluation Table
CREATE TABLE IF NOT EXISTS evaluation (
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classification_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    classification_correct BOOLEAN NOT NULL,
    evaluation_metadata JSONB NOT NULL,
    evaluation_kb_uuids UUID NULL
);

CREATE TABLE IF NOT EXISTS prompts (
    prompt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent TEXT NOT NULL,
    evaluation_id UUID REFERENCES evaluation(evaluation_id),
    status TEXT NOT NULL,
    prompt TEXT NOT NULL
);


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'classification_label'
    ) THEN
        CREATE TYPE classification_label AS ENUM ('benign', 'malicious');
    END IF;
END
$$;


CREATE TABLE IF NOT EXISTS classification (
    classification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name TEXT NOT NULL,
    package_metadata JSONB NOT NULL,
    classification classification_label NOT NULL,
    justification TEXT NOT NULL,
    suspicious_files TEXT[] NOT NULL  DEFAULT '{}'::text[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    prompt_id UUID REFERENCES prompts(prompt_id)
);


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        JOIN pg_namespace n ON t.relnamespace = n.oid
        WHERE c.contype = 'f'
          AND c.conname = 'fk_evaluation_classification'
          AND t.relname = 'evaluation'
          AND n.nspname = 'experiments'
    ) THEN
        ALTER TABLE evaluation
        ADD CONSTRAINT fk_evaluation_classification
        FOREIGN KEY (classification_id) REFERENCES classification(classification_id);
    END IF;
END
$$;

-- Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation(evaluation_id),
    classification_id UUID REFERENCES classification(classification_id),
    agent_feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_classification_touch'
          AND tgrelid = 'classification'::regclass
    ) THEN
        CREATE TRIGGER trg_classification_touch
        BEFORE UPDATE ON classification
        FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
    END IF;
END
$$;



CREATE INDEX IF NOT EXISTS idx_prompts_created_at ON prompts(created_at);
CREATE INDEX IF NOT EXISTS idx_prompts_evaluation_id ON prompts(evaluation_id);
CREATE INDEX IF NOT EXISTS classification_pkg_name_idx
    ON classification(package_name);
CREATE INDEX IF NOT EXISTS classification_created_at_idx
    ON classification(created_at);
