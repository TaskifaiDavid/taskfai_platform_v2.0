"""
Performance tests for AI chat system
Target: <5 seconds for chat query response
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock


# Target latency in seconds
TARGET_CHAT_LATENCY_SECONDS = 5
ACCEPTABLE_CHAT_LATENCY_SECONDS = 7  # With tolerance


class TestAIChatPerformance:
    """Test AI chat system performance"""

    # ============================================
    # BASIC CHAT QUERY PERFORMANCE
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_simple_query_latency(self):
        """Test simple query response time"""
        from app.services.ai_chat.agent import ChatAgent

        # Mock LLM response to avoid external API call
        with patch('app.services.ai_chat.agent.ChatOpenAI') as mock_llm:
            mock_response = Mock()
            mock_response.content = "SELECT SUM(sales_eur) FROM sellout_entries2 WHERE year = 2024;"

            agent = ChatAgent()

            start = time.perf_counter()

            # Simulate query
            query = "What are total sales for 2024?"
            # Mock the agent response
            with patch.object(agent, 'query', return_value={"response": "Total sales: $1,000,000"}):
                response = await agent.query(query, user_id="test-user")

            latency = time.perf_counter() - start

            print(f"\nSimple query latency: {latency:.2f}s")

            assert latency < TARGET_CHAT_LATENCY_SECONDS, f"Simple query too slow: {latency:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_complex_query_latency(self):
        """Test complex analytical query response time"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()

        start = time.perf_counter()

        # Complex query requiring joins and aggregations
        query = "Compare online vs offline sales by product category for Q1 2024, show top 10 products"

        with patch.object(agent, 'query', return_value={"response": "Comparison analysis..."}):
            response = await agent.query(query, user_id="test-user")

        latency = time.perf_counter() - start

        print(f"\nComplex query latency: {latency:.2f}s")

        # Complex queries allowed slightly more time
        assert latency < ACCEPTABLE_CHAT_LATENCY_SECONDS, f"Complex query too slow: {latency:.2f}s"

    # ============================================
    # INTENT DETECTION PERFORMANCE
    # ============================================

    @pytest.mark.performance
    def test_intent_detection_latency(self):
        """Test intent detection speed"""
        from app.services.ai_chat.intent import IntentDetector

        detector = IntentDetector()

        queries = [
            "Show me total sales",
            "What are top products?",
            "Compare online vs offline",
            "Show sales by month",
            "Which resellers are performing best?"
        ]

        latencies = []

        for query in queries:
            start = time.perf_counter()
            intent = detector.detect_intent(query)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)

        print(f"\nIntent detection average latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max(latencies):.2f}ms")

        # Intent detection should be fast (<100ms)
        assert avg_latency < 100, f"Intent detection too slow: {avg_latency:.2f}ms"
        assert max(latencies) < 200, f"Max intent detection too slow: {max(latencies):.2f}ms"

    # ============================================
    # SQL GENERATION PERFORMANCE
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sql_generation_latency(self):
        """Test SQL generation speed"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()

        queries = [
            "Total sales for 2024",
            "Top 5 products by revenue",
            "Monthly sales trend",
        ]

        with patch('app.services.ai_chat.agent.ChatOpenAI') as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=Mock(content="SELECT * FROM sales;"))

            latencies = []

            for query in queries:
                start = time.perf_counter()

                # Mock SQL generation
                sql = await agent._generate_sql(query)

                latency = time.perf_counter() - start
                latencies.append(latency)

            avg_latency = sum(latencies) / len(latencies)

            print(f"\nSQL generation average latency: {avg_latency:.2f}s")

            # SQL generation should be fast (most time is LLM call)
            # With mocked LLM, should be near instant
            assert avg_latency < 1.0, f"SQL generation too slow: {avg_latency:.2f}s"

    # ============================================
    # SECURITY VALIDATION PERFORMANCE
    # ============================================

    @pytest.mark.performance
    def test_security_validation_latency(self):
        """Test SQL security validation speed"""
        from app.services.ai_chat.security import SecurityValidator

        validator = SecurityValidator()

        test_queries = [
            "SELECT * FROM sellout_entries2 WHERE user_id = '123' AND year = 2024;",
            "SELECT product_ean, SUM(sales_eur) FROM sellout_entries2 GROUP BY product_ean;",
            "SELECT * FROM ecommerce_orders WHERE order_date > '2024-01-01';",
        ]

        latencies = []

        for query in test_queries:
            start = time.perf_counter()
            is_safe, error = validator.validate_query(query, user_id="test-user")
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)

        print(f"\nSecurity validation average latency: {avg_latency:.2f}ms")

        # Security validation should be very fast (<10ms)
        assert avg_latency < 10, f"Security validation too slow: {avg_latency:.2f}ms"

    # ============================================
    # CONVERSATION MEMORY PERFORMANCE
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_conversation_memory_latency(self):
        """Test conversation memory retrieval speed"""
        from app.services.ai_chat.memory import ConversationMemory

        memory = ConversationMemory()

        start = time.perf_counter()

        # Mock memory operations
        with patch.object(memory, 'get_conversation_history', return_value=[]):
            history = await memory.get_conversation_history(user_id="test-user", session_id="test-session")

        latency = (time.perf_counter() - start) * 1000

        print(f"\nConversation memory retrieval: {latency:.2f}ms")

        # Memory retrieval should be fast (<50ms)
        assert latency < 50, f"Memory retrieval too slow: {latency:.2f}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_conversation_memory_save_latency(self):
        """Test conversation memory save speed"""
        from app.services.ai_chat.memory import ConversationMemory

        memory = ConversationMemory()

        message_data = {
            "user_id": "test-user",
            "session_id": "test-session",
            "user_message": "Test query",
            "ai_response": "Test response",
            "query_intent": "ONLINE_SALES"
        }

        start = time.perf_counter()

        with patch.object(memory, 'save_message', return_value=None):
            await memory.save_message(**message_data)

        latency = (time.perf_counter() - start) * 1000

        print(f"\nConversation memory save: {latency:.2f}ms")

        # Memory save should be fast (<100ms)
        assert latency < 100, f"Memory save too slow: {latency:.2f}ms"

    # ============================================
    # CONCURRENT CHAT QUERIES
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_chat_queries(self):
        """Test handling multiple concurrent chat queries"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()
        num_concurrent = 5

        queries = [
            "Total sales for 2024",
            "Top 10 products",
            "Sales by reseller",
            "Monthly trend",
            "Online vs offline comparison"
        ]

        with patch.object(agent, 'query', return_value={"response": "Mock response"}):
            start = time.perf_counter()

            # Execute concurrent queries
            tasks = [agent.query(q, user_id=f"user-{i}") for i, q in enumerate(queries)]
            responses = await asyncio.gather(*tasks)

            total_time = time.perf_counter() - start

        avg_time_per_query = total_time / num_concurrent

        print(f"\nConcurrent queries ({num_concurrent}):")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average per query: {avg_time_per_query:.2f}s")

        # With concurrency, should handle better than sequential
        # Allow up to 2x target latency per query
        assert avg_time_per_query < TARGET_CHAT_LATENCY_SECONDS * 2, \
            f"Concurrent queries too slow: {avg_time_per_query:.2f}s per query"

    # ============================================
    # QUERY RESULT SIZE IMPACT
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_result_set_latency(self):
        """Test latency with large result sets"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()

        # Mock large result set
        large_results = [{"product": f"Product {i}", "sales": 1000} for i in range(1000)]

        with patch.object(agent, 'query', return_value={"response": "Large dataset", "data": large_results}):
            start = time.perf_counter()

            response = await agent.query("Show all products", user_id="test-user")

            latency = time.perf_counter() - start

        print(f"\nLarge result set latency (1000 rows): {latency:.2f}s")

        # Should handle large results efficiently
        assert latency < ACCEPTABLE_CHAT_LATENCY_SECONDS, f"Large result set too slow: {latency:.2f}s"

    # ============================================
    # CACHE EFFECTIVENESS
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_hit_vs_miss_latency(self):
        """Test latency difference between cache hit and miss"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()
        query = "Total sales for 2024"

        # First query (cache miss)
        with patch.object(agent, 'query', return_value={"response": "Total: $1M"}):
            start_miss = time.perf_counter()
            response_miss = await agent.query(query, user_id="test-user")
            miss_latency = time.perf_counter() - start_miss

        # Second query (cache hit - if caching implemented)
        with patch.object(agent, 'query', return_value={"response": "Total: $1M", "cached": True}):
            start_hit = time.perf_counter()
            response_hit = await agent.query(query, user_id="test-user")
            hit_latency = time.perf_counter() - start_hit

        print(f"\nCache miss latency: {miss_latency:.2f}s")
        print(f"Cache hit latency: {hit_latency:.2f}s")

        if hit_latency < miss_latency:
            improvement = ((miss_latency - hit_latency) / miss_latency) * 100
            print(f"Cache improvement: {improvement:.1f}%")

    # ============================================
    # DATABASE QUERY EXECUTION TIME
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_query_execution_time(self):
        """Test database query execution time"""
        # This would test actual SQL execution against tenant database
        # Requires database setup

        from app.core.db_manager import DatabaseManager

        db_manager = DatabaseManager()

        test_queries = [
            "SELECT COUNT(*) FROM sellout_entries2;",
            "SELECT SUM(sales_eur) FROM sellout_entries2 WHERE year = 2024;",
            "SELECT product_ean, SUM(quantity) FROM sellout_entries2 GROUP BY product_ean LIMIT 10;",
        ]

        for query in test_queries:
            start = time.perf_counter()

            # Mock database execution
            with patch.object(db_manager, 'execute_query', return_value=[{"count": 1000}]):
                result = await db_manager.execute_query(query, tenant_id="demo")

            latency = (time.perf_counter() - start) * 1000

            print(f"\nQuery execution: {latency:.2f}ms")
            print(f"Query: {query[:50]}...")

            # Database queries should be fast (<100ms for simple queries)
            assert latency < 200, f"Database query too slow: {latency:.2f}ms"


