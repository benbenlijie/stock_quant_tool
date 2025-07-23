-- Migration to fix existing null dates in backtest_results
-- Created at: 1753287917

-- Update existing records with null start_date or end_date
-- Set them to reasonable defaults based on created_at timestamp

UPDATE backtest_results 
SET start_date = CASE 
    WHEN start_date IS NULL THEN 
        COALESCE(created_at::date - INTERVAL '30 days', '2025-01-01'::date)
    ELSE start_date
END,
end_date = CASE 
    WHEN end_date IS NULL THEN 
        COALESCE(created_at::date - INTERVAL '1 day', '2025-01-24'::date)
    ELSE end_date
END
WHERE start_date IS NULL OR end_date IS NULL;

-- Now make start_date and end_date NOT NULL
ALTER TABLE backtest_results 
ALTER COLUMN start_date SET NOT NULL,
ALTER COLUMN end_date SET NOT NULL;

-- Add check constraints to ensure logical date order
ALTER TABLE backtest_results 
ADD CONSTRAINT check_date_order 
CHECK (start_date <= end_date);

-- Add check constraint to ensure dates are not too far in the future
ALTER TABLE backtest_results 
ADD CONSTRAINT check_reasonable_dates 
CHECK (start_date >= '2020-01-01' AND end_date <= CURRENT_DATE + INTERVAL '1 year');