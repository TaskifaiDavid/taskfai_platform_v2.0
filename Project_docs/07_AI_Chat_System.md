# 7. AI-Powered Chat System

This document describes the AI chat system that enables users to query their sales data using natural language.

## 7.1. Core Purpose

The AI chat system provides an intelligent, conversational interface for exploring sales data. Users can ask questions in plain English (or any natural language) and receive data-driven insights without writing SQL queries or navigating complex filters.

**Key Business Value:**
- Democratizes data access for non-technical users
- Reduces time from question to insight
- Enables exploratory data analysis through conversation
- Maintains conversation context for follow-up questions

## 7.2. System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Chat UI                         │
│  (Message input, conversation history, typing indicators)    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/JSON
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend API Gateway                         │
│            (Authentication, rate limiting)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  AI Chat Agent Engine                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Intent Detection (ONLINE/OFFLINE/COMPARISON)      │  │
│  │  2. Conversation Memory (Context from history)        │  │
│  │  3. Data Retrieval (Multi-channel query routing)      │  │
│  │  4. LLM Analysis (GPT-4 response generation)          │  │
│  │  5. Response Formatting (User-friendly output)        │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ↓                       ↓
┌──────────────────┐    ┌──────────────────┐
│ Sales Database   │    │ Conversation DB  │
│ (sellout_entries,│    │ (chat history)   │
│  ecommerce)      │    │                  │
└──────────────────┘    └──────────────────┘
```

### Core Processing Flow

1. **User Input** → Frontend captures message and session context
2. **Authentication** → Backend verifies user identity
3. **Intent Analysis** → System determines query type (comparison, online sales, time analysis, etc.)
4. **Context Loading** → Retrieves recent conversation history for continuity
5. **Data Routing** → Queries appropriate tables based on intent
6. **Data Filtering** → Applies user-specific data isolation and time filters
7. **Data Summarization** → Aggregates and analyzes data for LLM consumption
8. **LLM Generation** → GPT-4 generates natural language response
9. **Memory Persistence** → Saves conversation turn to database
10. **Response Delivery** → Returns formatted answer to user

## 7.3. Intent Detection System

The system automatically classifies user queries into specific intent types to route data efficiently:

### Intent Categories

| Intent Type | Description | Example Questions | Data Source |
|------------|-------------|------------------|-------------|
| `ONLINE_SALES` | E-commerce specific queries | "Show online sales in Germany", "Which device type converts best?" | `ecommerce_orders` |
| `OFFLINE_SALES` | B2B/wholesale queries | "Top reseller by volume", "Wholesale performance 2025" | `sellout_entries2` |
| `COMBINED_SALES` | Total business queries | "What are total sales?", "All revenue across channels" | Both tables |
| `SALES_COMPARISON` | Online vs offline analysis | "Compare online vs offline sales", "Which channel is growing?" | Both tables |
| `TIME_ANALYSIS` | Temporal trends | "Sales by month in 2024", "Year over year growth" | Time-filtered data |
| `RESELLER_ANALYSIS` | Partner performance | "Which reseller sold the most?", "Top 5 customers" | Reseller grouping |
| `PRODUCT_ANALYSIS` | Product performance | "Best selling product", "Revenue by product category" | Product grouping |
| `COMPARISON` | General comparisons | "May vs June sales", "Product A vs Product B" | Context-dependent |
| `TOTAL_SUMMARY` | Aggregate metrics | "Total revenue this year", "How many units sold?" | Aggregated data |

### Intent Detection Logic

The system uses keyword analysis and pattern matching:

```
Input: "What were online sales in May 2024?"