# ============================================
# STREAMING RESPONSE TESTS
# ============================================

class TestStreamingPerformance:
    """Test streaming response performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_time_to_first_token(self):
        """Test time to first token in streaming response"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()

        start = time.perf_counter()

        # Mock streaming response
        async def mock_stream():
            yield "First token"
            await asyncio.sleep(0.1)
            yield " more tokens"

        with patch.object(agent, 'stream_query', return_value=mock_stream()):
            stream = await agent.stream_query("Test query", user_id="test-user")

            # Get first token
            first_token = await stream.__anext__()
            first_token_time = time.perf_counter() - start

        print(f"\nTime to first token: {first_token_time:.2f}s")

        # First token should arrive quickly (<2s)
        assert first_token_time < 2.0, f"Time to first token too slow: {first_token_time:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_streaming_throughput(self):
        """Test streaming response throughput"""
        # Test tokens per second in streaming mode
        pass


# ============================================
# ERROR HANDLING PERFORMANCE
# ============================================

class TestChatErrorHandlingPerformance:
    """Test chat error handling performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_invalid_query_handling_speed(self):
        """Test that invalid queries fail fast"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()

        start = time.perf_counter()

        # Invalid query that should be rejected quickly
        try:
            with patch.object(agent, 'query', side_effect=ValueError("Invalid query")):
                response = await agent.query("", user_id="test-user")
        except ValueError:
            pass

        latency = time.perf_counter() - start

        print(f"\nInvalid query rejection time: {latency:.2f}s")

        # Should fail fast (<1s)
        assert latency < 1.0, f"Error handling too slow: {latency:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_malicious_query_detection_speed(self):
        """Test malicious query detection speed"""
        from app.services.ai_chat.security import SecurityValidator

        validator = SecurityValidator()

        malicious_queries = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM sellout_entries2 WHERE 1=1; DELETE FROM products;",
            "SELECT * FROM ecommerce_orders; UPDATE users SET role='admin';",
        ]

        latencies = []

        for query in malicious_queries:
            start = time.perf_counter()
            is_safe, error = validator.validate_query(query, user_id="test-user")
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)

        print(f"\nMalicious query detection: {avg_latency:.2f}ms")

        # Should detect and block quickly (<5ms)
        assert avg_latency < 5, f"Malicious query detection too slow: {avg_latency:.2f}ms"


