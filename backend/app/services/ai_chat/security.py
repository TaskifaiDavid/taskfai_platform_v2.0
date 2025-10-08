"""
SQL security validator for AI-generated queries
"""

import re
from typing import Optional, List
import sqlparse
from sqlparse.sql import Statement, IdentifierList, Identifier, Where, Token
from sqlparse.tokens import Keyword, DML


class QuerySecurityValidator:
    """
    Validate and secure AI-generated SQL queries

    Security Rules:
    1. Only SELECT statements allowed
    2. No modification keywords (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE)
    3. No dangerous functions (pg_sleep, pg_terminate_backend, etc.)
    4. Must include user_id filter (auto-injected if missing)
    5. No semicolons (prevents query chaining)
    6. No comments (prevents SQL injection via comments)
    """

    # Dangerous SQL keywords
    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "REPLACE", "MERGE", "GRANT", "REVOKE",
        "EXEC", "EXECUTE", "CALL"
    ]

    # Dangerous PostgreSQL functions
    FORBIDDEN_FUNCTIONS = [
        "pg_sleep", "pg_terminate_backend", "pg_cancel_backend",
        "pg_read_file", "pg_write_file", "pg_ls_dir",
        "dblink", "copy"
    ]

    # Tables that require user_id filtering
    USER_SCOPED_TABLES = [
        "sellout_entries2",
        "ecommerce_orders",
        "upload_batches",
        "error_reports",
        "conversation_history",
        "dashboard_configs",
        "email_logs"
    ]

    def validate_and_inject_user_filter(
        self,
        sql_query: str,
        user_id: str
    ) -> str:
        """
        Validate SQL query and inject user_id filter

        Args:
            sql_query: SQL query to validate
            user_id: User identifier to inject into WHERE clause

        Returns:
            Validated and filtered SQL query

        Raises:
            ValueError: If query is invalid or dangerous
        """
        # Basic validation
        self._validate_basic_security(sql_query)

        # Parse SQL
        try:
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                raise ValueError("Unable to parse SQL query")

            statement = parsed[0]
        except Exception as e:
            raise ValueError(f"SQL parsing error: {str(e)}")

        # Validate statement type
        self._validate_statement_type(statement)

        # Validate no dangerous functions
        self._validate_no_dangerous_functions(sql_query)

        # Inject user_id filter
        filtered_query = self._inject_user_id_filter(sql_query, user_id)

        return filtered_query

    def _validate_basic_security(self, sql_query: str) -> None:
        """Basic security checks"""
        # Check for semicolons (query chaining)
        if ';' in sql_query.rstrip(';'):  # Allow trailing semicolon
            raise ValueError("Multiple statements not allowed (semicolon detected)")

        # Check for SQL comments
        if '--' in sql_query or '/*' in sql_query or '*/' in sql_query:
            raise ValueError("Comments not allowed in queries")

        # Check for dangerous keywords
        query_upper = sql_query.upper()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(rf'\b{keyword}\b', query_upper):
                raise ValueError(f"Forbidden keyword detected: {keyword}")

    def _validate_statement_type(self, statement: Statement) -> None:
        """Validate that statement is a SELECT"""
        token = statement.token_first(skip_ws=True, skip_cm=True)
        if not token or token.ttype is not Keyword.DML or token.value.upper() != 'SELECT':
            raise ValueError("Only SELECT queries are allowed")

    def _validate_no_dangerous_functions(self, sql_query: str) -> None:
        """Check for dangerous PostgreSQL functions"""
        query_lower = sql_query.lower()
        for func in self.FORBIDDEN_FUNCTIONS:
            if func.lower() in query_lower:
                raise ValueError(f"Forbidden function detected: {func}")

    def _inject_user_id_filter(self, sql_query: str, user_id: str) -> str:
        """
        Inject user_id filter into WHERE clause

        Strategy:
        1. Parse query to find tables
        2. For each user-scoped table, ensure user_id filter exists
        3. If WHERE clause exists, add AND user_id = 'xxx'
        4. If no WHERE clause, add WHERE user_id = 'xxx'
        """
        parsed = sqlparse.parse(sql_query)[0]

        # Find tables in query
        tables = self._extract_tables(parsed)

        # Check if any user-scoped tables are present
        needs_filter = any(table in self.USER_SCOPED_TABLES for table in tables)

        if not needs_filter:
            return sql_query  # No user filtering needed

        # Check if user_id filter already exists
        if self._has_user_id_filter(sql_query):
            return sql_query  # Filter already present

        # Inject user_id filter
        return self._add_user_id_filter(sql_query, user_id)

    def _extract_tables(self, statement: Statement) -> List[str]:
        """Extract table names from SQL statement"""
        tables = []

        from_seen = False
        for token in statement.tokens:
            if from_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        table_name = identifier.get_real_name()
                        if table_name:
                            tables.append(table_name)
                elif isinstance(token, Identifier):
                    table_name = token.get_real_name()
                    if table_name:
                        tables.append(table_name)
                elif token.ttype is Keyword:
                    break

            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True

        return tables

    def _has_user_id_filter(self, sql_query: str) -> bool:
        """Check if query already has user_id filter"""
        query_lower = sql_query.lower()
        return 'user_id' in query_lower and ('=' in query_lower or 'in' in query_lower)

    def _add_user_id_filter(self, sql_query: str, user_id: str) -> str:
        """
        Add user_id filter to query

        Handles:
        - Queries with existing WHERE clause
        - Queries without WHERE clause
        - Queries with subqueries (adds to main query only)
        """
        # Escape user_id for SQL
        escaped_user_id = user_id.replace("'", "''")

        # Find WHERE clause position
        where_match = re.search(r'\bWHERE\b', sql_query, re.IGNORECASE)

        if where_match:
            # WHERE clause exists - add AND condition
            where_pos = where_match.end()

            # Find the end of WHERE clause (before GROUP BY, ORDER BY, LIMIT, etc.)
            end_keywords = ['GROUP BY', 'ORDER BY', 'LIMIT', 'OFFSET', 'HAVING']
            end_pos = len(sql_query)

            for keyword in end_keywords:
                match = re.search(rf'\b{keyword}\b', sql_query[where_pos:], re.IGNORECASE)
                if match:
                    end_pos = min(end_pos, where_pos + match.start())

            # Extract WHERE clause
            where_clause = sql_query[where_pos:end_pos].strip()

            # Add user_id condition
            user_filter = f" user_id = '{escaped_user_id}' AND ({where_clause})"

            # Reconstruct query
            filtered_query = (
                sql_query[:where_pos] +
                user_filter +
                sql_query[end_pos:]
            )

        else:
            # No WHERE clause - add one
            # Find position to insert WHERE (before GROUP BY, ORDER BY, etc.)
            insert_keywords = ['GROUP BY', 'ORDER BY', 'LIMIT', 'OFFSET', 'HAVING']
            insert_pos = len(sql_query.rstrip(';'))

            for keyword in insert_keywords:
                match = re.search(rf'\b{keyword}\b', sql_query, re.IGNORECASE)
                if match:
                    insert_pos = min(insert_pos, match.start())

            # Add WHERE clause
            where_clause = f" WHERE user_id = '{escaped_user_id}' "

            filtered_query = (
                sql_query[:insert_pos].rstrip() +
                where_clause +
                sql_query[insert_pos:]
            )

        return filtered_query.strip()

    def sanitize_user_input(self, user_input: str) -> str:
        """
        Sanitize user input for use in SQL queries

        Args:
            user_input: Raw user input

        Returns:
            Sanitized input safe for SQL
        """
        # Remove dangerous characters
        sanitized = user_input.replace("'", "''")  # Escape single quotes
        sanitized = sanitized.replace(";", "")     # Remove semicolons
        sanitized = sanitized.replace("--", "")    # Remove SQL comments
        sanitized = sanitized.replace("/*", "")    # Remove block comments
        sanitized = sanitized.replace("*/", "")

        return sanitized

    def validate_query_result_size(
        self,
        sql_query: str,
        max_rows: int = 10000
    ) -> str:
        """
        Ensure query has LIMIT clause to prevent excessive results

        Args:
            sql_query: SQL query
            max_rows: Maximum allowed rows

        Returns:
            Query with LIMIT added if missing
        """
        if not re.search(r'\bLIMIT\b', sql_query, re.IGNORECASE):
            # Add LIMIT clause
            sql_query = sql_query.rstrip(';') + f" LIMIT {max_rows}"

        return sql_query


# Alias for backwards compatibility
SQLSecurityValidator = QuerySecurityValidator
