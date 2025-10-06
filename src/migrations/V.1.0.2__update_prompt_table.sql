DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='prompts' and column_name='agent_group'
  ) THEN
    ALTER TABLE prompts ADD COLUMN agent_group VARCHAR(255);
  END IF;
END
$$;
