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


# Universal database schema for AI context - Works across all tenants
DATABASE_SCHEMA_UNIVERSAL = """
Your database contains sales/order transaction data. The exact table names and columns
may vary by tenant, but follow these common patterns:

PRIMARY SALES TABLE (Query this first - table name varies by tenant):
- B2C tenants: ecommerce_orders, orders
- B2B tenants: sales_unified, sales

Common transaction columns (most will exist):
- Transaction ID: order_id, sale_id, transaction_id, id
- Product identifier: product_ean (EAN-13 barcode), product_id, sku
- Product name: functional_name (human-readable, ALWAYS use for display)
- Revenue: sales_eur (always in EUR for reporting)
- Quantity: quantity, units_sold (INTEGER, can be negative for returns)
- Date: order_date, sale_date, transaction_date (DATE type)
- Geography: country, city, region (TEXT, denormalized in fact table)
- Time dimensions: year, month, quarter (INTEGER, extracted from date)

Security filtering columns:
- user_id: Filter by this in WHERE clause (B2C/multi-user tenants)
- tenant_id: Filter by subdomain value (multi-tenant systems)
- Some tenants have single-tenant databases with NO filtering required

Optional B2B-specific columns (check if present before using):
- reseller_id: UUID pointing to resellers lookup table
- store_id: UUID pointing to stores lookup table
- sales_channel: TEXT ('online', 'retail', 'B2B', 'B2C')
- customer_id: UUID for end customer in B2B sales
- store_identifier: TEXT (original store code from upload file)

Optional financial columns (may not exist):
- cost_eur, cost_of_goods: Product cost for margin calculations
- stripe_fee, payment_fees: Transaction processing fees
- sales_local_currency, local_currency: Original currency amounts

Optional marketing columns (may not exist):
- utm_source, utm_medium, utm_campaign: Marketing attribution
- device_type: Desktop, mobile, tablet

LOOKUP TABLES (only query if needed for human-readable names):

1. resellers (B2B tenants only - join when query mentions reseller names):
   Columns: reseller_id (UUID), name (TEXT), country (TEXT)
   JOIN pattern: JOIN resellers r ON main_table.reseller_id = r.reseller_id
   Use when: Query asks "what are Liberty's sales" or "which reseller performs best"
   Shows: Human-readable reseller names instead of UUIDs

2. stores (B2B tenants only - join when query mentions store names):
   Columns: store_id (UUID), reseller_id (UUID), store_name (TEXT),
            store_type (TEXT), country (TEXT), city (TEXT)
   JOIN pattern: JOIN stores s ON main_table.store_id = s.store_id
   Use when: Query asks "flagship store performance" or "which store sold most"
   Shows: Human-readable store names instead of UUIDs

3. product_reseller_mappings (rare - only for vendor code lookups):
   Columns: reseller_product_code, product_ean, product_name
   Use when: Need to map vendor-specific product codes to EANs

CRITICAL QUERY STRATEGY:
1. Start with PRIMARY sales table (ecommerce_orders OR sales_unified)
2. Use denormalized columns when available (functional_name, country, city)
   - Product names: Use functional_name directly - NO JOIN needed
   - Geography: Use country, city directly - NO JOIN needed
3. Only JOIN lookup tables when:
   - Query specifically mentions reseller/store names OR
   - Need to display human-readable names instead of UUIDs
4. Handle missing columns gracefully - if column doesn't exist, adapt without it
5. Security filtering: Apply user_id/tenant_id filter ONLY if specified in tenant config
   - Single-tenant databases do not require filtering
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

        # Use universal schema for all tenants
        self.database_schema = DATABASE_SCHEMA_UNIVERSAL

        # Set tenant-specific table and filter configuration
        if self.tenant_subdomain == "bibbi":
            self.primary_table = "sales_unified"
            self.filter_column = None  # BIBBI has single-tenant database, no filtering needed
            self.filter_value = None
            self.available_columns = """id, product_ean, functional_name, reseller_id, store_id, customer_id,
                                         sale_date, year, month, quarter, week_of_year, quantity,
                                         sales_local_currency, currency, sales_eur, exchange_rate,
                                         cost_of_goods, commission_amount, vat_rate, vat_amount,
                                         shipping_cost, payment_processing_fee, gross_revenue, net_revenue,
                                         gross_margin, order_id, sales_channel, is_gift, is_refund, refund_reason,
                                         country, region, city, customer_ip, device_type,
                                         utm_source, utm_medium, utm_campaign, utm_content, utm_term,
                                         session_pages, session_count, referrer_url, upload_id,
                                         created_at, updated_at"""
        else:  # demo or other B2C tenants
            self.primary_table = "ecommerce_orders"
            self.filter_column = "user_id"
            self.filter_value = "{user_id}"  # Will be replaced in _generate_sql
            self.available_columns = """order_id, user_id, product_ean, functional_name, product_name,
                                         sales_eur, quantity, cost_of_goods, stripe_fee, order_date,
                                         country, city, year, month, utm_source, utm_medium,
                                         utm_campaign, device_type, reseller, created_at"""

        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=model,
            temperature=temperature
        )

        # Initialize supporting services
        self.intent_detector = IntentDetector()
        self.security_validator = QuerySecurityValidator()

    def _generate_sql(self, query: str, user_id: str, conversation_context: str = "") -> str:
        """Generate SQL from natural language using OpenAI

        Args:
            query: User's natural language question
            user_id: User ID for filtering (if applicable)
            conversation_context: Recent conversation history for understanding follow-up questions
        """

        # Build filter clause for prompt
        if self.filter_column and self.filter_value:
            # Replace user_id placeholder if needed
            filter_value = self.filter_value.replace("{user_id}", user_id)
            filter_clause = f"WHERE {self.filter_column} = '{filter_value}'"
            filter_info = f"Filter: {self.filter_column} = '{filter_value}'"
            where_example = f"WHERE {self.filter_column} = '{filter_value}'\n  AND "
        else:
            # BIBBI case: no tenant filtering needed (single-tenant database)
            filter_clause = ""
            filter_info = "Filter: None (single-tenant database)"
            where_example = "WHERE "

        # Add conversation context if available
        context_section = ""
        if conversation_context:
            context_section = f"""
