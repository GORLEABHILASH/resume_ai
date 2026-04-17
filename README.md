# Resume Tailor Agent

A deterministic LangGraph pipeline for tailoring a software engineering resume to a job description.

## What it does

This project follows a fixed, stage-based flow:

1. Eligibility and role-fit analysis
2. JD keyword gap extraction
3. Keyword insertion into experience and project bullets
4. Hiring-manager optimization
5. Inline tech stack enhancement
6. JD-specific services/platform alignment
7. Skills section rewrite
8. Final assembly
9. Validation

It can also use an existing `.docx` resume as the formatting source, write tailored content back into that template, and export PDF when a supported converter is available.

The pipeline is resume-input agnostic. You can pass raw text directly or point it at `.txt` files containing resume and JD text.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
```

## Usage

Pass text files:

```bash
python app.py --resume-file sample_resume.txt --jd-file sample_jd.txt
```

Use an existing DOCX template and preserve its formatting:

```bash
python app.py \
  --resume-docx "/absolute/path/Resume Template.docx" \
  --jd-file sample_jd.txt \
  --output-docx tailored_resume.docx \
  --output-pdf tailored_resume.pdf
```

Pass raw text:

```bash
python app.py --resume-text "..." --jd-text "..."
```

Write output to a file:

```bash
python app.py --resume-file sample_resume.txt --jd-file sample_jd.txt --output result.json
```

Choose a model:

```bash
python app.py --resume-file sample_resume.txt --jd-file sample_jd.txt --model gpt-4.1
```

## Notes

- This version expects resume text and JD text as inputs, but `--resume-docx` can auto-extract the resume content from a DOCX template.
- PDF export is attempted via `soffice` or `libreoffice`, `docx2pdf`, or Microsoft Word on macOS if available.
- The graph uses an in-memory checkpointer for local runs.
