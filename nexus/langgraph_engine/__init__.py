"""
langgraph_engine — Layer 4: V1 Pipeline LangGraph Engine

Public API:
    state:       GovernanceState
    pipeline:    compile(), run_workitem(), get_pipeline()
    graph:       build_graph()
    nodes:       register_node(), get_node()
    agent:       RoleShapedAgent, make_agent_for_stage, AgentStatus
    executor:    AgentExecutor
"""

from nexus.langgraph_engine.state import GovernanceState
from nexus.langgraph_engine.pipeline import compile, run_workitem, get_pipeline
from nexus.langgraph_engine.graph import build_graph
from nexus.langgraph_engine.runtime import init_runtime, get_runtime
from nexus.langgraph_engine.nodes import register_node, get_node, NODE_REGISTRY
from nexus.langgraph_engine.agent import (
    RoleShapedAgent,
    make_agent_for_stage,
    make_viper_ba,
    make_viper_sa,
    make_viper_dev,
    make_viper_qa,
    AgentStatus,
)
from nexus.langgraph_engine.executor import AgentExecutor

__all__ = [
    "GovernanceState",
    "compile",
    "run_workitem",
    "get_pipeline",
    "init_runtime",
    "get_runtime",
    "build_graph",
    "register_node",
    "get_node",
    "NODE_REGISTRY",
    # Agent
    "RoleShapedAgent",
    "make_agent_for_stage",
    "make_viper_ba",
    "make_viper_sa",
    "make_viper_dev",
    "make_viper_qa",
    "AgentStatus",
    # Executor
    "AgentExecutor",
]
