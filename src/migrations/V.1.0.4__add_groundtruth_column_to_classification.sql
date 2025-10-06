-- 1. Add column if not exists, nullable and without NOT NULL constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'experiments' AND table_name='classification' AND column_name='ground_truth_class'
  ) THEN
    ALTER TABLE IF EXISTS experiments.classification
    ADD COLUMN ground_truth_class experiments.classification_label;
  END IF;
END
$$;


