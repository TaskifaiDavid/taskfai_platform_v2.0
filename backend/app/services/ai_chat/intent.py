"""
Query intent detection for routing and optimization
"""

from typing import Dict, Optional, List, Any
from pydantic import BaseModel
import re


class QueryIntent(BaseModel):
    """Detected query intent"""
    intent_type: str
    confidence: float
    entities: Dict[str, Any] = {}
    suggested_filters: Optional[Dict] = None


class IntentDetector:
    """
    Detect user query intent for better SQL generation

    Intent Types:
    - ONLINE_SALES: Queries about online/ecommerce data
    - OFFLINE_SALES: Queries about offline/B2B sales
    - COMPARISON: Comparing online vs offline or time periods
    - TIME_ANALYSIS: Trend analysis over time
    - PRODUCT_ANALYSIS: Product-specific queries
    - RESELLER_ANALYSIS: Reseller/partner analysis
    - PREDICTION: Sales forecasting and predictions
    - ADVANCED_ANALYSIS: Trend, seasonality, anomaly detection
    - GENERAL: General queries or unclear intent
    """

    # Intent patterns (keywords -> intent type)
    INTENT_PATTERNS = {
        "PREDICTION": [
            "predict", "forecast", "projection", "estimate", "future",
            "what will", "next month", "next quarter", "next year",
            "expected sales", "anticipated", "predict for", "forecast for"
        ],
        "ADVANCED_ANALYSIS": [
            "trend", "pattern", "seasonality", "seasonal", "anomaly",
            "unusual", "spike", "drop", "growth rate", "velocity",
            "acceleration", "compare periods", "period comparison",
            "analyze trend", "detect pattern"
        ],
        "ONLINE_SALES": [
            "online", "ecommerce", "e-commerce", "web", "website",
            "utm", "marketing", "campaign", "device", "country"
        ],
        "OFFLINE_SALES": [
            "offline", "wholesale", "b2b", "retail", "reseller",
            "distributor", "partner", "sellout"
        ],
        "COMPARISON": [
            "compare", "vs", "versus", "difference", "compared to",
            "online vs offline", "channel comparison"
        ],
        "TIME_ANALYSIS": [
            "over time", "monthly", "quarterly", "year over year",
            "growth", "decline", "last month", "this year"
        ],
        "PRODUCT_ANALYSIS": [
            "product", "sku", "ean", "category", "top selling",
            "best seller", "worst", "underperforming"
        ],
        "RESELLER_ANALYSIS": [
            "reseller", "partner", "distributor", "by reseller",
            "which reseller", "reseller performance"
        ]
    }

    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "date_range": [
            r"last (\d+) (day|week|month|year)s?",
            r"in (january|february|march|april|may|june|july|august|september|october|november|december)",
            r"in (202\d)",
            r"(Q[1-4]) (202\d)"
        ],
        "prediction_target": [
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(202\d)",
            r"(Q[1-4])\s+(202\d)",
            r"next (month|quarter|year)",
            r"for (202\d)"
        ],
        "analysis_type": [
            r"(trend|seasonality|anomaly|growth rate|velocity|pattern)"
        ],
        "product_ean": [
            r"\b\d{13}\b"  # 13-digit EAN
        ],
        "reseller_name": [
            r"(Galilu|Boxnox|Skins|CDLC|Selfridges|Liberty|Ukraine|Continuity)"
        ],
        "metric": [
            r"(revenue|sales|quantity|units|orders|customers)"
        ],
        "comparison_operator": [
            r"(greater than|more than|less than|below|above|over|under)",
            r"(>|<|>=|<=)"
        ]
    }

    def detect_intent(self, query: str) -> QueryIntent:
        """
        Detect intent from user query

        Args:
            query: Natural language query

        Returns:
            QueryIntent with detected type and metadata
        """
        query_lower = query.lower()

        # Calculate scores for each intent
        intent_scores = {}
        for intent_type, keywords in self.INTENT_PATTERNS.items():
            score = self._calculate_intent_score(query_lower, keywords)
            if score > 0:
                intent_scores[intent_type] = score

        # Determine primary intent
        if not intent_scores:
            primary_intent = "GENERAL"
            confidence = 0.5
        else:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[primary_intent], 1.0)

        # Extract entities
        entities = self._extract_entities(query)

        # Generate suggested filters
        suggested_filters = self._generate_filters(primary_intent, entities)

        return QueryIntent(
            intent_type=primary_intent,
            confidence=confidence,
            entities=entities,
            suggested_filters=suggested_filters
        )

    def _calculate_intent_score(self, query: str, keywords: List[str]) -> float:
        """Calculate intent score based on keyword matches"""
        score = 0.0
        word_count = len(query.split())

        for keyword in keywords:
            if keyword in query:
                # Weight by keyword length (more specific = higher score)
                keyword_weight = len(keyword.split()) / max(word_count, 1)
                score += keyword_weight

        return score

    def _extract_entities(self, query: str) -> Dict[str, any]:
        """Extract entities from query"""
        entities = {}

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    entities[entity_type] = match.group(0)
                    break

        # Extract numeric values
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', query)
        if numbers:
            entities["numeric_values"] = [float(n) for n in numbers]

        return entities

    def _generate_filters(
        self,
        intent_type: str,
        entities: Dict[str, any]
    ) -> Optional[Dict]:
        """Generate suggested filters based on intent and entities"""
        filters = {}

        # Table selection based on intent
        if intent_type == "ONLINE_SALES":
            filters["table"] = "ecommerce_orders"
        elif intent_type == "OFFLINE_SALES":
            filters["table"] = "sellout_entries2"
        elif intent_type == "COMPARISON":
            filters["tables"] = ["ecommerce_orders", "sellout_entries2"]
        elif intent_type in ["PREDICTION", "ADVANCED_ANALYSIS"]:
            # Prefer online data (more granular), fall back to offline
            filters["table"] = "ecommerce_orders"
            filters["fallback_table"] = "sellout_entries2"

        # Date filters
        if "date_range" in entities:
            filters["date_filter"] = entities["date_range"]

        # Prediction-specific filters
        if "prediction_target" in entities:
            filters["prediction_target"] = entities["prediction_target"]

        # Analysis type filters
        if "analysis_type" in entities:
            filters["analysis_type"] = entities["analysis_type"]

        # Product filters
        if "product_ean" in entities:
            filters["product_ean"] = entities["product_ean"]

        # Reseller filters
        if "reseller_name" in entities:
            filters["reseller"] = entities["reseller_name"]

        # Metric selection
        if "metric" in entities:
            filters["metric"] = entities["metric"]
        else:
            # Default metrics by intent
            if intent_type in ["ONLINE_SALES", "OFFLINE_SALES", "PREDICTION", "ADVANCED_ANALYSIS"]:
                filters["metrics"] = ["sales_eur", "quantity"]

        return filters if filters else None

    def get_intent_hints(self, intent_type: str) -> List[str]:
        """
        Get helpful hints for specific intent types

        Args:
            intent_type: Intent type

        Returns:
            List of query hints
        """
        hints = {
            "PREDICTION": [
                "Try: 'What's your prediction for October 2025?'",
                "Try: 'Forecast my sales for next quarter'",
                "Try: 'What will my revenue be in December?'",
                "Try: 'Predict sales for the next 3 months'"
            ],
            "ADVANCED_ANALYSIS": [
                "Try: 'Analyze my sales trends'",
                "Try: 'Detect seasonality patterns in my data'",
                "Try: 'Show me any unusual spikes or drops'",
                "Try: 'What's my sales velocity?'",
                "Try: 'Compare Q1 2024 to Q1 2025'"
            ],
            "ONLINE_SALES": [
                "Try: 'Show me online sales for the last month'",
                "Try: 'What are the top products from our website?'",
                "Try: 'Which countries generate the most revenue?'"
            ],
            "OFFLINE_SALES": [
                "Try: 'Show me wholesale sales by reseller'",
                "Try: 'What are my best performing products in retail?'",
                "Try: 'How much did we sell through Galilu last quarter?'"
            ],
            "COMPARISON": [
                "Try: 'Compare online vs offline sales this year'",
                "Try: 'Show me the difference between Q1 and Q2'",
                "Try: 'Which channel performs better for product X?'"
            ],
            "TIME_ANALYSIS": [
                "Try: 'Show me sales trend for the last 6 months'",
                "Try: 'What is our month-over-month growth?'",
                "Try: 'Compare this year to last year'"
            ],
            "PRODUCT_ANALYSIS": [
                "Try: 'What are my top 10 products by revenue?'",
                "Try: 'Which products are underperforming?'",
                "Try: 'Show me sales for EAN 1234567890123'"
            ],
            "RESELLER_ANALYSIS": [
                "Try: 'Which reseller has the highest sales?'",
                "Try: 'Show me performance by country'",
                "Try: 'How is Boxnox performing compared to Galilu?'"
            ],
            "GENERAL": [
                "Try: 'Show me my total sales'",
                "Try: 'What are my sales this month?'",
                "Try: 'Give me an overview of my business'"
            ]
        }

        return hints.get(intent_type, hints["GENERAL"])
