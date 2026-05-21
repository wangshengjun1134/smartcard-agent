"""Tests for LangGraph workflow."""

import pytest
from agents.graph.state import AgentState, create_initial_state
from agents.nodes.intent.intent_node import intent_node, classify_intent
from agents.nodes.planner.goal_planner_node import goal_planner_node, determine_goal


class TestAgentState:
    """Tests for agent state."""

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state("读取 IMSI")

        assert state["user_input"] == "读取 IMSI"
        assert state["execution_intent"] == ""
        assert state["current_goal"] == ""
        assert state["finished"] == False
        assert state["observations"] == []

    def test_state_structure(self):
        """Test state structure."""
        state: AgentState = {
            "user_input": "test",
            "execution_intent": "KNOWLEDGE_ONLY",
            "current_goal": "knowledge_query",
            "next_action": {},
            "selected_skill": "",
            "skill_params": {},
            "observations": [],
            "runtime_state": {},
            "rag_context": [],
            "need_rag": False,
            "need_retry": False,
            "retry_count": 0,
            "final_response": "",
            "finished": True,
            "error": None,
        }

        assert state["execution_intent"] == "KNOWLEDGE_ONLY"
        assert state["finished"] == True


class TestIntentNode:
    """Tests for intent node."""

    def test_classify_intent_knowledge(self):
        """Test knowledge intent classification."""
        intent = classify_intent("什么是 IMSI")
        assert intent == "KNOWLEDGE_ONLY"

    def test_classify_intent_card(self):
        """Test card intent classification."""
        intent = classify_intent("读取 IMSI")
        assert intent == "REQUIRES_CARD"

    def test_classify_intent_apdu(self):
        """Test APDU intent classification."""
        intent = classify_intent("发送 SELECT APDU")
        assert intent == "REQUIRES_APDU"

    def test_intent_node(self):
        """Test intent node execution."""
        state = create_initial_state("读取 IMSI")
        result = intent_node(state)

        assert result["execution_intent"] == "REQUIRES_CARD"


class TestGoalPlanner:
    """Tests for goal planner node."""

    def test_determine_goal_imsi(self):
        """Test IMSI goal determination."""
        goal = determine_goal("读取 IMSI")
        assert goal == "read_imsi"

    def test_determine_goal_iccid(self):
        """Test ICCID goal determination."""
        goal = determine_goal("读取 ICCID")
        assert goal == "read_iccid"

    def test_determine_goal_discover(self):
        """Test discover goal determination."""
        goal = determine_goal("探测卡片类型")
        assert goal == "discover_card"

    def test_goal_planner_node(self):
        """Test goal planner execution."""
        state: AgentState = {
            "user_input": "读取 IMSI",
            "execution_intent": "REQUIRES_CARD",
            "current_goal": "",
            "next_action": {},
            "selected_skill": "",
            "skill_params": {},
            "observations": [],
            "runtime_state": {},
            "rag_context": [],
            "need_rag": False,
            "need_retry": False,
            "retry_count": 0,
            "final_response": "",
            "finished": False,
            "error": None,
        }

        result = goal_planner_node(state)
        assert result["current_goal"] == "read_imsi"

    def test_goal_planner_knowledge(self):
        """Test goal planner for knowledge."""
        state: AgentState = {
            "user_input": "什么是 IMSI",
            "execution_intent": "KNOWLEDGE_ONLY",
            "current_goal": "",
            "next_action": {},
            "selected_skill": "",
            "skill_params": {},
            "observations": [],
            "runtime_state": {},
            "rag_context": [],
            "need_rag": False,
            "need_retry": False,
            "retry_count": 0,
            "final_response": "",
            "finished": False,
            "error": None,
        }

        result = goal_planner_node(state)
        assert result["current_goal"] == "knowledge_query"


class TestWorkflowCreation:
    """Tests for workflow creation."""

    def test_create_workflow(self):
        """Test workflow creation."""
        from agents.graph.workflow import create_workflow

        workflow = create_workflow()

        # Check nodes exist
        assert "intent" in workflow.nodes
        assert "planner" in workflow.nodes
        assert "think" in workflow.nodes
        assert "finalize" in workflow.nodes

    def test_compile_workflow(self):
        """Test workflow compilation."""
        from agents.graph.workflow import compile_workflow

        graph = compile_workflow()
        assert graph is not None


class TestRuntimeState:
    """Tests for runtime state."""

    def test_runtime_context(self):
        """Test runtime context."""
        from runtime.context import RuntimeContext

        ctx = RuntimeContext()
        ctx.connect("Mock Reader", bytes.fromhex("3B9F96801F"))

        assert ctx.connected == True
        assert ctx.current_reader == "Mock Reader"
        assert ctx.selected_path == ["3F00"]

    def test_runtime_context_select(self):
        """Test runtime context select."""
        from runtime.context import RuntimeContext

        ctx = RuntimeContext()
        ctx.connect("Reader", bytes.fromhex("3B"))
        ctx.select_file("7F20")

        assert ctx.selected_path == ["3F00", "7F20"]

    def test_checkpoint_manager(self):
        """Test checkpoint manager."""
        from runtime.checkpoint import CheckpointManager
        from runtime.context import RuntimeContext

        manager = CheckpointManager()
        ctx = RuntimeContext()
        ctx.connect("Reader", bytes.fromhex("3B"))

        checkpoint = manager.save_checkpoint(ctx, "test_checkpoint")
        assert checkpoint.id.startswith("cp_")

        # Restore
        new_ctx = RuntimeContext()
        manager.restore_checkpoint(new_ctx, checkpoint.id)
        assert new_ctx.connected == True