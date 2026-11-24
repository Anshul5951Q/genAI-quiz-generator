"""
AI-powered resume information extraction service.
Extracts structured candidate data from resume text using the configured LLM.
"""
import json
from typing import Any

from app.core.logging import logger
from app.services.llm_provider import BaseLLMProvider, LLMProviderError


RESUME_EXTRACTION_SYSTEM_PROMPT = """You are an expert resume parser and career analyst. 
Extract structured information from the resume text with high accuracy.
Output only valid JSON. Do not invent information not present in the resume.
If a field is not found, use null or an empty array."""

RESUME_EXTRACTION_PROMPT_TEMPLATE = """
Analyze the following resume text and extract all information into the specified JSON structure.

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"

Extract and return a JSON object with this exact structure:
{{
  "candidate_name": "Full name or null",
  "email": "Email address or null",
  "phone": "Phone number or null",
  "education": [
    {{
      "degree": "Degree name",
      "institution": "Institution name",
      "year": "Year or period",
      "field": "Field of study"
    }}
  ],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "duration": "Duration e.g. Jan 2022 - Dec 2023",
      "responsibilities": ["Key responsibility 1", "Key responsibility 2"]
    }}
  ],
  "internships": [
    {{
      "title": "Role",
      "company": "Company",
      "duration": "Duration"
    }}
  ],
  "technical_skills": ["skill1", "skill2"],
  "programming_languages": ["Python", "Java"],
  "frameworks": ["React", "FastAPI"],
  "databases": ["PostgreSQL", "MongoDB"],
  "tools": ["Git", "Docker"],
  "projects": [
    {{
      "title": "Project title",
      "description": "Brief description",
      "problem_statement": "What problem does it solve",
      "technologies": ["tech1", "tech2"],
      "architecture": "Architecture description if mentioned",
      "contribution": "Candidate's specific contribution",
      "key_features": ["feature1", "feature2"],
      "achievements": "Measurable achievements if any",
      "concepts": ["concept1", "concept2"]
    }}
  ],
  "certifications": ["Certification name and issuer"],
  "achievements": ["Achievement 1", "Achievement 2"],
  "soft_skills": ["Communication", "Leadership"]
}}

RULES:
- Extract ONLY information explicitly present in the resume text
- Do not invent technologies, achievements, or projects not mentioned
- For projects, extract as much technical detail as possible
- programming_languages and frameworks are subsets of technical_skills
- concepts should be technical concepts the project demonstrates (e.g. "REST API design", "database normalization")
"""


class ResumeExtractor:
    """
    Uses an LLM to extract structured information from resume text.
    Validates all outputs and handles malformed model responses gracefully.
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def extract(self, resume_text: str) -> dict[str, Any]:
        """
        Run AI extraction on resume text.
        Returns a validated structured dictionary.
        """
        # Truncate if too long (preserve first 12000 chars which covers most resumes)
        truncated_text = resume_text[:12000] if len(resume_text) > 12000 else resume_text

        prompt = RESUME_EXTRACTION_PROMPT_TEMPLATE.format(resume_text=truncated_text)

        for attempt in range(1, 3):
            try:
                raw_output = self.llm.generate(
                    prompt=prompt,
                    system_instruction=RESUME_EXTRACTION_SYSTEM_PROMPT,
                )
                data = self._parse_and_validate(raw_output)
                if data:
                    return data
            except LLMProviderError:
                raise
            except Exception as e:
                logger.warning(f"Resume extraction attempt {attempt} failed: {type(e).__name__}")
                if attempt == 2:
                    raise LLMProviderError(f"Failed to extract resume data: {e}")

        return self._empty_extraction()

    def _parse_and_validate(self, raw: str) -> dict[str, Any] | None:
        """Parse JSON output and validate required fields."""
        cleaned = raw.strip()
        # Strip markdown code blocks if present
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        import re
        try:
            data = json.loads(cleaned)
        except Exception:
            # Try regex extraction
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    return None
            else:
                return None

        if not isinstance(data, dict):
            return None

        # Normalize fields to expected types
        return self._normalize(data)

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ensure all fields are correct types, filling missing ones with defaults."""
        def as_list(v):
            if isinstance(v, list):
                return v
            if v is None:
                return []
            return [str(v)] if v else []

        def as_str(v):
            if isinstance(v, str):
                return v.strip() or None
            return None

        return {
            "candidate_name": as_str(data.get("candidate_name")),
            "email": as_str(data.get("email")),
            "phone": as_str(data.get("phone")),
            "education": as_list(data.get("education")),
            "experience": as_list(data.get("experience")),
            "internships": as_list(data.get("internships")),
            "technical_skills": as_list(data.get("technical_skills")),
            "programming_languages": as_list(data.get("programming_languages")),
            "frameworks": as_list(data.get("frameworks")),
            "databases": as_list(data.get("databases")),
            "tools": as_list(data.get("tools")),
            "projects": as_list(data.get("projects")),
            "certifications": as_list(data.get("certifications")),
            "achievements": as_list(data.get("achievements")),
            "soft_skills": as_list(data.get("soft_skills")),
        }

    @staticmethod
    def _empty_extraction() -> dict[str, Any]:
        return {
            "candidate_name": None, "email": None, "phone": None,
            "education": [], "experience": [], "internships": [],
            "technical_skills": [], "programming_languages": [], "frameworks": [],
            "databases": [], "tools": [], "projects": [],
            "certifications": [], "achievements": [], "soft_skills": [],
        }

    @staticmethod
    def compute_confidence(extracted: dict[str, Any]) -> float:
        """
        Estimate extraction confidence based on field completeness.
        Returns 0.0-1.0.
        """
        score = 0.0
        weights = {
            "candidate_name": 0.15,
            "email": 0.10,
            "technical_skills": 0.20,
            "projects": 0.25,
            "experience": 0.15,
            "education": 0.15,
        }
        for field, weight in weights.items():
            val = extracted.get(field)
            if val:
                score += weight
        return round(min(score, 1.0), 2)
