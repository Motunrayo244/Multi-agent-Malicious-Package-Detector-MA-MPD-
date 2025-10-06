SET search_path TO EXPERIMENTS;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- 1. Create the dataset table
CREATE TABLE IF NOT EXISTS dataset (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  package_name       TEXT        NOT NULL,
  package_location   TEXT        NOT NULL,
  subclass           TEXT        NOT NULL,
  class              TEXT        NOT NULL,
  dataset_category   TEXT        NOT NULL,
  package_size       BIGINT      NOT NULL CHECK (package_size >= 0),
  is_archived        BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Create the experiments table
CREATE TABLE IF NOT EXISTS experiments (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_name    TEXT        NOT NULL,
  experiment_status  TEXT        NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Ensure the touch_updated_at() function exists
--    (this simple plpgsql function updates updated_at on every UPDATE)
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Attach triggers to keep updated_at in sync
DO $$
BEGIN
  -- dataset.updated_at
  IF NOT EXISTS (
    SELECT 1
      FROM pg_trigger
     WHERE tgname = 'trg_dataset_touch'
       AND tgrelid = 'dataset'::regclass
  ) THEN
    CREATE TRIGGER trg_dataset_touch
      BEFORE UPDATE
      ON dataset
      FOR EACH ROW
      EXECUTE FUNCTION touch_updated_at();
  END IF;

  -- experiments.updated_at
  IF NOT EXISTS (
    SELECT 1
      FROM pg_trigger
     WHERE tgname = 'trg_experiments_touch'
       AND tgrelid = 'experiments'::regclass
  ) THEN
    CREATE TRIGGER trg_experiments_touch
      BEFORE UPDATE
      ON experiments
      FOR EACH ROW
      EXECUTE FUNCTION touch_updated_at();
  END IF;
END
$$;

-- 5. Prepare classification table (if not already created)
CREATE TABLE IF NOT EXISTS classification (
  id       UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  -- add your other classification-specific columns here
);

-- 6. Add dataset_id and experiment_id to classification
ALTER TABLE classification
  ADD COLUMN IF NOT EXISTS dataset_id     UUID,
  ADD COLUMN IF NOT EXISTS experiment_id  UUID;

-- 7. Add (or recreate) foreign-key constraints
ALTER TABLE classification
  DROP CONSTRAINT IF EXISTS fk_classification_dataset,
  ADD CONSTRAINT fk_classification_dataset
    FOREIGN KEY (dataset_id)
    REFERENCES dataset(id)
    ON DELETE RESTRICT;

ALTER TABLE classification
  DROP CONSTRAINT IF EXISTS fk_classification_experiment,
  ADD CONSTRAINT fk_classification_experiment
    FOREIGN KEY (experiment_id)
    REFERENCES experiments(id)
    ON DELETE CASCADE;

-- 8. Index the new foreign-key columns for performance
CREATE INDEX IF NOT EXISTS idx_classification_dataset_id
  ON classification(dataset_id);
CREATE INDEX IF NOT EXISTS idx_classification_experiment_id
  ON classification(experiment_id);




CREATE EXTENSION IF NOT EXISTS vector
    SCHEMA experiments
    VERSION "0.8.0";