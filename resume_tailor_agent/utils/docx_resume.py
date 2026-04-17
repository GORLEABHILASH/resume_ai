import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def _paragraphs_from_docx(path: str) -> list[dict]:
    with ZipFile(path) as docx_zip:
        root = ET.fromstring(docx_zip.read("word/document.xml"))

    paragraphs = []
    for idx, para in enumerate(root.findall(".//w:p", NS)):
        text = "".join(node.text or "" for node in para.findall(".//w:t", NS)).strip()
        if text:
            paragraphs.append({"xml_index": idx, "text": text})
    return paragraphs


def _section_bounds(paragraphs: list[dict], start_heading: str, end_heading: Optional[str]) -> tuple[int, int]:
    start_idx = next(i for i, item in enumerate(paragraphs) if item["text"] == start_heading)
    if end_heading is None:
        return start_idx, len(paragraphs)
    end_idx = next(i for i, item in enumerate(paragraphs) if item["text"] == end_heading)
    return start_idx, end_idx


def _extract_section_lines(paragraphs: list[dict], start_heading: str, end_heading: Optional[str]) -> list[str]:
    start, end = _section_bounds(paragraphs, start_heading, end_heading)
    return [item["text"] for item in paragraphs[start + 3 : end]]


def _extract_plain_resume_text(paragraphs: list[dict]) -> str:
    return "\n".join(item["text"] for item in paragraphs)


def _parse_projects(paragraphs: list[dict]) -> list[dict]:
    _, end = _section_bounds(paragraphs, "Projects", "Work Experience")
    start = next(i for i, item in enumerate(paragraphs) if item["text"] == "Projects") + 3
    items = paragraphs[start:end]
    projects = []
    cursor = 0
    while cursor < len(items):
        title = items[cursor]["text"]
        bullets = []
        cursor += 1
        while cursor < len(items) and " | GitHub :" not in items[cursor]["text"]:
            bullets.append(items[cursor]["text"])
            cursor += 1
        projects.append({"name": title, "bullets": bullets})
    return projects


def _looks_like_role_line(text: str) -> bool:
    return bool(re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}", text))


def _parse_experience(paragraphs: list[dict]) -> list[dict]:
    _, end = _section_bounds(paragraphs, "Work Experience", "Education")
    start = next(i for i, item in enumerate(paragraphs) if item["text"] == "Work Experience") + 3
    items = paragraphs[start:end]
    experience = []
    cursor = 0
    while cursor < len(items):
        role_line = items[cursor]["text"]
        if not _looks_like_role_line(role_line):
            cursor += 1
            continue
        company_line = items[cursor + 1]["text"] if cursor + 1 < len(items) else ""
        bullets = []
        cursor += 2
        while cursor < len(items) and not _looks_like_role_line(items[cursor]["text"]):
            bullets.append(items[cursor]["text"])
            cursor += 1
        experience.append({"company": company_line, "role": role_line, "bullets": bullets})
    return experience


def parse_resume_docx_template(path: str) -> dict:
    paragraphs = _paragraphs_from_docx(path)
    skills_section = "\n".join(_extract_section_lines(paragraphs, "Technical Skills", "Projects"))
    summary_idx = next(i for i, item in enumerate(paragraphs) if item["text"] == "Profile Summary") + 3

    return {
        "resume_text": _extract_plain_resume_text(paragraphs),
        "paragraphs": paragraphs,
        "summary": paragraphs[summary_idx]["text"],
        "skills_section": skills_section,
        "project_entries": _parse_projects(paragraphs),
        "experience_entries": _parse_experience(paragraphs),
        "education_lines": _extract_section_lines(paragraphs, "Education", "Certifications"),
        "certification_lines": _extract_section_lines(paragraphs, "Certifications", None),
    }


def _set_paragraph_text(paragraph_element: ET.Element, text: str) -> None:
    text_nodes = paragraph_element.findall(".//w:t", NS)
    if not text_nodes:
        run = ET.SubElement(paragraph_element, f"{{{W_NS}}}r")
        text_node = ET.SubElement(run, f"{{{W_NS}}}t")
        text_node.text = text
        return

    text_nodes[0].text = text
    for node in text_nodes[1:]:
        node.text = ""