Analysis:
- Keywords: "online" → ONLINE_SALES intent
- Time extraction: "May 2024" → month=5, year=2024
- Result: Query ecommerce_orders filtered by month=5 AND year=2024
```

## 7.4. Conversation Memory

### Memory Architecture

The chat system maintains conversation context using modern LangChain memory patterns:

**Modern Memory Approach (LangGraph MemorySaver):**
- Uses `MemorySaver` from `langgraph.checkpoint.memory` for state persistence
- Thread-based conversation management with unique thread IDs
- Automatic message trimming for context window management
- Checkpoint-based state restoration across sessions

**Short-Term Memory (In-Session):**
- Last 10 messages (5 user + 5 AI exchanges) via message trimming
- Managed through `trim_messages` utility for token optimization
- Used for immediate context understanding

**Long-Term Memory (Persistent):**
- All conversations stored in database with checkpointing
- User-specific conversation history via thread IDs
- Session grouping for multiple chat threads
- Enables conversation resumption across sessions with full state restoration

### Memory Data Model

```
ConversationHistory:
- user_id: Identifies the user
- session_id: Groups related conversations (optional)
- user_message: The question asked
- ai_response: The answer generated
- timestamp: When the exchange occurred
```

### Context Usage Example

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
import uuid

# Initialize memory and agent
memory = MemorySaver()
agent = create_react_agent(model, tools=[], checkpointer=memory)

# First interaction with unique thread ID
thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": str(thread_id)}}

agent.invoke(
    {"messages": [HumanMessage("What were sales in May 2024?")]},
    config=config
)
# AI: "In May 2024, total sales were €45,320 across all channels..."

# Follow-up with same thread ID - memory automatically loaded
agent.invoke(
    {"messages": [HumanMessage("How does that compare to June?")]},
    config=config
)
# AI: [Loads previous context, understands "that" = May 2024 sales]
#     "June 2024 had €52,180 in sales, which is €6,860 higher than May..."
```

## 7.5. Multi-Channel Data Integration

### Data Sources

The system integrates two distinct sales channels:

**1. Offline/Wholesale Sales (`sellout_entries2`)**
- B2B transactions through reseller partners
- Fields: functional_name, reseller, sales_eur, quantity, month, year, product_ean
- Aggregated by reseller and product
- Monthly granularity

**2. Online Sales (`ecommerce_orders`)**
- Direct-to-consumer e-commerce transactions
- Fields: order_id, product_name, sales_eur, quantity, order_date, country, city, utm_source, device_type
- Individual order-level data
- Daily granularity with marketing attribution

### Channel-Specific Analysis

**For Online Sales Queries:**
- Geographic analysis (country, city distribution)
- Marketing performance (UTM sources, campaigns)
- Device behavior (mobile, desktop, tablet)
- Customer acquisition insights

**For Offline Sales Queries:**
- Reseller/partner performance
- B2B volume trends
- Wholesale pricing patterns
- Channel partner effectiveness

**For Combined Analysis:**
- Total business performance
- Channel mix and contribution
- Cross-channel product performance
- Holistic revenue view

### Data Normalization

When combining online and offline data, the system normalizes structures:

```
Online Record:
{
  order_date: "2024-05-15",
  product_name: "Product A",
  sales_eur: 49.99,
  quantity: 1,
  country: "DE",
  utm_source: "google"
}

Normalized to:
{
  year: 2024,
  month: 5,
  functional_name: "Product A",
  sales_eur: 49.99,
  quantity: 1,
  channel: "online",
  reseller: "Online",
  country: "DE",
  utm_source: "google"
}
```

## 7.6. Security and Data Isolation

### Query Validation

All SQL queries are validated before execution:

**Blocked Operations:**
- `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`
- SQL injection patterns (`;`, `--`, `/*`, `*/`)
- UNION attacks
- File operations (`INTO OUTFILE`)

**Allowed Operations:**
- `SELECT` statements only
- Limited to approved tables
- Read-only access

### User Data Isolation

Each user only accesses their own data:

```
Query Pattern:
SELECT * FROM sellout_entries2
WHERE user_id = [authenticated_user_id]
AND [additional_filters]
```

User authentication via JWT ensures data privacy.

## 7.7. LLM Integration

### Language Model Configuration

**Provider:** OpenAI GPT-4
**Purpose:** Natural language understanding and response generation

**Modern LangChain Setup:**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langgraph.checkpoint.memory import MemorySaver

# Initialize LLM
model = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0,  # Deterministic for SQL queries
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create prompt with message history placeholder
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sales analyst expert..."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Initialize memory
memory = MemorySaver()
```

**Model Capabilities:**
- Understands complex business questions
- Performs calculations on provided data
- Generates formatted, human-readable responses
- Maintains professional tone with conversation history
- Provides actionable insights with context awareness

### Prompt Engineering

The system uses intent-specific prompts:

**For Comparison Queries:**
```
You are an expert sales analyst. Based on the following data:
[COMPLETE SALES DATA SUMMARY]

Question: [USER QUESTION]

