-- ABOUTME: Creates exec_sql RPC function for AI chat system to execute dynamic SQL queries
-- ABOUTME: This function enables the chat agent to query tenant databases securely with proper error handling

-- Create exec_sql function for executing dynamic SQL queries from AI chat
-- This function is called by the chat system in backend/app/api/chat.py line 54
CREATE OR REPLACE FUNCTION public.exec_sql(query TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result_json JSONB;
    row_count INTEGER;
BEGIN
    -- Security: Prevent DDL operations (CREATE, DROP, ALTER, TRUNCATE)
    IF query ~* '^\s*(CREATE|DROP|ALTER|TRUNCATE|DELETE|INSERT|UPDATE)\s' THEN
        RAISE EXCEPTION 'Only SELECT queries are allowed. DDL and DML operations are prohibited.';
    END IF;

    -- Security: Prevent multiple statements (prevents SQL injection via semicolons)
    IF query ~ ';.*[A-Za-z]' THEN
        RAISE EXCEPTION 'Multiple statements are not allowed';
    END IF;

    -- Execute the query and convert result to JSON
    BEGIN
        EXECUTE format('SELECT jsonb_agg(row_to_json(t)) FROM (%s) t', query) INTO result_json;

        -- If no results, return empty array instead of null
        IF result_json IS NULL THEN
            result_json := '[]'::jsonb;
        END IF;

        RETURN result_json;
    EXCEPTION
        WHEN OTHERS THEN
            -- Return error details as JSON
            RETURN jsonb_build_object(
                'error', TRUE,
                'message', SQLERRM,
                'detail', SQLSTATE,
                'query', query
            );
    END;
END;
$$;

-- Grant execute permission to authenticated users (chat system uses service role)
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO service_role;

-- Add comment explaining function purpose
COMMENT ON FUNCTION public.exec_sql(TEXT) IS 'Executes SELECT queries for AI chat system. Only allows SELECT statements for security. Returns results as JSONB array.';
