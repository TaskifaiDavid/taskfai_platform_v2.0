"""
LangGraph SQL Agent for natural language to SQL conversion
"""

from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from .intent import IntentDetector
from .security import QuerySecurityValidator


class ChatState(TypedDict):
    """State for chat conversation"""
    messages: Annotated[List, add_messages]
    user_id: str
    session_id: Optional[str]
    query_intent: Optional[str]
    sql_query: Optional[str]
    sql_result: Optional[Dict[str, Any]]
    error: Optional[str]


class SQLChatAgent:
    """
    LangGraph-based SQL chat agent with conversation memory

    Workflow:
    1. Detect intent from user query
    2. Generate secure SQL query
    3. Validate SQL for security
    4. Execute query (caller responsibility)
    5. Format results into natural language response
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.0
    ):
        """
        Initialize SQL chat agent

        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
            temperature: Temperature for generation
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=model,
            temperature=temperature
        )

        self.intent_detector = IntentDetector()
        self.security_validator = QuerySecurityValidator()
        self.memory = MemorySaver()

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(ChatState)

        # Add nodes
        workflow.add_node("detect_intent", self._detect_intent_node)
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("validate_sql", self._validate_sql_node)
        workflow.add_node("format_response", self._format_response_node)

        # Define edges
        workflow.set_entry_point("detect_intent")
        workflow.add_edge("detect_intent", "generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")

        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate_sql",
            self._should_format_response,
            {
                "format": "format_response",
                "error": END
            }
        )

        workflow.add_edge("format_response", END)

        return workflow.compile(checkpointer=self.memory)

    def _detect_intent_node(self, state: ChatState) -> Dict[str, Any]:
        """Detect user query intent"""
        last_message = state["messages"][-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        intent = self.intent_detector.detect_intent(user_query)

        return {
            "query_intent": intent.intent_type
        }

    def _generate_sql_node(self, state: ChatState) -> Dict[str, Any]:
        """Generate SQL query from natural language"""
        last_message = state["messages"][-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)
        user_id = state["user_id"]
        query_intent = state.get("query_intent", "GENERAL")

        # SQL generation prompt with schema context
        system_prompt = self._get_system_prompt(query_intent)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{query}")
        ])

        # Get conversation history (last 5 messages)
        chat_history = state["messages"][-6:-1] if len(state["messages"]) > 1 else []

        # Generate SQL
        chain = prompt | self.llm
        response = chain.invoke({
            "query": user_query,
            "chat_history": chat_history,
            "user_id": user_id
        })

        sql_query = self._extract_sql_from_response(response.content)

        return {
            "sql_query": sql_query
        }

    def _validate_sql_node(self, state: ChatState) -> Dict[str, Any]:
        """Validate SQL for security"""
        sql_query = state.get("sql_query")
        user_id = state["user_id"]

        if not sql_query:
            return {"error": "No SQL query generated"}

        # Validate with security validator
        try:
            validated_sql = self.security_validator.validate_and_inject_user_filter(
                sql_query,
                user_id
            )
            return {"sql_query": validated_sql, "error": None}
        except ValueError as e:
            return {"error": str(e)}

    def _format_response_node(self, state: ChatState) -> Dict[str, Any]:
        """Format SQL results into natural language response"""
        sql_result = state.get("sql_result")
        last_message = state["messages"][-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        if not sql_result:
            response_text = "I couldn't find any data matching your query."
        else:
            # Format results into natural language
            response_text = self._format_results_to_text(user_query, sql_result)

        # Add AI response to messages
        return {
            "messages": [AIMessage(content=response_text)]
        }

    def _should_format_response(self, state: ChatState) -> str:
        """Determine if we should format response or end with error"""
        if state.get("error"):
            return "error"
        return "format"

    def _get_system_prompt(self, query_intent: str) -> str:
        """Get system prompt based on query intent"""
        base_prompt = """You are a SQL query generator for a sales analytics platform.

Database Schema:
- sellout_entries2: Offline/B2B sales (product_ean, functional_name, reseller, sales_eur, quantity, month, year, user_id)
- ecommerce_orders: Online/D2C sales (product_ean, functional_name, sales_eur, quantity, order_date, country, utm_source, user_id)
- products: Product catalog (product_id, sku, product_name, product_ean, functional_name, category)
- resellers: Reseller information (reseller_id, name, country)

Important Rules:
1. ALWAYS filter by user_id (it will be automatically injected)
2. Use only SELECT queries - NO INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
3. Use parameterized queries with $1, $2, etc. for user inputs
4. For date ranges, extract month/year from order_date for ecommerce_orders
5. Join tables when needed for complete information
6. Return clear, aggregated results

Query Intent: {intent}

Generate ONLY the SQL query, wrapped in ```sql``` code blocks."""

        return base_prompt.format(intent=query_intent)

    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Look for SQL code block
        if "```sql" in response:
            start = response.find("```sql") + 6
            end = response.find("```", start)
            sql = response[start:end].strip()
            return sql
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            sql = response[start:end].strip()
            return sql
        else:
            # Assume entire response is SQL
            return response.strip()

    def _format_results_to_text(self, query: str, results: Dict[str, Any]) -> str:
        """Format SQL results into natural language"""
        if not results or not results.get("rows"):
            return "No results found for your query."

        rows = results["rows"]
        columns = results.get("columns", [])

        # Use LLM to format results
        format_prompt = f"""Given this user query: "{query}"

And these SQL results:
Columns: {columns}
Rows: {rows[:10]}  # Limit to first 10 for context

Generate a clear, concise natural language response summarizing the results.
Include key metrics and insights. If there are many rows, provide a summary."""

        response = self.llm.invoke([HumanMessage(content=format_prompt)])
        return response.content

    def chat(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        sql_executor: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Process chat query

        Args:
            query: User's natural language query
            user_id: User identifier
            session_id: Session identifier for conversation memory
            sql_executor: Function to execute SQL (signature: sql, user_id -> results)

        Returns:
            Dict with response, sql_query, intent, error
        """
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "user_id": user_id,
            "session_id": session_id,
            "query_intent": None,
            "sql_query": None,
            "sql_result": None,
            "error": None
        }

        # Configure for conversation memory
        config = {"configurable": {"thread_id": session_id or f"user_{user_id}"}}

        # Run graph up to SQL validation
        result = self.graph.invoke(initial_state, config)

        # If validation passed and we have SQL, execute it
        if not result.get("error") and result.get("sql_query") and sql_executor:
            try:
                sql_results = sql_executor(result["sql_query"], user_id)
                result["sql_result"] = sql_results

                # Continue graph to format response
                result = self.graph.invoke(result, config)
            except Exception as e:
                result["error"] = f"Query execution error: {str(e)}"

        # Extract final response
        final_messages = result.get("messages", [])
        final_response = final_messages[-1].content if final_messages else "I encountered an error processing your query."

        return {
            "response": final_response,
            "sql_query": result.get("sql_query"),
            "query_intent": result.get("query_intent"),
            "error": result.get("error")
        }

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages
        """
        config = {"configurable": {"thread_id": session_id}}

        try:
            # Get state from memory
            state = self.graph.get_state(config)
            messages = state.values.get("messages", [])

            # Convert to dict format
            history = []
            for msg in messages[-limit:]:
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                history.append({
                    "role": role,
                    "content": msg.content,
                    "timestamp": datetime.utcnow().isoformat()
                })

            return history
        except Exception:
            return []


# Alias for backwards compatibility
SQLAgent = SQLChatAgent
