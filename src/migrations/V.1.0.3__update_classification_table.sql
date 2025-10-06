-- 1. Add column if not exists, nullable and without NOT NULL constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'experiments' AND table_name='classification' AND column_name='model'
  ) THEN
    ALTER TABLE experiments.classification ADD COLUMN model text;
  END IF;
END
$$;

-- 2. Update existing NULLs to default value
UPDATE experiments.classification
SET model = 'undefined'
WHERE model IS NULL;

-- 3. Set default value for future inserts
ALTER TABLE experiments.classification
ALTER COLUMN model SET DEFAULT 'undefined';

-- 4. Alter column to NOT NULL now that data is clean
ALTER TABLE experiments.classification
ALTER COLUMN model SET NOT NULL;