RECENT CONVERSATION CONTEXT:
{conversation_context}

Use this context to understand follow-up questions. For example:
- If user previously asked about "BBGOT100" and now asks "what about revenue?",
  they're asking about BBGOT100's revenue.
- If user asked "top products" and says "show me the second one",
  refer to the second product from previous results.
- If user says "compare it to...", "it" refers to the subject of previous query.

"""

        # Use tenant-specific database schema
        system_prompt = f"""You are a SQL expert for a sales analytics platform.
{context_section}
CURRENT TENANT CONFIGURATION:
Tenant: {self.tenant_subdomain}
Primary Table: {self.primary_table}
{filter_info}
Available Columns: {self.available_columns}

CONCRETE SQL EXAMPLES FOR YOUR TENANT ({self.tenant_subdomain}):

Example 1 - Top 5 products last month:
SELECT
    functional_name AS product_name,
    SUM(sales_eur) AS total_revenue,
    SUM(quantity) AS total_units_sold
FROM {self.primary_table}
{where_example}month = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month')
  AND year = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 month')
GROUP BY functional_name
ORDER BY total_revenue DESC
LIMIT 5

Example 2 - Total sales this year:
SELECT
    SUM(sales_eur) AS total_revenue,
    COUNT(*) AS transaction_count
FROM {self.primary_table}
{where_example}year = EXTRACT(YEAR FROM CURRENT_DATE)

Example 3 - Sales by country:
SELECT
    country,
    SUM(sales_eur) AS revenue,
    SUM(quantity) AS units_sold
FROM {self.primary_table}
{filter_clause if filter_clause else ""}
GROUP BY country
ORDER BY revenue DESC

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

CRITICAL RULES - FOLLOW EXACTLY:

1. ALWAYS USE THIS TABLE: {self.primary_table}
   - This is the ONLY table you should query for sales data
   - Do NOT use any other table name

2. DATA FILTERING:
   {f"- MUST INCLUDE: WHERE {self.filter_column} = '{filter_value}' in EVERY query" if self.filter_column else "- NO filtering required (single-tenant database)"}
   {f"- This is mandatory for security and data isolation" if self.filter_column else "- All data in this database belongs to the current tenant"}

3. FOLLOW THE EXAMPLES ABOVE
   - The 3 examples show the correct table name and filtering pattern
   - Pattern-match your queries to those examples
   - Use the same FROM clause: FROM {self.primary_table}
   {f"- Use the same WHERE clause: WHERE {self.filter_column} = '{filter_value}'" if self.filter_column else ""}

4. AVAILABLE COLUMNS (only use these):
   {self.available_columns}

5. Use ONLY SELECT queries - NO INSERT, UPDATE, DELETE, DROP, ALTER, CREATE

6. Use ONLY PostgreSQL syntax for date/time operations (EXTRACT, INTERVAL)

7. PRODUCT NAMES - Use functional_name column (present in your table)

8. GEOGRAPHY - Use country, city columns directly (present in your table)

