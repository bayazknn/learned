from typing import List, Dict, Any, Optional, TypedDict, Annotated, AsyncGenerator
import uuid
import logging
import asyncio
from contextlib import asynccontextmanager, suppress
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.tools.retriever_tool import async_retriever_tool
from backend.states.agent_state import AgentState
from backend.prompts.agent_prompts import get_query_prompt, get_chatbot_prompt
from backend import crud
from backend.database import SessionLocal
from backend.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)
DATABASE_URL = settings.DATABASE_URL

# Define the LangGraph state with additional fields for our workflow
class LangGraphState(TypedDict):
    """State for LangGraph RAG workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    project_id: Optional[str]
    video_ids: Optional[List[str]]
    generated_queries: Optional[List[str]]
    retrieval_results: Optional[List[Dict[str, Any]]]
    final_response: Optional[str]
    thread_id: Optional[str]
    query_generate_llm_model: Optional[str]
    chat_llm_model: Optional[str]

class LangGraphAgent:
    """LangGraph-based agent with three-step RAG workflow and proper checkpointer management"""

    def __init__(self):
        self.checkpointer_cm = None  # Store the context manager
        self.checkpointer = None     # Store the actual checkpointer instance
        self.graph = None
        self._initialization_lock = asyncio.Lock()
        self._is_initialized = False

    async def initialize(self):
        """Initialize the agent with persistent checkpointer"""
        async with self._initialization_lock:
            if self._is_initialized:
                return
            
            try:
                # Create the async context manager for the checkpointer
                self.checkpointer_cm = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
                
                # Enter the context manager
                self.checkpointer = await self.checkpointer_cm.__aenter__()
                
                # Build and compile the graph with checkpointer
                builder = self._build_graph_builder()
                self.graph = builder.compile(checkpointer=self.checkpointer)
                
                self._is_initialized = True
                logger.info("LangGraph agent initialized successfully with persistent checkpointer")
                
            except Exception as e:
                logger.error(f"Failed to initialize LangGraph agent: {e}")
                await self._cleanup_checkpointer()
                raise

    async def _cleanup_checkpointer(self):
        """Helper to cleanup checkpointer resources"""
        if self.checkpointer_cm and self.checkpointer:
            try:
                await self.checkpointer_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error exiting checkpointer context: {e}")
            finally:
                self.checkpointer = None
                self.checkpointer_cm = None

    def _build_graph_builder(self) -> StateGraph:
        """Build and return the StateGraph builder"""
        builder = StateGraph(LangGraphState)
        
        # Add nodes for each step
        builder.add_node("generate_queries", self._generate_queries_node)
        builder.add_node("retrieve_context", self._retrieve_context_node)
        builder.add_node("generate_response", self._generate_response_node)

        # Define the workflow edges
        builder.add_edge(START, "generate_queries")
        builder.add_edge("generate_queries", "retrieve_context")
        builder.add_edge("retrieve_context", "generate_response")
        builder.add_edge("generate_response", END)
        
        return builder

    async def _ensure_initialized(self):
        """Ensure the agent is initialized before use"""
        if not self._is_initialized:
            await self.initialize()

    async def _get_model(self, model_type: str, temperature: float = 0.1):
        """Get the appropriate model based on type"""
        if model_type == "ollama":
            return init_chat_model(
                model="gemma3:270m",
                model_provider="ollama",
                temperature=temperature,
                base_url="http://localhost:11434"
            )
        elif model_type == "gemini":
            return init_chat_model(
                model="gemini-2.5-flash",
                model_provider="google-genai",
                temperature=temperature
            )
        else:
            # Default to gemini
            return init_chat_model(
                model="gemma3:270m",
                model_provider="ollama",
                temperature=temperature,
                base_url="http://localhost:11434"
            )

    async def _generate_queries_node(self, state: LangGraphState) -> LangGraphState:
        """Step 1: Generate search queries from user input using selected LLM"""
        db = None
        try:
            # Extract user message
            user_message = state["messages"][-1].content if state["messages"] else ""
            query_model = state.get("query_generate_llm_model", "gemini")

            # Get model
            model = await self._get_model(query_model, temperature=0.1)

            # System prompt for query generation
            db = SessionLocal()
            videos = crud.get_videos_by_ids(db, state.get("video_ids"))
            query_prompt = get_query_prompt(user_message, videos)

            # Generate queries
            response = await model.ainvoke([
                # SystemMessage(content="You are a helpful assistant that generates multiple search queries based on a single input query and context."),
                HumanMessage(content=query_prompt)
            ])

            # Parse the generated queries
            queries = [user_message]  # Start with the original user message

            if hasattr(response, 'content'):
                query_text = response.content.strip()
                additional_queries = [q.strip() for q in query_text.split('\n') if q.strip()]
                additional_queries.pop(0)
                queries.extend(additional_queries)

            # Limit to 3 queries max
            # queries = queries[:3]
            logger.info(f"Generated queries: {queries}")

            return {"generated_queries": queries}

        except Exception as e:
            logger.error(f"Error in query generation: {e}")
            # Return a valid state that allows the graph to continue
            return {
                "generated_queries": [user_message],  # Fallback to original query
                "final_response": f"I encountered an issue while processing your request. Let me try to help with a direct response."
            }
        finally:
            if db:
                try:
                    db.close()
                except Exception as close_error:
                    logger.warning(f"Error closing database session: {close_error}")

    async def _retrieve_context_node(self, state: LangGraphState) -> LangGraphState:
        """Step 2: Retrieve relevant context using Qdrant"""
        try:
            if not state.get("generated_queries"):
                return {
                    "retrieval_results": [],
                    "final_response": "No queries generated for retrieval"
                }

            project_id = state.get("project_id")
            if not project_id:
                return {
                    "retrieval_results": [],
                    "final_response": "Project ID not provided"
                }

            # Retrieve context for each query using the async retriever
            all_results = []
            for query in state["generated_queries"]:
                try:
                    results = await async_retriever_tool(
                        query=query,
                        project_id=project_id,
                        video_ids=state.get("video_ids")
                    )
                    all_results.extend(results)  # Extend instead of append to flatten the results
                except Exception as e:
                    logger.warning(f"Failed to retrieve for query '{query}': {e}")

            logger.info(f"Retrieved {len(all_results)} unique results")
            return {"retrieval_results": all_results}

        except Exception as e:
            logger.error(f"Error in context retrieval: {e}")
            return {
                "retrieval_results": [],
                "final_response": f"Error retrieving context: {str(e)}"
            }

    async def _generate_response_node(self, state: LangGraphState) -> LangGraphState:
        """Step 3: Generate final response using retrieved context"""
        try:
            user_message = state["messages"][-1].content if state["messages"] else ""

            if not state.get("retrieval_results"):
                # No context found - provide a helpful fallback response
                fallback_response = f"I don't have specific information about '{user_message}' in my knowledge base. Could you try rephrasing your question or providing more details?"
                return {
                    "messages": [AIMessage(content=fallback_response)],
                    "final_response": fallback_response
                }

            chat_model = state.get("chat_llm_model", "ollama")
            model = await self._get_model(chat_model, temperature=0.3)

            # Prepare context from retrieval results
            context_parts = []
            for result in state["retrieval_results"]:
                if isinstance(result, dict) and result.get('text'):
                    context_parts.append(
                        f"Source: {result.get('source_url', 'Unknown')}\n"
                        f"Content: {result.get('text', '')}\n"
                        f"Relevance score: {result.get('score', 0):.3f}"
                    )

            context_text = "\n\n".join(context_parts) if context_parts else "No relevant context found."

            chat_prompt = get_chatbot_prompt(user_message, context_text)

            # Generate response
            response = await model.ainvoke([
                # SystemMessage(content="You are a helpful AI assistant. Answer questions based on the provided context. Be concise and accurate."),
                HumanMessage(content=chat_prompt)
            ])

            final_response = response.content if hasattr(response, 'content') else "No response generated"

            return {
                "messages": [AIMessage(content=final_response)],
                "final_response": final_response
            }

        except Exception as e:
            logger.error(f"Error in response generation: {e}")
            # Provide a helpful fallback response that still allows the graph to complete
            fallback_response = f"I encountered a technical issue while processing your request about '{user_message}'. This might be due to API rate limits or temporary service issues. Please try again in a moment, or consider using a different model."
            return {
                "messages": [AIMessage(content=fallback_response)],
                "final_response": fallback_response
            }

    async def process_query(
        self,
        query: str,
        project_id: str,
        video_ids: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        query_generate_llm_model: Optional[str] = "gemini",
        chat_llm_model: Optional[str] = "ollama"
    ) -> Dict[str, Any]:
        """Process a query using the LangGraph RAG workflow"""
        try:
            await self._ensure_initialized()

            if not thread_id:
                thread_id = str(uuid.uuid4())

            config = {"configurable": {"thread_id": thread_id}}

            # Load existing messages from checkpointer
            existing_messages = []
            try:
                async for state in self.checkpointer.alist(config, limit=1):
                    channel_values = state.checkpoint.get("channel_values", {})
                    existing_messages = channel_values.get("messages", [])
                    break
            except Exception as e:
                logger.debug(f"No existing state found for thread {thread_id}: {e}")

            # Create initial state with accumulated messages
            initial_state: LangGraphState = {
                "messages": existing_messages + [HumanMessage(content=query)],
                "project_id": project_id,
                "video_ids": video_ids,
                "generated_queries": None,
                "retrieval_results": None,
                "final_response": None,
                "thread_id": thread_id,
                "query_generate_llm_model": query_generate_llm_model,
                "chat_llm_model": chat_llm_model
            }

            final_state = await self.graph.ainvoke(initial_state, config)

            return {
                "success": True,
                "response": final_state.get("final_response", "No response generated"),
                "thread_id": thread_id,
                "generated_queries": final_state.get("generated_queries", []),
                "retrieval_count": len(final_state.get("retrieval_results", [])),
                "project_id": project_id
            }

        except Exception as e:
            logger.error(f"Error in LangGraph processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Error processing your request: {str(e)}",
                "thread_id": thread_id or "unknown"
            }

    async def process_query_streaming(
        self,
        query: str,
        project_id: str,
        video_ids: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        query_generate_llm_model: Optional[str] = "gemini",
        chat_llm_model: Optional[str] = "gemini"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query using streaming with the same persistent checkpointer"""
        stream_started = False
        final_response = ""

        try:
            await self._ensure_initialized()

            if not thread_id:
                thread_id = str(uuid.uuid4())

            config = {"configurable": {"thread_id": thread_id}}

            # Load existing messages from checkpointer
            existing_messages = []
            try:
                async for state in self.checkpointer.alist(config, limit=1):
                    channel_values = state.checkpoint.get("channel_values", {})
                    existing_messages = channel_values.get("messages", [])
                    break
            except Exception as e:
                logger.debug(f"No existing state found for thread {thread_id}: {e}")

            # Create initial state with accumulated messages
            initial_state: LangGraphState = {
                "messages": existing_messages + [HumanMessage(content=query)],
                "project_id": project_id,
                "video_ids": video_ids,
                "generated_queries": None,
                "retrieval_results": None,
                "final_response": None,
                "thread_id": thread_id,
                "query_generate_llm_model": query_generate_llm_model,
                "chat_llm_model": chat_llm_model
            }

            # Use the same graph with persistent checkpointer
            try:
                async for event in self.graph.astream(initial_state, config):
                    stream_started = True

                    for node_name, state in event.items():
                        try:
                            if node_name == "generate_queries" and state.get("generated_queries"):
                                yield {
                                    "type": "queries_generated",
                                    "queries": state["generated_queries"]
                                }

                            elif node_name == "retrieve_context" and state.get("retrieval_results"):
                                yield {
                                    "type": "sources",
                                    "sources": [
                                        {
                                            "url": result.get("source_url", ""),
                                            "content": result.get("text", "")[:200] + "...",
                                            "score": float(result.get("score", 0))
                                        }
                                        for result in state["retrieval_results"][:5]
                                    ]
                                }

                            elif node_name == "generate_response" and state.get("final_response"):
                                response_text = state["final_response"]
                                final_response = response_text

                                # Stream the response word by word with proper error handling
                                words = response_text.split()
                                for i, word in enumerate(words):
                                    try:
                                        yield {
                                            "type": "text",
                                            "content": word + " ",
                                            "is_complete": i == len(words) - 1
                                        }
                                    except GeneratorExit:
                                        # Client disconnected - this is normal, don't log as error
                                        logger.debug("Client disconnected during word streaming")
                                        return
                                    except Exception as word_error:
                                        logger.warning(f"Error streaming word: {word_error}")
                                        continue

                                # Send completion signal
                                try:
                                    yield {
                                        "type": "done",
                                        "content": response_text,
                                        "thread_id": thread_id
                                    }
                                except GeneratorExit:
                                    # Client disconnected - this is normal
                                    logger.debug("Client disconnected during completion signal")
                                    return
                                return

                        except GeneratorExit:
                            # Client disconnected - this is normal, don't log as error
                            logger.debug("Client disconnected during event processing")
                            #return
                            continue
                        except Exception as event_error:
                            logger.error(f"Error processing event from {node_name}: {event_error}")
                            continue    
            except GeneratorExit:
                # Client disconnected - this is normal, don't log as error
                logger.debug("Client disconnected during graph execution")
                return
            except Exception as stream_error:
                logger.error(f"Error in graph streaming: {stream_error}")
                if stream_started:
                    try:
                        yield {"type": "error", "content": f"Stream error: {str(stream_error)}"}
                    except GeneratorExit:
                        # Client disconnected during error handling
                        logger.debug("Client disconnected during error handling")
                        return
                else:
                    raise
            with suppress(GeneratorExit):
                        await asyncio.sleep(0)

        except GeneratorExit:
            # Client disconnected - this is normal, don't log as error
            logger.debug("Client disconnected during initialization")
            return
        except Exception as e:
            logger.error(f"Error in streaming processing: {e}")
            try:
                yield {"type": "error", "content": str(e)}
            except GeneratorExit:
                # Client disconnected during error handling
                logger.debug("Client disconnected during error handling")
                return
        finally:
            # Ensure any cleanup is done
            if stream_started:
                logger.debug(f"Stream completed for thread {thread_id}")

                # CRITICAL FIX: After streaming completes, explicitly save the final state
                # The streaming method doesn't automatically persist the final state like ainvoke() does
                try:
                    # Get the current state after streaming to ensure all state properties are saved
                    current_state = await self.graph.aget_state(config)

                    if current_state and current_state.values:
                        state_values = current_state.values

                        # Log the state for debugging
                        logger.info(f"Final state after streaming for thread {thread_id}:")
                        logger.info(f"  - generated_queries: {'✓' if state_values.get('generated_queries') else '✗'} ({len(state_values.get('generated_queries', []))} queries)")
                        logger.info(f"  - retrieval_results: {'✓' if state_values.get('retrieval_results') else '✗'} ({len(state_values.get('retrieval_results', []))} results)")
                        logger.info(f"  - final_response: {'✓' if state_values.get('final_response') else '✗'} ({len(state_values.get('final_response', '')[:50])}...)")

                        # Explicitly update the state to ensure persistence
                        await self.graph.aupdate_state(config, state_values)
                        logger.info(f"Successfully persisted final state for thread {thread_id}")
                    else:
                        logger.warning(f"No state found to persist for thread {thread_id}")

                except Exception as persistence_error:
                    logger.error(f"Error persisting final state: {persistence_error}")
                    # Try alternative approach - get state from checkpointer
                    try:
                        async for checkpoint_tuple in self.checkpointer.alist(config, limit=1):
                            latest_checkpoint = checkpoint_tuple.checkpoint
                            channel_values = latest_checkpoint.get("channel_values", {})

                            logger.info(f"Fallback: State from checkpointer for thread {thread_id}:")
                            logger.info(f"  - generated_queries: {'✓' if channel_values.get('generated_queries') else '✗'}")
                            logger.info(f"  - retrieval_results: {'✓' if channel_values.get('retrieval_results') else '✗'}")
                            logger.info(f"  - final_response: {'✓' if channel_values.get('final_response') else '✗'}")
                            break
                    except Exception as fallback_error:
                        logger.error(f"Error in fallback state check: {fallback_error}")

    async def get_chat_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get chat history for a specific thread"""
        try:
            await self._ensure_initialized()

            config = {"configurable": {"thread_id": thread_id}}

            # Get the latest state for this thread
            latest_state = None
            async for checkpoint_tuple in self.checkpointer.alist(config, limit=1):
                latest_state = checkpoint_tuple
                break

            if not latest_state:
                return []

            # Extract messages from the latest checkpoint
            # CheckpointTuple has attributes: checkpoint, metadata, config, parent_config
            checkpoint_data = latest_state.checkpoint
            channel_values = checkpoint_data.get("channel_values", {})
            messages = channel_values.get("messages", [])

            # Format messages for response
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    formatted_messages.append({
                        "type": "human" if isinstance(msg, HumanMessage) else "ai",
                        "content": msg.content,
                        "timestamp": None  # LangGraph doesn't store timestamps in the same way
                    })

            return formatted_messages

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    async def cleanup(self):
        """Clean up resources"""
        await self._cleanup_checkpointer()
        self._is_initialized = False


# Global instance
langgraph_agent = LangGraphAgent()


async def initialize_global_agent():
    """Initialize the global agent instance"""
    await langgraph_agent.initialize()


async def cleanup_global_agent():
    """Cleanup the global agent instance"""
    await langgraph_agent.cleanup()


# Utility functions
async def process_with_langgraph(query: str, project_id: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to process query with LangGraph"""
    return await langgraph_agent.process_query(query, project_id, **kwargs)


async def process_with_langgraph_streaming(query: str, project_id: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
    """Convenience function to process query with LangGraph streaming"""
    try:
        async for chunk in langgraph_agent.process_query_streaming(query, project_id, **kwargs):
            yield chunk
    except GeneratorExit:
        # Client disconnected - this is normal, don't log as error
        logger.debug("Streaming generator closed by client")
        return
    except Exception as e:
        logger.error(f"Error in streaming wrapper: {e}")
        try:
            yield {"type": "error", "content": str(e)}
        except GeneratorExit:
            # Client disconnected during error handling
            logger.debug("Client disconnected during error handling")
            return


async def get_chat_history(thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get chat history for a thread"""
    return await langgraph_agent.get_chat_history(thread_id, limit)
