"""
Hybrid SQL Agent for natural language to SQL conversion with Supabase execution.

This module implements a hybrid architecture where:
- OpenAI GPT generates SQL from natural language queries
- Supabase executes queries via REST API (exec_sql RPC function)
- Security validation ensures user_id filtering on all queries

The agent prioritizes ecommerce_orders (D2C/online sales) over sellout_entries2 (B2B/offline)
to ensure accurate results for users with primarily online sales data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
import os
import re
import json
import calendar

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .intent import IntentDetector, QueryIntent
from .security import QuerySecurityValidator


# Database schema for AI context - DEMO tenant
DATABASE_SCHEMA_DEMO = """
Tables (in priority order for queries):

1. ecommerce_orders: PRIMARY sales table (D2C/online sales data) - QUERY THIS FIRST
   Columns: order_id, user_id, product_ean, functional_name, product_name, sales_eur,
            quantity, cost_of_goods, stripe_fee, order_date, country, city,
            utm_source, utm_medium, utm_campaign, device_type, reseller
   Note: Contains functional_name directly - NO JOIN to products table needed

2. sellout_entries2: B2B/offline sales data (may be empty for some users)
   Columns: sale_id, user_id, product_id, reseller_id, functional_name, product_ean,
            reseller, sales_eur, quantity, currency, month, year, created_at
   Note: Requires JOIN to products table for product_name

3. products: Product catalog (only needed for sellout_entries2 queries)
   Columns: product_id, sku, product_name, product_ean, functional_name, category

4. resellers: Reseller directory
   Columns: reseller_id, name, country

5. users: User accounts
   Columns: user_id, email, full_name, role, tenant_id
"""

# Database schema for AI context - BIBBI tenant
DATABASE_SCHEMA_BIBBI = """
Tables (in priority order for queries):

1. sales_unified: PRIMARY sales table (all reseller sales data) - QUERY THIS FIRST
   Columns: sale_id, user_id, reseller_id, product_id, functional_name, product_ean,
            product_name, quantity, sales_eur, cost_eur, month, year, store_name,
            store_country, created_at, updated_at
   Note: Unified table combining all reseller sales data with full product details

2. stores: Store/location directory
   Columns: store_id, reseller_id, store_name, city, country, created_at

3. product_reseller_mappings: Product-to-reseller mappings
   Columns: mapping_id, reseller_id, product_ean, product_name, functional_name,
            reseller_sku, created_at

4. sales_staging: Temporary upload staging (do not query)
   Note: Internal table for upload processing

5. users: User accounts
   Columns: user_id, email, full_name, role, tenant_id
"""


class SQLDatabaseAgent:
    """
    Hybrid SQL Agent: OpenAI generates SQL, Supabase MCP executes it

    Features:
    - Natural language to SQL conversion via OpenAI
    - Query execution via Supabase MCP (REST API)
    - Schema-aware query generation
    - Security validation and user filtering
    - No IPv6 connectivity required
    """

    def __init__(
        self,
        project_id: str,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        tenant_subdomain: str = "demo"
    ):
        """
        Initialize Hybrid SQL Agent

        Args:
            project_id: Supabase project ID
            openai_api_key: OpenAI API key
            model: OpenAI model name
            temperature: LLM temperature
            tenant_subdomain: Tenant subdomain for schema selection (demo, bibbi, etc.)
        """
        self.project_id = project_id
        self.tenant_subdomain = tenant_subdomain
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key required")

        # Select database schema based on tenant
        self.database_schema = DATABASE_SCHEMA_BIBBI if tenant_subdomain == "bibbi" else DATABASE_SCHEMA_DEMO

        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=model,
            temperature=temperature
        )

        # Initialize supporting services
        self.intent_detector = IntentDetector()
        self.security_validator = QuerySecurityValidator()

    def _generate_sql(self, query: str, user_id: str) -> str:
        """Generate SQL from natural language using OpenAI"""

        # Use tenant-specific database schema
        system_prompt = f"""You are a SQL expert for a sales analytics platform.

{self.database_schema}

DATABASE: PostgreSQL (Supabase)

