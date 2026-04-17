import argparse
import json
from pathlib import Path

from resume_tailor_agent.graph import build_graph
from resume_tailor_agent.utils.docx_resume import (
    convert_docx_to_pdf,
    parse_resume_docx_template,
    render_tailored_docx,
)
from resume_tailor_agent.utils.parsing import read_text, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic LangGraph resume-tailoring workflow."
    )
    parser.add_argument("--resume-file", help="Path to a UTF-8 text file containing the resume.")
    parser.add_argument("--resume-docx", help="Path to a DOCX resume template to use for formatting.")
    parser.add_argument("--jd-file", help="Path to a UTF-8 text file containing the job description.")
    parser.add_argument("--resume-text", help="Raw resume text.")
    parser.add_argument("--jd-text", help="Raw job description text.")
    parser.add_argument("--company-name", default="", help="Optional company name.")
    parser.add_argument("--role-title", default="", help="Optional role title.")
    parser.add_argument("--skills-section", default="", help="Optional existing skills section.")
    parser.add_argument("--graduation-details", default="", help="Optional graduation details.")
    parser.add_argument("--work-authorization", default="", help="Optional work authorization details.")
    parser.add_argument("--model", default="gpt-4.1", help="Chat model name to use.")
    parser.add_argument(
        "--thread-id",
        default="resume-tailor-local",
        help="Thread ID used by the LangGraph checkpointer.",
    )
    parser.add_argument("--output-docx", help="Optional path to write the tailored DOCX.")
    parser.add_argument("--output-pdf", help="Optional path to write the tailored PDF.")
    parser.add_argument("--output", help="Optional path to write final JSON output.")
    return parser


def resolve_input(args) -> tuple[str, str, dict]:
    template_data = {}
    resume_text = args.resume_text

    if args.resume_docx:
        template_data = parse_resume_docx_template(args.resume_docx)
        resume_text = resume_text or template_data["resume_text"]
    else:
        resume_text = resume_text or read_text(args.resume_file)

    jd_text = args.jd_text or read_text(args.jd_file)

    if not resume_text.strip():
        raise ValueError("Resume input is required. Provide --resume-text, --resume-file, or --resume-docx.")
    if not jd_text.strip():
        raise ValueError("Job description input is required. Provide --jd-text or --jd-file.")

    return resume_text, jd_text, template_data


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    resume_text, jd_text, template_data = resolve_input(args)

    graph = build_graph()
    initial_state = {
        "resume_text": resume_text,
        "job_description_text": jd_text,
        "company_name": args.company_name,
        "role_title": args.role_title,
        "current_skills_section": args.skills_section or template_data.get("skills_section", ""),
        "graduation_details": args.graduation_details,
        "work_authorization": args.work_authorization,
        "model_name": args.model,
        "existing_experience_bullets": template_data.get("experience_entries", []),
        "projects": template_data.get("project_entries", []),
    }

    result = graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": args.thread_id}},
    )

    payload = {
        "eligibility": result.get("eligibility", {}),
        "jd_terms": result.get("jd_terms", {}),
        "missing_keywords": result.get("missing_keywords", {}),
        "tailored_resume": result.get("final_output", {}),
        "validation": result.get("validation", {}),
    }

    generated_files = {}

    if args.resume_docx and args.output_docx:
        output_docx = str(Path(args.output_docx).expanduser())
        render_tailored_docx(
            template_path=args.resume_docx,
            output_path=output_docx,
            template_data=template_data,
            final_output=result.get("final_output", {}),
        )
        generated_files["docx"] = output_docx

        if args.output_pdf:
            output_pdf = str(Path(args.output_pdf).expanduser())
            generated_files["pdf"] = convert_docx_to_pdf(output_docx, output_pdf)
            generated_files["pdf"]["path"] = output_pdf

    if generated_files:
        payload["generated_files"] = generated_files

    if args.output:
        output_path = str(Path(args.output).expanduser())
        write_json(output_path, payload)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
