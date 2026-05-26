"""LangGraph Workflow for the Runtime Agent.

This module defines the StateGraph workflow that orchestrates
the agent nodes.
"""

from typing import Literal, Any, Dict
from langgraph.graph import StateGraph, END

from agents.graph.state import AgentState, create_initial_state
from agents.nodes.intent.intent_node import intent_node
from agents.nodes.planner.goal_planner_node import goal_planner_node
from agents.nodes.runtime.think_node import think_node
from agents.nodes.runtime.observe_node import observe_node
from agents.nodes.runtime.retry_node import retry_node
from agents.nodes.runtime.rag_node import runtime_rag_node
from agents.nodes.runtime.finalize_node import finalize_node
from agents.nodes.skill.skill_selector_node import skill_selector_node
from agents.nodes.skill.skill_runtime_node import skill_runtime_node


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow.

    Returns:
        StateGraph instance.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent", intent_node)
    workflow.add_node("planner", goal_planner_node)
    workflow.add_node("think", think_node)
    workflow.add_node("skill_selector", skill_selector_node)
    workflow.add_node("skill_runtime", skill_runtime_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("runtime_rag", runtime_rag_node)
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("intent")

    # Add edges
    workflow.add_edge("intent", "planner")

    # Conditional routing after planner
    def route_after_planner(state: AgentState) -> Literal["finalize", "think"]:
        """Route based on execution intent."""
        if state["execution_intent"] == "KNOWLEDGE_ONLY":
            return "finalize"
        return "think"

    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "finalize": "finalize",
            "think": "think",
        }
    )

    workflow.add_edge("think", "skill_selector")
    workflow.add_edge("skill_selector", "skill_runtime")
    workflow.add_edge("skill_runtime", "observe")

    # Conditional routing after observe - four-way routing
    def route_after_observe(state: AgentState) -> Literal["retry", "runtime_rag", "finalize", "think"]:
        """Route based on observation results.

        Routes:
        - finished → finalize
        - need_rag → runtime_rag (query knowledge base for SW explanation)
        - need_retry → retry
        - otherwise → think (continue)
        """
        if state["finished"]:
            return "finalize"

        if state.get("need_rag"):
            return "runtime_rag"

        if state.get("need_retry"):
            return "retry"

        return "think"

    workflow.add_conditional_edges(
        "observe",
        route_after_observe,
        {
            "retry": "retry",
            "runtime_rag": "runtime_rag",
            "finalize": "finalize",
            "think": "think",
        }
    )

    workflow.add_edge("retry", "think")
    workflow.add_edge("runtime_rag", "think")  # RAG provides context, then continue thinking
    workflow.add_edge("finalize", END)

    return workflow


def compile_workflow() -> Any:
    """Compile the workflow into an executable graph.

    Returns:
        Compiled LangGraph.
    """
    workflow = create_workflow()
    return workflow.compile()


# Global compiled graph
_graph = None


def get_graph() -> Any:
    """Get the compiled workflow graph.

    Returns:
        Compiled LangGraph instance.
    """
    global _graph
    if _graph is None:
        _graph = compile_workflow()
    return _graph


def run_agent(user_input: str) -> Dict[str, Any]:
    """Run the agent with user input.

    Args:
        user_input: User request text

    Returns:
        Final agent state with response.
    """
    graph = get_graph()
    initial_state = create_initial_state(user_input)

    result = graph.invoke(initial_state)

    return result


async def run_agent_async(user_input: str) -> Dict[str, Any]:
    """Run the agent asynchronously.

    Args:
        user_input: User request text

    Returns:
        Final agent state.
    """
    graph = get_graph()
    initial_state = create_initial_state(user_input)

    result = await graph.ainvoke(initial_state)

    return result


class AgentRunner:
    """Runner for executing the agent workflow.

    Provides methods to run the agent with various configurations.
    """

    def __init__(self):
        """Initialize agent runner."""
        self.graph = compile_workflow()

    def run(self, user_input: str) -> Dict[str, Any]:
        """Run agent synchronously.

        Args:
            user_input: User input

        Returns:
            Result dictionary.
        """
        initial_state = create_initial_state(user_input)
        return self.graph.invoke(initial_state)

    async def run_async(self, user_input: str) -> Dict[str, Any]:
        """Run agent asynchronously.

        Args:
            user_input: User input

        Returns:
            Result dictionary.
        """
        initial_state = create_initial_state(user_input)
        return await self.graph.ainvoke(initial_state)

    def stream(self, user_input: str) -> Any:
        """Stream agent execution.

        Args:
            user_input: User input

        Returns:
            Stream of state updates.
        """
        initial_state = create_initial_state(user_input)
        return self.graph.stream(initial_state)