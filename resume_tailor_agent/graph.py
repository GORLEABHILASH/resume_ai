from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from resume_tailor_agent.nodes.add_keywords import add_keywords_node
from resume_tailor_agent.nodes.add_services import add_services_node
from resume_tailor_agent.nodes.add_tech_stack import add_tech_stack_node
from resume_tailor_agent.nodes.eligibility import eligibility_node
from resume_tailor_agent.nodes.final_assembler import final_assembler_node
from resume_tailor_agent.nodes.hiring_manager import hiring_manager_node
from resume_tailor_agent.nodes.jd_terms import jd_terms_node
from resume_tailor_agent.nodes.keyword_gap import keyword_gap_node
from resume_tailor_agent.nodes.skills_section import skills_section_node
from resume_tailor_agent.nodes.validate import validate_node
from resume_tailor_agent.state import ResumeTailorState


def build_graph():
    builder = StateGraph(ResumeTailorState)

    builder.add_node("jd_terms", jd_terms_node)
    builder.add_node("eligibility", eligibility_node)
    builder.add_node("keyword_gap", keyword_gap_node)
    builder.add_node("add_keywords", add_keywords_node)
    builder.add_node("hiring_manager", hiring_manager_node)
    builder.add_node("add_tech_stack", add_tech_stack_node)
    builder.add_node("add_services", add_services_node)
    builder.add_node("skills_section", skills_section_node)
    builder.add_node("final_assembler", final_assembler_node)
    builder.add_node("validate", validate_node)

    builder.add_edge(START, "jd_terms")
    builder.add_edge("jd_terms", "eligibility")
    builder.add_edge("eligibility", "keyword_gap")
    builder.add_edge("keyword_gap", "add_keywords")
    builder.add_edge("add_keywords", "hiring_manager")
    builder.add_edge("hiring_manager", "add_tech_stack")
    builder.add_edge("add_tech_stack", "add_services")
    builder.add_edge("add_services", "skills_section")
    builder.add_edge("skills_section", "final_assembler")
    builder.add_edge("final_assembler", "validate")
    builder.add_edge("validate", END)

    return builder.compile(checkpointer=InMemorySaver())