POSTGRESQL SYNTAX RULES:
1. Date/time extraction: Use EXTRACT() function, NOT MONTH()/YEAR()
   - ✓ EXTRACT(MONTH FROM date_column)
   - ✓ EXTRACT(YEAR FROM date_column)
   - ✗ MONTH(date_column)  -- MySQL syntax, DO NOT USE
   - ✗ YEAR(date_column)   -- MySQL syntax, DO NOT USE

2. Date arithmetic: Use INTERVAL with single quotes
   - ✓ CURRENT_DATE - INTERVAL '1 month'
   - ✓ CURRENT_DATE - INTERVAL '1 year'
   - ✗ CURRENT_DATE - INTERVAL 1 MONTH  -- Incorrect, missing quotes

3. Filtering by month/year INTEGER columns (when schema has separate month, year columns):
   - ✓ WHERE month = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month')
        AND year = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 month')
   - ✗ WHERE month = MONTH(CURRENT_DATE - INTERVAL 1 MONTH)  -- Wrong dialect

CRITICAL RULES:
1. ALWAYS filter by user_id='{user_id}' in WHERE clause for all sales tables
2. QUERY THE PRIMARY SALES TABLE FIRST (check schema above for correct table name)
3. Use ONLY SELECT queries - NO INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
4. Use ONLY PostgreSQL syntax for all date/time operations
5. For time queries: Use appropriate date/month/year columns from schema
6. Aggregate for totals, averages, summaries
7. Use LIMIT (max 1000 rows)
8. Handle NULL values with COALESCE

Query Best Practices:
- For general sales questions: Use the primary sales table from schema
- Product names and details: Use columns available in primary table (check schema)
- Meaningful column aliases
- Logical ORDER BY (DESC for top results)
- GROUP BY appropriate dimensions
- Clear monetary formatting (sales_eur, cost_eur, etc.)

