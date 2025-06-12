import sys
import os
import unittest
from unittest.mock import patch, AsyncMock, MagicMock, call
from collections import OrderedDict
from typing import List, Dict, Any, AsyncGenerator
import json

# Adjust sys.path to include the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory

# Modules to test
from src.backend.chat_service.llm_service import LLMService, DEFAULTAIRESPONSE
from src.backend.db.database_manager import SenderType

# Mocked LLM chunk response
class MockLLMResponseChunk:
    def __init__(self, content: str, role: str = "assistant"):
        self.message = AIMessage(content=content) if role == "assistant" else HumanMessage(content=content)
        self.content = content # For direct access if message attribute isn't used by all parts of the code

class TestLLMServiceGetResponse(unittest.IsolatedAsyncioTestCase):

    @patch('src.backend.chat_service.llm_service.DatabaseManager')
    @patch('src.backend.chat_service.llm_service.WeaviateManager')
    @patch('src.backend.chat_service.llm_service.ChatOpenAI') # Default LLM provider
    @patch('src.backend.chat_service.llm_service.logger')
    async def asyncSetUp(self, MockLogger, MockChatOpenAI, MockWeaviateManager, MockDatabaseManager):
        self.mock_logger = MockLogger
        self.mock_chat_openai_class = MockChatOpenAI
        self.mock_llm_instance = AsyncMock()
        self.mock_chat_openai_class.return_value = self.mock_llm_instance

        self.mock_weaviate_manager_class = MockWeaviateManager
        self.mock_weaviate_instance = AsyncMock()
        self.mock_weaviate_manager_class.return_value = self.mock_weaviate_instance

        self.mock_db_manager_class = MockDatabaseManager
        self.mock_db_instance = AsyncMock()
        self.mock_db_instance.get_paginated_chat_messages.return_value = [] # Default no history
        self.mock_db_manager_class.return_value = self.mock_db_instance

        # Initialize LLMService - this will now use the mocked ChatOpenAI
        # Ensure that the LLMService uses a known provider that maps to ChatOpenAI for these tests
        LLMService.LLMProvider = "OPENAI"
        LLMService.model = "gpt-test"
        # Clear histories and reinitialize LLMService for a cleaner state
        LLMService.histories = OrderedDict()
        # Forcing re-initialization of the llm instance within LLMService
        # This is tricky due to Singleton and class-level llm.
        # The ideal way is that LLMService().llm gets set by its init.
        # We mock ChatOpenAI which is called by _initialize_llm
        self.llm_service = LLMService(buffer_size=3)
        # Ensure the service's llm instance is indeed our mock after re-init
        self.llm_service.llm = self.mock_llm_instance
        LLMService.llm = self.mock_llm_instance # Also set the class variable if it's used directly

        self.user_id = "test_user"
        self.customer_guid = "test_customer"
        self.chat_id = "test_chat"
        self.session_id = f"{self.user_id}:{self.customer_guid}:{self.chat_id}"

        # Default LLM astream responses
        self.default_rewritten_query_response = [MockLLMResponseChunk(content="rewritten query")]
        self.default_final_answer_response = [MockLLMResponseChunk(content="final answer")]

    async def _consume_async_generator(self, gen: AsyncGenerator[Dict[str, Any], None]) -> List[Dict[str, Any]]:
        items = []
        async for item in gen:
            items.append(item)
        return items

    async def _generate_async_chunks(self, chunks: List[MockLLMResponseChunk]) -> AsyncGenerator[MockLLMResponseChunk, None]:
        for chunk in chunks:
            yield chunk

    async def test_get_response_llm_mode_with_relevant_docs(self):
        LLMService.set_llm_response("LLM")
        question = "What is product X?"
        rewritten_query = "Details about product X"
        search_results_data = [{"title": "Product X Page", "content": "Product X is amazing."}]
        final_answer_content = "Product X is amazing based on the provided documents."

        self.mock_llm_instance.astream.side_effect = [
            self._generate_async_chunks(self.default_rewritten_query_response), # For rewrite
            self._generate_async_chunks([MockLLMResponseChunk(content=final_answer_content)]) # For final answer
        ]
        self.default_rewritten_query_response[0].message.content = rewritten_query # Adjust mock content

        self.mock_weaviate_instance.search_query.return_value = search_results_data

        responses = await self._consume_async_generator(
            self.llm_service.get_response(question, self.user_id, self.customer_guid, self.chat_id)
        )

        self.assertTrue(len(responses) >= 2)
        self.assertEqual(responses[0]['choices'][0]['delta']['content'], final_answer_content)
        self.assertEqual(responses[-1]['choices'][0]['finish_reason'], "stop")

        # Check calls
        # First call to LLM for query rewrite
        rewrite_call = self.mock_llm_instance.astream.call_args_list[0][0][0]
        self.assertEqual(rewrite_call[-1].content, "Based on our conversation so far, please rewrite the last user question to be a concise, self-contained query suitable for a vector database search. Only output the rewritten query itself, with no preamble or explanation.")

        # Call to Weaviate
        self.mock_weaviate_instance.search_query.assert_called_once_with(self.customer_guid, rewritten_query, alpha=0.5)

        # Second call to LLM for final answer
        final_answer_call_args = self.mock_llm_instance.astream.call_args_list[1][0][0]
        self.assertIsInstance(final_answer_call_args[-2], SystemMessage) # System message with context
        self.assertIn(json.dumps(search_results_data), final_answer_call_args[-2].content)
        self.assertEqual(final_answer_call_args[-1].content, question) # Last message is user question

        history = self.llm_service.get_conversation_history(self.user_id, self.customer_guid, self.chat_id)
        self.assertEqual(history.chat_memory.messages[-2].content, question)
        self.assertEqual(history.chat_memory.messages[-1].content, final_answer_content)

    async def test_get_response_llm_mode_no_docs_found(self):
        LLMService.set_llm_response("LLM")
        question = "Non-existent topic?"
        rewritten_query = "Search for non-existent topic"
        search_results_data = []
        final_answer_content = "I couldn't find specific information in the documents. From my general knowledge..."

        self.mock_llm_instance.astream.side_effect = [
            self._generate_async_chunks([MockLLMResponseChunk(content=rewritten_query)]),
            self._generate_async_chunks([MockLLMResponseChunk(content=final_answer_content)])
        ]
        self.mock_weaviate_instance.search_query.return_value = search_results_data

        responses = await self._consume_async_generator(
            self.llm_service.get_response(question, self.user_id, self.customer_guid, self.chat_id)
        )

        self.assertEqual(responses[0]['choices'][0]['delta']['content'], final_answer_content)
        self.mock_weaviate_instance.search_query.assert_called_once_with(self.customer_guid, rewritten_query, alpha=0.5)

        final_llm_call_args = self.mock_llm_instance.astream.call_args_list[1][0][0]
        self.assertIn(json.dumps(search_results_data), final_llm_call_args[-2].content)

        history = self.llm_service.get_conversation_history(self.user_id, self.customer_guid, self.chat_id)
        self.assertEqual(history.chat_memory.messages[-1].content, final_answer_content)

    async def test_get_response_llm_mode_query_rewrite_fallback(self):
        LLMService.set_llm_response("LLM")
        question = "A complex question needing fallback"
        final_answer_content = "Answering based on original question as rewrite failed."

        self.mock_llm_instance.astream.side_effect = [
            self._generate_async_chunks([MockLLMResponseChunk(content="")]), # Empty rewrite
            self._generate_async_chunks([MockLLMResponseChunk(content=final_answer_content)])
        ]
        self.mock_weaviate_instance.search_query.return_value = []

        await self._consume_async_generator(
            self.llm_service.get_response(question, self.user_id, self.customer_guid, self.chat_id)
        )
        self.mock_weaviate_instance.search_query.assert_called_once_with(self.customer_guid, question, alpha=0.5)
        self.mock_logger.warning.assert_any_call(f"Rewritten query is empty for session {self.session_id}. Falling back to original question for search.")

    async def test_get_response_non_llm_mode(self):
        LLMService.set_llm_response("NONLLM")
        question = "Hello?"

        responses = await self._consume_async_generator(
            self.llm_service.get_response(question, self.user_id, self.customer_guid, self.chat_id)
        )
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0]['choices'][0]['delta']['content'], DEFAULTAIRESPONSE)
        self.assertEqual(responses[0]['choices'][0]['finish_reason'], "stop")

        self.mock_llm_instance.astream.assert_not_called()
        self.mock_weaviate_instance.search_query.assert_not_called()

        history = self.llm_service.get_conversation_history(self.user_id, self.customer_guid, self.chat_id)
        self.assertEqual(history.chat_memory.messages[-2].content, question)
        self.assertEqual(history.chat_memory.messages[-1].content, DEFAULTAIRESPONSE)

    async def test_get_response_llm_mode_weaviate_error(self):
        LLMService.set_llm_response("LLM")
        question = "Search that causes error"
        rewritten_query = "Error prone search query"
        error_message = "Weaviate connection failed"
        final_answer_content = "Sorry, I encountered an issue searching our knowledge base."

        self.mock_llm_instance.astream.side_effect = [
            self._generate_async_chunks([MockLLMResponseChunk(content=rewritten_query)]),
            self._generate_async_chunks([MockLLMResponseChunk(content=final_answer_content)])
        ]
        self.mock_weaviate_instance.search_query.side_effect = Exception(error_message)

        responses = await self._consume_async_generator(
            self.llm_service.get_response(question, self.user_id, self.customer_guid, self.chat_id)
        )

        self.assertEqual(responses[0]['choices'][0]['delta']['content'], final_answer_content)
        self.mock_logger.error.assert_any_call(f"Error during Weaviate search for session {self.session_id}: {error_message}")

        final_llm_call_args = self.mock_llm_instance.astream.call_args_list[1][0][0]
        self.assertIn(json.dumps({"error": error_message}), final_llm_call_args[-2].content)

        history = self.llm_service.get_conversation_history(self.user_id, self.customer_guid, self.chat_id)
        self.assertEqual(history.chat_memory.messages[-1].content, final_answer_content)

    async def test_query_rewriting_with_history(self):
        LLMService.set_llm_response("LLM")
        prev_question = "Tell me about dogs."
        prev_answer = "Dogs are friendly animals."
        current_question = "What about cats?"
        expected_rewritten_current_question = "Information about cats given prior discussion on dogs."

        # Setup history in mock DB
        self.mock_db_instance.get_paginated_chat_messages.return_value = [
            {'sender_type': SenderType.CUSTOMER.value, 'message': prev_question, 'timestamp': '123'},
            {'sender_type': SenderType.SYSTEM.value, 'message': prev_answer, 'timestamp': '124'}
        ]
        # Force LLMService to reload history for this specific test scenario
        LLMService.histories.clear()

        self.mock_llm_instance.astream.side_effect = [
            self._generate_async_chunks([MockLLMResponseChunk(content=expected_rewritten_current_question)]),
            self._generate_async_chunks([MockLLMResponseChunk(content="Cats are also great.")])
        ]
        self.mock_weaviate_instance.search_query.return_value = []

        await self._consume_async_generator(
            self.llm_service.get_response(current_question, self.user_id, self.customer_guid, self.chat_id)
        )

        rewrite_call_args = self.mock_llm_instance.astream.call_args_list[0][0][0]

        # Expected messages for rewrite: SysPrompt, Human(prev_q), AI(prev_a), Human(curr_q), RewriteInstruction
        self.assertIsInstance(rewrite_call_args[0], SystemMessage) # Initial System Prompt
        self.assertEqual(rewrite_call_args[1].content, prev_question)
        self.assertIsInstance(rewrite_call_args[2], AIMessage)
        self.assertEqual(rewrite_call_args[2].content, prev_answer)
        self.assertEqual(rewrite_call_args[3].content, current_question)
        self.assertEqual(rewrite_call_args[4].content, "Based on our conversation so far, please rewrite the last user question to be a concise, self-contained query suitable for a vector database search. Only output the rewritten query itself, with no preamble or explanation.")

        self.mock_weaviate_instance.search_query.assert_called_with(self.customer_guid, expected_rewritten_current_question, alpha=0.5)

    async def test_context_injection_prompt_format(self):
        LLMService.set_llm_response("LLM")
        question = "What is the context?"
        rewritten_query = "Context query"
        search_results = [{"doc_id": "1", "text_chunk": "This is a piece of context."}]
        search_results_str = json.dumps(search_results)

        expected_system_prompt_for_final_answer = (
            f"Provided context from a document search (use if relevant to the user's last question): {search_results_str}. "
            "Analyze this context to answer the user's question. "
            "If the context is relevant and sufficient, base your answer primarily on it. "
            "If the context is not relevant, insufficient, or if the question is general conversation (e.g., a greeting), "
            "answer from your general knowledge. When answering from general knowledge because the context was not helpful, "
            "please explicitly state that the provided documents did not contain the specific information needed. "
            "Maintain a professional tone and avoid inner monologue. The user's question is next."
        )

        self.mock_llm_instance.astream.side_effect = [
            self._generate_async_chunks([MockLLMResponseChunk(content=rewritten_query)]),
            self._generate_async_chunks([MockLLMResponseChunk(content="Acknowledged context.")])
        ]
        self.mock_weaviate_instance.search_query.return_value = search_results

        await self._consume_async_generator(
            self.llm_service.get_response(question, self.user_id, self.customer_guid, self.chat_id)
        )

        final_llm_call_messages = self.mock_llm_instance.astream.call_args_list[1][0][0]

        # messages_for_llm structure:
        # 1. Initial System Prompt (from get_or_create_history)
        # 2. Injected Context System Prompt (created in get_response)
        # 3. User's current question (HumanMessage)

        self.assertEqual(len(final_llm_call_messages), 3)
        self.assertIsInstance(final_llm_call_messages[0], SystemMessage) # Initial system prompt
        self.assertNotEqual(final_llm_call_messages[0].content, expected_system_prompt_for_final_answer) # Should be the general one

        self.assertIsInstance(final_llm_call_messages[1], SystemMessage) # Context injection prompt
        self.assertEqual(final_llm_call_messages[1].content, expected_system_prompt_for_final_answer)

        self.assertIsInstance(final_llm_call_messages[2], HumanMessage)
        self.assertEqual(final_llm_call_messages[2].content, question)

    async def asyncTearDown(self):
        LLMService.histories.clear()
        LLMService.LLMProvider = "OPENAI"
        LLMService.model = "gpt-test"
        # Reset mocks for other tests if necessary, though IsolatedAsyncioTestCase helps
        self.mock_llm_instance.reset_mock()
        self.mock_weaviate_instance.reset_mock()
        self.mock_db_instance.reset_mock()

if __name__ == '__main__':
    unittest.main()