Instructions:
1. Calculate exact differences and percentage changes
2. Provide clear before/after comparison
3. Include business insights about the comparison
4. Use complete dataset totals, not individual reseller data
```

**For Online Sales:**
```
You are an ecommerce analyst. Focus on:
- Geographic performance (countries, cities)
- Digital marketing effectiveness
- Customer behavior patterns
- Device type analysis
```

### Response Quality Controls

- Responses are factual and data-driven
- No hallucination of numbers not in data
- Clear indication when data is insufficient
- Professional formatting with currency symbols
- Contextual insights beyond raw numbers

## 7.8. API Endpoints

### POST /api/chat

Send a message to the AI chat system.

**Request:**
```json
{
  "message": "What were total sales in May 2024?",
  "session_id": "optional-session-identifier"
}
```

**Response:**
```json
{
  "answer": "In May 2024, your total sales across all channels were €45,320.50...",
  "session_id": "optional-session-identifier"
}
```

### GET /api/chat/history

Retrieve conversation history for the authenticated user.

**Response:**
```json
{
  "conversations": [
    {
      "session_id": "default",
      "user_message": "What were sales in May?",
      "ai_response": "In May 2024, total sales were...",
      "timestamp": "2024-05-20T14:30:00Z"
    }
  ],
  "total_messages": 10
}
```

### POST /api/chat/clear

Clear conversation history for memory reset.

**Request:**
```json
{
  "session_id": "optional-session-to-clear"
}
```

**Response:**
```json
{
  "message": "Conversation cleared successfully",
  "session_id": "default"
}
```

### GET /api/chat/health

Health check for chat system availability.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## 7.9. Example Interactions

### Simple Total Query

```
User: "What are my total sales this year?"

System Process:
1. Intent: TOTAL_SUMMARY
2. Time Filter: year=2025
3. Data: Query both sellout_entries2 and ecommerce_orders
4. Aggregate: Sum all sales_eur values

Response: "Your total sales for 2025 are €234,567.89 across all channels,
representing 15,432 units sold through 12 resellers and your online store."
```

### Time Comparison Query

```
User: "Compare sales between May and June 2024"

System Process:
1. Intent: COMPARISON
2. Time Extraction: May 2024, June 2024
3. Data: Query both months separately
4. Calculate: Differences and percentages

Response: "Comparing May vs June 2024:
- May 2024: €45,320.50 (3,210 units)
- June 2024: €52,180.75 (3,680 units)
- Change: +€6,860.25 (+15.1% growth)
This represents a strong upward trend heading into summer months."
```

### Channel-Specific Query

```
User: "Which country had the most online sales?"

System Process:
1. Intent: ONLINE_SALES
2. Data: Query ecommerce_orders only
3. Group By: country
4. Order: By total sales DESC

Response: "Germany leads your online sales with €78,432.10 (42% of total online revenue),
followed by France (€45,231.20, 24%) and Netherlands (€32,109.50, 17%).
Consider expanding marketing efforts in these high-performing markets."
```

### Follow-Up with Memory

```
User: "Show me sales by product"
AI: "Top products by revenue:
1. Product A: €45,230
2. Product B: €38,920
3. Product C: €29,340"

User: "Which resellers sold the most of the first one?"
AI: [Uses memory to understand "first one" = Product A]
    "For Product A, top resellers are:
    1. Galilu: €12,340
    2. Boxnox: €8,920
    3. Skins SA: €7,100"
```

## 7.10. Performance Considerations

**Query Optimization:**
- Limit results to 5,000 recent records per query
- Use indexed fields (year, month, user_id) for filtering
- Aggregate data before sending to LLM to reduce token usage

**Caching Strategy:**
- Cache conversation memory in-memory for active sessions
- Only load full history from database on session start
- Clear stale sessions after 30 minutes of inactivity

**Rate Limiting:**
- Prevent abuse of expensive LLM calls
- Limit to reasonable queries per user per minute
- Monitor token usage for cost control

## 7.11. Error Handling

**Insufficient Data:**
```
Response: "I don't have enough sales data to answer that question.
Please ensure you've uploaded data for the requested time period."
```

**Ambiguous Query:**
```
Response: "I need more context. Are you asking about online sales,
offline sales, or combined sales across all channels?"
```

**System Error:**
```
Response: "I encountered an error processing your request.
Please try rephrasing your question or contact support if this persists."
```

## 7.12. Future Enhancements

Potential improvements for future versions:

1. **Visualization Generation:** Auto-generate charts based on query intent
2. **Predictive Analytics:** "What will sales be next month?" forecasting
3. **Anomaly Detection:** "Alert me to unusual sales patterns"
4. **Natural Language Reports:** "Generate a monthly report" → Full PDF
5. **Voice Input:** Speech-to-text for mobile users
6. **Multi-Language Support:** Queries in German, French, etc.
7. **Custom Metrics:** User-defined KPIs and calculations
8. **Export Conversations:** Save chat insights as documents