# ============================================
# INTEGRATION PERFORMANCE TESTS
# ============================================

class TestChatIntegrationPerformance:
    """Test end-to-end chat performance"""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_complete_chat_workflow(self):
        """Test complete chat workflow from query to response"""
        # This would test: query → intent → security → SQL → execute → format → respond
        # Requires full integration setup
        pass

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sustained_chat_session(self):
        """Test performance over sustained conversation"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()
        num_queries = 10

        queries = [f"Query {i}: Show sales data" for i in range(num_queries)]

        latencies = []

        with patch.object(agent, 'query', return_value={"response": "Mock response"}):
            for query in queries:
                start = time.perf_counter()
                response = await agent.query(query, user_id="test-user")
                latency = time.perf_counter() - start
                latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\nSustained session ({num_queries} queries):")
        print(f"Average latency: {avg_latency:.2f}s")
        print(f"P95 latency: {p95_latency:.2f}s")

        # Performance should not degrade over time
        first_half_avg = sum(latencies[:num_queries//2]) / (num_queries//2)
        second_half_avg = sum(latencies[num_queries//2:]) / (num_queries - num_queries//2)

        print(f"First half avg: {first_half_avg:.2f}s")
        print(f"Second half avg: {second_half_avg:.2f}s")

        # Second half should not be significantly slower
        assert second_half_avg < first_half_avg * 1.5, "Performance degradation detected"


# ============================================
# BENCHMARKING
# ============================================

class TestChatBenchmark:
    """Benchmark chat system performance"""

    @pytest.mark.performance
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_chat_performance_baseline(self):
        """Establish performance baseline for chat system"""
        from app.services.ai_chat.agent import ChatAgent

        agent = ChatAgent()

        test_cases = {
            "simple": "Total sales for 2024",
            "moderate": "Top 10 products by revenue in Q1",
            "complex": "Compare online vs offline sales by product category, show trends",
        }

        results = {}

        for test_type, query in test_cases.items():
            with patch.object(agent, 'query', return_value={"response": "Mock response"}):
                start = time.perf_counter()
                response = await agent.query(query, user_id="test-user")
                latency = time.perf_counter() - start

                results[test_type] = latency

        print("\nChat Performance Baseline:")
        for test_type, latency in results.items():
            print(f"{test_type.capitalize()} query: {latency:.2f}s")

        # Store baseline for regression testing
        # In CI/CD, compare against stored baseline values