9. PRODUCT IDENTIFICATION STRATEGY - CRITICAL:

   A) Determine Product Type from User Input:
      - 13-digit number (e.g., "7350154320022") → This is product_ean (EAN barcode)
      - Product code/SKU (e.g., "BBGOT100", "GOT100", "BBSP30") → This is functional_name

   B) Query Strategy by Type:
      - For EAN Barcodes (13 digits): WHERE product_ean = '7350154320022'
      - For Product Names/SKUs: WHERE functional_name ILIKE '%PRODUCTCODE%'
        * Use ILIKE for case-insensitive matching
        * Use % wildcards for partial matching
        * Example: "GOT100" → WHERE functional_name ILIKE '%GOT100%' (matches BBGOT100, BBGOT30, etc.)

   C) Examples:
      User asks: "How much did BBGOT100 sell for?"
      SELECT functional_name, SUM(sales_eur) AS revenue, SUM(quantity) AS units
      FROM {self.primary_table}
      WHERE functional_name ILIKE '%BBGOT100%'
      GROUP BY functional_name

      User asks: "Show me GOT100 sales"
      SELECT functional_name, SUM(sales_eur) AS revenue
      FROM {self.primary_table}
      WHERE functional_name ILIKE '%GOT100%'
      GROUP BY functional_name

      User asks: "Sales for EAN 7350154320022"
      SELECT product_ean, functional_name, SUM(sales_eur)
      FROM {self.primary_table}
      WHERE product_ean = '7350154320022'
      GROUP BY product_ean, functional_name

10. RESELLER QUERY STRATEGY - Use JOINs when user mentions reseller names:

   When user asks about specific reseller (Liberty, Galilu, Boxnox, etc.),
   you MUST JOIN the resellers table to filter by reseller name.

   A) Reseller Total Sales:
      User asks: "How much did Liberty sell for?"
      SELECT r.name AS reseller_name, SUM(s.sales_eur) AS total_revenue, SUM(s.quantity) AS units
      FROM {self.primary_table} s
      JOIN resellers r ON s.reseller_id = r.reseller_id
      WHERE r.name ILIKE '%Liberty%'
      GROUP BY r.name

   B) Reseller Sales by Product:
      User asks: "What did Liberty sell of BBGOT100?"
      SELECT r.name AS reseller, s.functional_name AS product, SUM(s.sales_eur) AS revenue
      FROM {self.primary_table} s
      JOIN resellers r ON s.reseller_id = r.reseller_id
      WHERE r.name ILIKE '%Liberty%' AND s.functional_name ILIKE '%BBGOT100%'
      GROUP BY r.name, s.functional_name

   C) Compare Resellers:
      User asks: "Compare Liberty and Galilu sales"
      SELECT r.name AS reseller, SUM(s.sales_eur) AS revenue
      FROM {self.primary_table} s
      JOIN resellers r ON s.reseller_id = r.reseller_id
      WHERE r.name ILIKE '%Liberty%' OR r.name ILIKE '%Galilu%'
      GROUP BY r.name
      ORDER BY revenue DESC

   CRITICAL: The resellers table has column "name", not "reseller_name"

11. STORE QUERIES (if needed):
    JOIN stores: JOIN stores s ON {self.primary_table}.store_id = s.store_id
    Use when query asks for store names or locations

12. Aggregate with SUM, COUNT, AVG for totals and summaries

13. Use LIMIT (max 1000 rows) to control result size

14. Handle NULL values with COALESCE when needed

Query Best Practices:
- Start with primary sales table (ecommerce_orders OR sales_unified)
- Use denormalized columns first (functional_name, country, city)
- For product names/SKUs: ALWAYS use ILIKE with wildcards for matching
- For reseller names: ALWAYS JOIN resellers table and use ILIKE
- Only JOIN lookup tables when displaying human-readable names
- Meaningful column aliases for clarity
- Logical ORDER BY (DESC for "top" results, ASC for "lowest")
- GROUP BY appropriate dimensions (product, country, month, etc.)
- Format monetary values clearly (sales_eur, cost_of_goods, etc.)

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
        intent: Optional[QueryIntent] = None,
        conversation_memory: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Process natural language query using hybrid approach

        Args:
            query: User's natural language question
            user_id: User identifier for filtering
            mcp_execute_sql_fn: Supabase MCP execute_sql function
            session_id: Session ID for conversation continuity
            intent: Optional pre-detected intent
            conversation_memory: Optional ConversationMemory instance for context

        Returns:
            Dictionary with response, sql, data, session_id
        """
        try:
            # Get recent conversation context if available
            conversation_context = ""
            if conversation_memory and session_id:
                try:
                    conversation_context = await conversation_memory.get_recent_context(
                        user_id=user_id,
                        session_id=session_id,
                        limit=3  # Last 3 exchanges for context
                    )
                except Exception as e:
                    # Log warning but continue without context
                    pass

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
            # Generate SQL using OpenAI with conversation context
            sql_query = self._generate_sql(query, user_id, conversation_context)

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
