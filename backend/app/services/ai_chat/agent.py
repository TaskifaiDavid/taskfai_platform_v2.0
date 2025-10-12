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
from ..analytics.predictor import SalesPredictionEngine, create_prediction_from_supabase_data
from ..analytics.analyzer import SalesAnalysisEngine, analyze_supabase_data


# Database schema for AI context
DATABASE_SCHEMA = """
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
        temperature: float = 0.0
    ):
        """
        Initialize Hybrid SQL Agent

        Args:
            project_id: Supabase project ID
            openai_api_key: OpenAI API key
            model: OpenAI model name
            temperature: LLM temperature
        """
        self.project_id = project_id
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key required")

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

        system_prompt = f"""You are a SQL expert for a sales analytics platform.

{DATABASE_SCHEMA}

CRITICAL RULES:
1. ALWAYS filter by user_id='{user_id}' in WHERE clause for sellout_entries2 and ecommerce_orders
2. QUERY ecommerce_orders FIRST - it's the PRIMARY sales table with most user data
3. ecommerce_orders has functional_name built-in - NO JOIN to products table needed
4. Only query sellout_entries2 if user explicitly asks for "B2B", "offline", or "reseller" data
5. Use ONLY SELECT queries - NO INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
6. For time queries:
   - ecommerce_orders: Use order_date column (PREFERRED)
   - sellout_entries2: Use month/year columns
7. Aggregate for totals, averages, summaries
8. Use LIMIT (max 1000 rows)
9. Handle NULL values with COALESCE