def _clone_run_with_text(run_template: ET.Element, text: str) -> ET.Element:
    new_run = deepcopy(run_template)
    text_nodes = new_run.findall(".//w:t", NS)
    if not text_nodes:
        text_node = ET.SubElement(new_run, f"{{{W_NS}}}t")
        text_nodes = [text_node]

    text_nodes[0].text = text
    if text.startswith(" ") or text.endswith(" "):
        text_nodes[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    elif "{http://www.w3.org/XML/1998/namespace}space" in text_nodes[0].attrib:
        del text_nodes[0].attrib["{http://www.w3.org/XML/1998/namespace}space"]

    for node in text_nodes[1:]:
        parent = new_run.find(".//w:t/..", NS)
        if parent is not None and node in list(parent):
            parent.remove(node)
    return new_run


def _pick_run_templates(paragraph_element: ET.Element) -> tuple[Optional[ET.Element], Optional[ET.Element]]:
    runs = paragraph_element.findall("w:r", NS)
    bold_template = None
    plain_template = None
    for run in runs:
        is_bold = run.find("w:rPr/w:b", NS) is not None
        if is_bold and bold_template is None:
            bold_template = run
        if not is_bold and plain_template is None:
            plain_template = run
    if bold_template is None and runs:
        bold_template = runs[0]
    if plain_template is None and runs:
        plain_template = runs[-1]
    return bold_template, plain_template


def _replace_runs(paragraph_element: ET.Element, segments: list[tuple[str, bool]]) -> None:
    bold_template, plain_template = _pick_run_templates(paragraph_element)
    if bold_template is None and plain_template is None:
        _set_paragraph_text(paragraph_element, "".join(text for text, _ in segments))
        return

    for run in list(paragraph_element.findall("w:r", NS)):
        paragraph_element.remove(run)

    for text, is_bold in segments:
        if not text:
            continue
        template = bold_template if is_bold else plain_template
        if template is None:
            template = bold_template or plain_template
        paragraph_element.append(_clone_run_with_text(template, text))


def _set_skills_paragraph_text(paragraph_element: ET.Element, text: str) -> None:
    if ":" not in text:
        _set_paragraph_text(paragraph_element, text)
        return
    heading, remainder = text.split(":", 1)
    segments = [(f"{heading}:", True)]
    if remainder:
        segments.append((remainder if remainder.startswith(" ") else f" {remainder}", False))
    _replace_runs(paragraph_element, segments)


def _keyword_candidates(final_output: dict) -> list[str]:
    base_terms = set(final_output.get("covered_keywords", []))
    for line in final_output.get("tailored_skills_section", "").splitlines():
        if ":" in line:
            _, values = line.split(":", 1)
            for item in values.split(","):
                cleaned = item.strip()
                if len(cleaned) >= 3:
                    base_terms.add(cleaned)

    base_terms.update(
        {
            "distributed services",
            "AWS scale",
            "data operations",
            "system architecture",
            "code reviews",
            "reliability",
            "scaling",
            "testing",
            "deployment",
            "launch",
            "performance",
            "availability",
            "durability",
            "FastAPI",
            "Supabase Postgres",
            "AWS Textract",
            "OpenAI APIs",
            "React",
            "Supabase Auth",
            "RBAC",
            "Django REST APIs",
            "Vue.js",
            "PostgreSQL",
            "Pandas",
            "Node.js",
            "Express",
            "HTTP/HTTPS",
            "AWS Lambda",
            "API Gateway",
            "Cognito",
            "AWS CloudWatch",
            "AWS X-Ray",
            "microservices",
            "AWS-based microservices",
            "EC2",
            "S3",
            "Glue",
            "Redshift",
            "Amazon RDS",
            "DynamoDB",
            "IAM",
            "Kinesis",
            "Terraform",
            "CI/CD",
            "RabbitMQ",
            "Elasticsearch",
            "Docker",
            "Kubernetes",
            "Neo4j",
            "LangChain",
            "Python",
            "Go",
            "Java",
            "REST APIs",
        }
    )
    return sorted(base_terms, key=len, reverse=True)


def _set_bullet_paragraph_text(paragraph_element: ET.Element, text: str, keywords: list[str]) -> None:
    normalized_text = text
    spans = []
    lowered = normalized_text.lower()
    for keyword in keywords:
        start = 0
        keyword_lower = keyword.lower()
        while True:
            idx = lowered.find(keyword_lower, start)
            if idx == -1:
                break
            before_ok = idx == 0 or not lowered[idx - 1].isalnum()
            end_idx = idx + len(keyword)
            after_ok = end_idx == len(lowered) or not lowered[end_idx].isalnum()
            if before_ok and after_ok:
                spans.append((idx, end_idx))
            start = idx + len(keyword)

    spans.sort()
    merged = []
    for start, end in spans:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    if not merged:
        _set_paragraph_text(paragraph_element, text)
        return

    segments = []
    cursor = 0
    for start, end in merged:
        if start > cursor:
            segments.append((normalized_text[cursor:start], False))
        segments.append((normalized_text[start:end], True))
        cursor = end
    if cursor < len(normalized_text):
        segments.append((normalized_text[cursor:], False))
    _replace_runs(paragraph_element, segments)


def _fit_lines_to_count(lines: list[str], target_count: int, fallback_lines: list[str]) -> list[str]:
    cleaned = [line.strip() for line in lines if line and line.strip()]
    if target_count <= 0:
        return []
    if not cleaned:
        return fallback_lines[:target_count]
    if len(cleaned) == target_count:
        return cleaned
    if len(cleaned) < target_count:
        return (cleaned + fallback_lines[len(cleaned) : target_count])[:target_count]

    return cleaned[: target_count - 1] + [" ".join(cleaned[target_count - 1 :])]


def _extract_title_prefix(title_line: str) -> str:
    return title_line.split("| GitHub :")[0].strip()


def _match_project(source_project: dict, tailored_projects: list[dict]) -> Optional[dict]:
    source_prefix = _extract_title_prefix(source_project["name"]).lower()
    for project in tailored_projects:
        if source_prefix and source_prefix in project.get("name", "").lower():
            return project
    return None


def _extract_role_prefix(role_line: str) -> str:
    match = re.match(r"^(.*?)(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}", role_line)
    return match.group(1).strip() if match else role_line.strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def _company_name_only(company_line: str) -> str:
    return _normalize_text(re.split(r"\s{2,}", company_line.strip())[0])


def _match_experience(source_entry: dict, tailored_experience: list[dict]) -> Optional[dict]:
    source_role = _normalize_text(_extract_role_prefix(source_entry["role"]))
    source_company = _company_name_only(source_entry["company"]) if source_entry["company"] else ""

    exact_matches = []
    partial_matches = []

    for entry in tailored_experience:
        role = _normalize_text(_extract_role_prefix(entry.get("role", "")))
        company = _company_name_only(entry.get("company", "")) if entry.get("company") else ""

        if source_role and source_company and role == source_role and company == source_company:
            exact_matches.append(entry)
        elif (source_company and company == source_company) or (source_role and role == source_role):
            partial_matches.append(entry)

    if exact_matches:
        return exact_matches[0]
    if partial_matches:
        return partial_matches[0]

    for entry in tailored_experience:
        role = _normalize_text(_extract_role_prefix(entry.get("role", "")))
        company = _company_name_only(entry.get("company", "")) if entry.get("company") else ""
        if source_company and source_company in company:
            return entry
        if source_role and source_role in role:
            return entry

    return None


def _paragraph_index_lookup(paragraphs: list[dict]) -> dict[str, int]:
    return {item["text"]: item["xml_index"] for item in paragraphs}


def render_tailored_docx(
    template_path: str,
    output_path: str,
    template_data: dict,
    final_output: dict,
) -> None:
    template = Path(template_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, output)

    paragraphs = template_data["paragraphs"]
    index_by_text = _paragraph_index_lookup(paragraphs)
    tailored_projects = final_output.get("tailored_projects", [])
    tailored_experience = final_output.get("tailored_experience", [])
    tailored_summary = final_output.get("tailored_summary", "").strip() or template_data.get("summary", "")
    highlight_keywords = _keyword_candidates(final_output)

    original_skill_lines = template_data.get("skills_section", "").splitlines()
    skill_lines = _fit_lines_to_count(
        final_output.get("tailored_skills_section", "").splitlines(),
        len(original_skill_lines),
        original_skill_lines,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        with ZipFile(output, "r") as source_zip:
            source_zip.extractall(tmpdir)

        document_path = Path(tmpdir) / "word" / "document.xml"
        root = ET.parse(document_path).getroot()
        xml_paragraphs = root.findall(".//w:p", NS)

        summary_anchor = index_by_text.get(template_data["summary"])
        if summary_anchor is not None:
            _set_paragraph_text(xml_paragraphs[summary_anchor], tailored_summary)

        for source_line, new_line in zip(original_skill_lines, skill_lines):
            para_idx = index_by_text.get(source_line)
            if para_idx is not None:
                _set_skills_paragraph_text(xml_paragraphs[para_idx], new_line)

        for project in template_data.get("project_entries", []):
            matched = _match_project(project, tailored_projects) or project
            new_bullets = _fit_lines_to_count(matched.get("bullets", []), len(project["bullets"]), project["bullets"])
            for source_bullet, new_bullet in zip(project["bullets"], new_bullets):
                para_idx = index_by_text.get(source_bullet)
                if para_idx is not None:
                    _set_bullet_paragraph_text(xml_paragraphs[para_idx], new_bullet, highlight_keywords)

        for entry in template_data.get("experience_entries", []):
            matched = _match_experience(entry, tailored_experience) or entry
            new_bullets = _fit_lines_to_count(matched.get("bullets", []), len(entry["bullets"]), entry["bullets"])
            for source_bullet, new_bullet in zip(entry["bullets"], new_bullets):
                para_idx = index_by_text.get(source_bullet)
                if para_idx is not None:
                    _set_bullet_paragraph_text(xml_paragraphs[para_idx], new_bullet, highlight_keywords)

        ET.register_namespace("w", W_NS)
        ET.ElementTree(root).write(document_path, encoding="utf-8", xml_declaration=True)

        with ZipFile(output, "w", ZIP_DEFLATED) as target_zip:
            for file_path in Path(tmpdir).rglob("*"):
                if file_path.is_file():
                    target_zip.write(file_path, file_path.relative_to(tmpdir))


def _run_command(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def convert_docx_to_pdf(docx_path: str, output_pdf_path: str) -> dict:
    docx = Path(docx_path).expanduser().resolve()
    target_pdf = Path(output_pdf_path).expanduser().resolve()
    target_pdf.parent.mkdir(parents=True, exist_ok=True)

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_command(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, str(docx)]
            )
            generated = Path(tmpdir) / f"{docx.stem}.pdf"
            if result.returncode == 0 and generated.exists():
                shutil.copyfile(generated, target_pdf)
                return {
                    "success": True,
                    "method": "libreoffice",
                    "message": "PDF exported with LibreOffice-compatible converter.",
                }

    if shutil.which("python3"):
        result = _run_command(["python3", "-m", "docx2pdf", str(docx), str(target_pdf)])
        if result.returncode == 0 and target_pdf.exists():
            return {
                "success": True,
                "method": "docx2pdf",
                "message": "PDF exported with docx2pdf.",
            }

    if os.uname().sysname == "Darwin":
        applescript = (
            f'tell application "Microsoft Word"\n'
            f'open POSIX file "{docx}"\n'
            f'set activeDocument to active document\n'
            f'save as activeDocument file name POSIX file "{target_pdf}" file format format PDF\n'
            f'close activeDocument saving no\n'
            f'end tell\n'
        )
        result = _run_command(["osascript", "-e", applescript])
        if result.returncode == 0 and target_pdf.exists():
            return {
                "success": True,
                "method": "microsoft_word",
                "message": "PDF exported with Microsoft Word.",
            }

    return {
        "success": False,
        "method": "unavailable",
        "message": (
            "No supported DOCX-to-PDF converter was available. "
            "Install LibreOffice, docx2pdf, or Microsoft Word to enable PDF export."
        ),
    }