Return ONLY the SQL query, nothing else."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        response = self.llm.invoke(messages)
        sql = response.content.strip()

        # Clean SQL: remove markdown code blocks if present
        sql = re.sub(r'```sql\s*|\s*```', '', sql).strip()

        # Remove trailing semicolon (exec_sql function doesn't support it)
        sql = sql.rstrip(';').strip()

        return sql

    async def process_query(
        self,
        query: str,
        user_id: str,
        mcp_execute_sql_fn: Any,
        session_id: Optional[str] = None,
        intent: Optional[QueryIntent] = None
    ) -> Dict[str, Any]:
        """
        Process natural language query using hybrid approach

        Args:
            query: User's natural language question
            user_id: User identifier for filtering
            mcp_execute_sql_fn: Supabase MCP execute_sql function
            session_id: Session ID for conversation continuity
            intent: Optional pre-detected intent

        Returns:
            Dictionary with response, sql, data, session_id
        """
        try:
            # Detect intent if not provided
            if intent is None:
                intent = self.intent_detector.detect_intent(query)

            # Route based on intent type
            if intent.intent_type == "PREDICTION":
                return await self._process_prediction_query(
                    query, user_id, mcp_execute_sql_fn, session_id
                )
            elif intent.intent_type == "ADVANCED_ANALYSIS":
                return await self._process_analysis_query(
                    query, user_id, mcp_execute_sql_fn, session_id
                )

            # Standard SQL query flow for other intents
            # Generate SQL using OpenAI
            sql_query = self._generate_sql(query, user_id)

            # Validate SQL security
            try:
                validated_sql = self.security_validator.validate_and_inject_user_filter(
                    sql_query,
                    user_id
                )
                sql_query = validated_sql
            except ValueError as e:
                return {
                    "response": f"Security validation failed: {str(e)}",
                    "sql": sql_query,
                    "data": None,
                    "session_id": session_id,
                    "error": str(e)
                }

            # Execute SQL via Supabase MCP
            result = await mcp_execute_sql_fn(
                project_id=self.project_id,
                query=sql_query
            )

            # Generate natural language response
            response_text = await self._generate_response(query, sql_query, result)

            return {
                "response": response_text,
                "sql": sql_query,
                "data": result,
                "session_id": session_id or f"session_{user_id}_{datetime.utcnow().timestamp()}"
            }

        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}. Please try rephrasing your question.",
                "sql": None,
                "data": None,
                "session_id": session_id,
                "error": str(e)
            }

    async def _generate_response(self, query: str, sql: str, data: Any) -> str:
        """Generate natural language response from query results"""

        # Format data for LLM
        data_str = json.dumps(data, indent=2) if data else "No results"

        system_prompt = """You are a helpful sales analytics assistant.

Given the user's question, the SQL query that was executed, and the results,
provide a clear, concise natural language answer.

Focus on:
- Directly answering the user's question
- Highlighting key insights from the data
- Using business-friendly language (not technical SQL terms)
- Formatting numbers clearly (e.g., €1,234.56)"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
User Question: {query}

SQL Query: {sql}

Results: {data_str}

Provide a clear answer:""")
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    async def _analyze_with_ai(
        self,
        query: str,
        historical_data: List[Dict[str, Any]],
        analysis_type: str = "general"
    ) -> str:
        """
        Analyze historical data using AI instead of statistical engines

        Args:
            query: User's original question
            historical_data: List of dicts with 'date' and 'sales' keys
            analysis_type: Type of analysis (prediction or analysis)

        Returns:
            Natural language analysis response
        """
        if not historical_data:
            return "I need historical sales data to perform analysis. Please upload some sales data first."

        # Calculate summary statistics for context
        total_records = len(historical_data)
        total_sales = sum(float(record.get('sales', 0)) for record in historical_data)
        avg_sales = total_sales / total_records if total_records > 0 else 0

        # Get date range
        dates = [record.get('date') for record in historical_data]
        date_range_start = min(dates) if dates else "Unknown"
        date_range_end = max(dates) if dates else "Unknown"

        # Format data for AI (limit to recent data for token efficiency)
        recent_data = historical_data[-100:] if len(historical_data) > 100 else historical_data
        data_summary = json.dumps(recent_data, indent=2)

        system_prompt = """You are an expert sales analytics consultant with deep experience in:
- Time series forecasting and predictions
- Trend analysis and pattern recognition
- Seasonality detection
- Anomaly identification
- Business insights and recommendations

Your goal is to analyze the provided historical sales data and answer the user's question with:
1. Clear, actionable insights in business terms
2. Specific numbers, percentages, and timeframes
3. Confidence levels for any predictions (e.g., High / Medium / Low)
4. Explanations that avoid technical or statistical jargon
5. Markdown formatting for readability

### Output Format
Structure your response as:
- **Executive Summary** (3–4 bullets with the main findings)
- **Trends & Patterns**
- **Forecast or Outlook** (if prediction-related)
- **Anomalies & Seasonality**
- **Recommendations**

### For Predictions
- Provide a specific forecasted value (e.g., €X) with a realistic confidence range.
- Explain what drives the forecast (trend, seasonality, recent momentum).
- State key assumptions or risks that might affect accuracy.
- Reference relevant historical context to justify conclusions.

### For Analyses
- Identify recent growth rates (MoM, QoQ, YoY if visible).
- Highlight unusual spikes or drops and plausible reasons.
- Detect recurring patterns (e.g., seasonal peaks, holiday uplifts).
- Offer 2–4 prioritized actions for improvement or follow-up.

### Additional Guidelines
- Quantify wherever possible.
- Use short, clear sentences.
- Avoid filler or speculative explanations.
- End with 1–2 concise recommendations tailored to the data.

If the data is too sparse or inconsistent for confident conclusions, clearly state this and provide cautious observations."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
**User Question:** {query}

**Data Summary:**
- Total Records: {total_records}
- Date Range: {date_range_start} to {date_range_end}
- Total Sales: €{total_sales:,.2f}
- Average Sales per Period: €{avg_sales:,.2f}

**Historical Sales Data (Recent {len(recent_data)} records):**
{data_summary}

Analyze this data and provide a comprehensive answer to the user's question.
Include specific numbers, trends, and actionable insights.""")
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    async def _process_prediction_query(
        self,
        query: str,
        user_id: str,
        mcp_execute_sql_fn: Any,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process prediction query using AI analysis

        Args:
            query: User's prediction question
            user_id: User identifier
            mcp_execute_sql_fn: SQL execution function
            session_id: Session ID

        Returns:
            Dict with prediction response
        """
        try:
            # Fetch historical data
            historical_data = await self._fetch_historical_data(
                user_id,
                mcp_execute_sql_fn,
                months_back=12
            )

            if not historical_data:
                return {
                    "response": "I need historical sales data to make predictions. Please upload some sales data first.",
                    "sql": None,
                    "data": None,
                    "session_id": session_id,
                    "analysis": None
                }

            # Use AI to analyze data and generate prediction
            response_text = await self._analyze_with_ai(
                query,
                historical_data,
                analysis_type="prediction"
            )

            return {
                "response": response_text,
                "sql": None,  # No SQL generated for predictions
                "data": historical_data,
                "session_id": session_id or f"session_{user_id}_{datetime.utcnow().timestamp()}",
                "analysis": {"type": "prediction", "data_points": len(historical_data)}
            }

        except Exception as e:
            return {
                "response": f"Prediction error: {str(e)}. Please try rephrasing your question.",
                "sql": None,
                "data": None,
                "session_id": session_id,
                "analysis": None,
                "error": str(e)
            }

    async def _process_analysis_query(
        self,
        query: str,
        user_id: str,
        mcp_execute_sql_fn: Any,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process advanced analysis query using AI

        Args:
            query: User's analysis question
            user_id: User identifier
            mcp_execute_sql_fn: SQL execution function
            session_id: Session ID

        Returns:
            Dict with analysis response
        """
        try:
            # Fetch historical data
            historical_data = await self._fetch_historical_data(
                user_id,
                mcp_execute_sql_fn,
                months_back=12
            )

            if not historical_data:
                return {
                    "response": "I need historical sales data for analysis. Please upload some sales data first.",
                    "sql": None,
                    "data": None,
                    "session_id": session_id,
                    "analysis": None
                }

            # Use AI to analyze data
            response_text = await self._analyze_with_ai(
                query,
                historical_data,
                analysis_type="analysis"
            )

            return {
                "response": response_text,
                "sql": None,  # No SQL generated for analysis
                "data": historical_data,
                "session_id": session_id or f"session_{user_id}_{datetime.utcnow().timestamp()}",
                "analysis": {"type": "analysis", "data_points": len(historical_data)}
            }

        except Exception as e:
            return {
                "response": f"Analysis error: {str(e)}. Please try rephrasing your question.",
                "sql": None,
                "data": None,
                "session_id": session_id,
                "analysis": None,
                "error": str(e)
            }

    async def _fetch_historical_data(
        self,
        user_id: str,
        mcp_execute_sql_fn: Any,
        months_back: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical sales data for predictions/analysis

        Args:
            user_id: User identifier
            mcp_execute_sql_fn: SQL execution function
            months_back: Number of months to fetch

        Returns:
            List of historical sales data points
        """
        # Try ecommerce_orders first (more granular data)
        sql = f"""
        SELECT
            order_date as date,
            SUM(sales_eur) as sales
        FROM ecommerce_orders
        WHERE user_id = '{user_id}'
            AND order_date >= CURRENT_DATE - INTERVAL '{months_back} months'
        GROUP BY order_date
        ORDER BY order_date
        """

        try:
            result = await mcp_execute_sql_fn(
                project_id=self.project_id,
                query=sql
            )

            if result and len(result) > 0:
                return result
        except:
            pass

        # Fallback to sellout_entries2 (monthly data)
        sql = f"""
        SELECT
            year || '-' || LPAD(month::text, 2, '0') || '-01' as date,
            SUM(sales_eur) as sales
        FROM sellout_entries2
        WHERE user_id = '{user_id}'
        GROUP BY year, month
        ORDER BY year, month
        """

        try:
            result = await mcp_execute_sql_fn(
                project_id=self.project_id,
                query=sql
            )
            return result if result else []
        except:
            return []

    def get_schema_info(self) -> str:
        """Get database schema information"""
        return DATABASE_SCHEMA

    async def test_connection(self, mcp_execute_sql_fn: Any) -> bool:
        """Test database connection via MCP"""
        try:
            result = await mcp_execute_sql_fn(
                project_id=self.project_id,
                query="SELECT 1 as test"
            )
            return True
        except Exception:
            return False


# Backward compatibility aliases
SQLAgent = SQLDatabaseAgent
SQLChatAgent = SQLDatabaseAgent