Query Best Practices:
- For general sales questions: Use ecommerce_orders
- For product names: Use functional_name from ecommerce_orders (no join needed)
- Meaningful column aliases
- Logical ORDER BY (DESC for top results)
- GROUP BY appropriate dimensions
- Clear monetary formatting

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

    async def _process_prediction_query(
        self,
        query: str,
        user_id: str,
        mcp_execute_sql_fn: Any,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process prediction query using forecasting engine

        Args:
            query: User's prediction question
            user_id: User identifier
            mcp_execute_sql_fn: SQL execution function
            session_id: Session ID

        Returns:
            Dict with prediction response
        """
        try:
            # Extract target date from query
            target_date = self._extract_target_date(query)

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
                    "prediction": None
                }

            # Create prediction engine and generate forecast
            engine = SalesPredictionEngine(historical_data)
            prediction = engine.predict(target_date, method='auto')

            # Generate natural language response
            response_text = self._format_prediction_response(query, prediction)

            return {
                "response": response_text,
                "sql": None,  # No SQL generated for predictions
                "data": None,
                "session_id": session_id or f"session_{user_id}_{datetime.utcnow().timestamp()}",
                "prediction": prediction
            }

        except ValueError as e:
            return {
                "response": f"I couldn't generate a prediction: {str(e)}. Please ensure you have sufficient historical data (at least 3 months).",
                "sql": None,
                "data": None,
                "session_id": session_id,
                "prediction": None,
                "error": str(e)
            }
        except Exception as e:
            return {
                "response": f"Prediction error: {str(e)}. Please try rephrasing your question.",
                "sql": None,
                "data": None,
                "session_id": session_id,
                "prediction": None,
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
        Process advanced analysis query

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

            # Create analysis engine and run analysis
            engine = SalesAnalysisEngine(historical_data)
            analysis = engine.get_comprehensive_analysis()

            # Generate natural language response
            response_text = self._format_analysis_response(query, analysis)

            return {
                "response": response_text,
                "sql": None,  # No SQL generated for analysis
                "data": None,
                "session_id": session_id or f"session_{user_id}_{datetime.utcnow().timestamp()}",
                "analysis": analysis
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

    def _extract_target_date(self, query: str) -> date:
        """
        Extract target date from prediction query

        Args:
            query: User's query string

        Returns:
            Target date for prediction
        """
        query_lower = query.lower()
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Month name patterns
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        # Check for specific month and year (e.g., "October 2025")
        for month_name, month_num in month_names.items():
            pattern = rf'{month_name}\s+(202\d)'
            match = re.search(pattern, query_lower)
            if match:
                year = int(match.group(1))
                return date(year, month_num, 1)

        # Check for "next month"
        if 'next month' in query_lower:
            if current_month == 12:
                return date(current_year + 1, 1, 1)
            else:
                return date(current_year, current_month + 1, 1)

        # Check for "next quarter"
        if 'next quarter' in query_lower:
            next_quarter_month = ((current_month - 1) // 3 + 1) * 3 + 1
            if next_quarter_month > 12:
                return date(current_year + 1, next_quarter_month - 12, 1)
            else:
                return date(current_year, next_quarter_month, 1)

        # Check for "next year"
        if 'next year' in query_lower:
            return date(current_year + 1, 1, 1)

        # Check for specific year
        year_match = re.search(r'(202\d)', query)
        if year_match:
            year = int(year_match.group(1))
            # Default to January of that year
            return date(year, 1, 1)

        # Default: predict for next month
        if current_month == 12:
            return date(current_year + 1, 1, 1)
        else:
            return date(current_year, current_month + 1, 1)

    def _format_prediction_response(self, query: str, prediction: Dict[str, Any]) -> str:
        """
        Format prediction results into natural language

        Args:
            query: Original query
            prediction: Prediction dictionary

        Returns:
            Natural language response
        """
        pred_sales = prediction['predicted_sales']
        target_date = prediction['target_date']
        lower_bound = prediction['confidence_interval']['lower']
        upper_bound = prediction['confidence_interval']['upper']
        method = prediction['method']
        confidence = prediction['confidence_level'] * 100

        # Format the date nicely
        date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        date_str = date_obj.strftime('%B %Y')

        response = f"Based on your sales trends, I predict **€{pred_sales:,.2f}** in sales for {date_str}.\n\n"
        response += f"**Confidence Interval ({confidence:.0f}%):** €{lower_bound:,.2f} to €{upper_bound:,.2f}\n\n"
        response += f"**Method Used:** {method.upper()} forecasting\n"
        response += f"**Data Points Analyzed:** {prediction['data_points_used']} historical records\n"
        response += f"**Historical Period:** {prediction['historical_period']['start']} to {prediction['historical_period']['end']}\n\n"

        # Add context based on method
        if method == 'seasonal':
            seasonal_factor = prediction.get('seasonal_factor', 1.0)
            if seasonal_factor > 1.1:
                response += f"Note: {date_str} typically shows **{(seasonal_factor-1)*100:.0f}% higher** sales due to seasonal patterns."
            elif seasonal_factor < 0.9:
                response += f"Note: {date_str} typically shows **{(1-seasonal_factor)*100:.0f}% lower** sales due to seasonal patterns."
        elif method == 'linear':
            trend_coef = prediction.get('trend_coefficient', 0)
            if trend_coef > 0:
                response += "Your sales show a **positive growth trend**."
            elif trend_coef < 0:
                response += "Your sales show a **declining trend**. Consider strategies to improve performance."

        return response

    def _format_analysis_response(self, query: str, analysis: Dict[str, Any]) -> str:
        """
        Format analysis results into natural language

        Args:
            query: Original query
            analysis: Analysis dictionary

        Returns:
            Natural language response
        """
        trends = analysis['trends']
        seasonality = analysis['seasonality']
        anomalies = analysis['anomalies']

        response = "## Sales Analysis Summary\n\n"

        # Trend analysis
        response += f"### 📈 Trend Analysis\n"
        response += f"- **Direction:** {trends['trend_direction'].capitalize()}\n"
        response += f"- **Average Growth Rate:** {trends['average_growth_rate']:.2f}% per period\n"

        if trends['latest_growth_rate']:
            response += f"- **Latest Growth:** {trends['latest_growth_rate']:.2f}%\n"

        if trends['acceleration']:
            if trends['acceleration'] > 0:
                response += f"- **Momentum:** Accelerating (+{trends['acceleration']:.2f}%)\n"
            else:
                response += f"- **Momentum:** Decelerating ({trends['acceleration']:.2f}%)\n"

        response += f"- **Peak Period:** {trends['peak_period']['date']} (€{trends['peak_period']['sales']:,.2f})\n"
        response += f"- **Lowest Period:** {trends['lowest_period']['date']} (€{trends['lowest_period']['sales']:,.2f})\n\n"

        # Seasonality
        response += f"### 🌊 Seasonality\n"
        if seasonality['has_seasonality']:
            response += f"- **Seasonal Pattern Detected:** Yes (p-value: {seasonality['p_value']:.4f})\n"
            response += f"- **Strength:** {seasonality['seasonality_strength']:.2f}\n"

            peak_months_names = [seasonality['month_names'][m] for m in seasonality['peak_months']]
            low_months_names = [seasonality['month_names'][m] for m in seasonality['low_months']]

            response += f"- **Peak Months:** {', '.join(peak_months_names)}\n"
            response += f"- **Low Months:** {', '.join(low_months_names)}\n"
            response += f"- **Peak Multiplier:** {seasonality['peak_month_multiplier']:.2f}x average\n\n"
        else:
            response += "- **Seasonal Pattern:** Not detected or insufficient data\n\n"

        # Anomalies
        if anomalies and len(anomalies) > 0:
            response += f"### ⚠️ Anomalies Detected\n"
            response += f"Found {len(anomalies)} unusual data point(s):\n\n"
            for anomaly in anomalies[:3]:  # Show top 3
                emoji = "📈" if anomaly['type'] == 'spike' else "📉"
                response += f"{emoji} **{anomaly['date']}** - {anomaly['type'].capitalize()} "
                response += f"(€{anomaly['sales']:,.2f}, {anomaly['percent_deviation']:+.1f}% from average)\n"
        else:
            response += f"### ✅ No Anomalies\n"
            response += "All data points are within expected ranges.\n"

        return response

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
