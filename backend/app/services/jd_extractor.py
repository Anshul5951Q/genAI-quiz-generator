"""
Job Description extraction and Resume-JD matching service.
"""
import json
import re
from typing import Any

from app.core.logging import logger
from app.services.llm_provider import BaseLLMProvider, LLMProviderError


JD_EXTRACTION_SYSTEM = """You are an expert HR analyst and job requirements specialist.
Extract structured requirements from job descriptions with high accuracy.
Output only valid JSON. Never invent requirements not present in the text."""

JD_EXTRACTION_TEMPLATE = """
Analyze the following job description and extract all requirements.

JOB DESCRIPTION:
\"\"\"
{jd_text}
\"\"\"

Return a JSON object with this exact structure:
{{
  "job_title": "Title of the position",
  "company": "Company name or null",
  "experience_min_years": null_or_integer,
  "experience_max_years": null_or_integer,
  "education_requirement": "Education requirement or null",
  "required_skills": ["Skill 1", "Skill 2"],
  "preferred_skills": ["Preferred skill 1"],
  "technical_requirements": ["Technical requirement 1"],
  "responsibilities": ["Responsibility 1", "Responsibility 2"],
  "domain_knowledge": ["Domain area 1"],
  "soft_skills": ["Communication", "Teamwork"],
  "requirements_list": [
    {{
      "text": "Requirement text",
      "category": "technical|experience|education|soft|preferred",
      "is_required": true_or_false
    }}
  ]
}}

RULES:
- Extract ONLY information present in the JD text
- Classify each requirement as: technical, experience, education, soft, or preferred
- is_required=true for mandatory requirements, false for preferred/nice-to-have
"""

MATCHING_SYSTEM = """You are an expert career counselor analyzing resume-job compatibility.
Compare the resume profile against job requirements accurately and objectively.
Output only valid JSON."""

MATCHING_TEMPLATE = """
Compare this candidate profile against the job requirements and generate a compatibility analysis.

CANDIDATE PROFILE:
{candidate_profile}

JOB REQUIREMENTS:
{job_requirements}

Return a JSON object:
{{
  "compatibility_score": 0_to_100_integer,
  "matching_skills": [
    {{"skill": "Python", "evidence": "Listed in resume technical skills", "strength": "strong"}}
  ],
  "missing_skills": [
    {{"skill": "Kubernetes", "importance": "required"}}
  ],
  "partial_matches": [
    {{"requirement": "3+ years experience", "evidence": "2 years from resume", "gap": "1 year short"}}
  ],
  "weak_areas": ["Area 1", "Area 2"],
  "strengths": ["Strong in Python", "Good project portfolio"],
  "recommendations": ["Learn Docker", "Get AWS certification"],
  "interview_focus": ["Database design", "System architecture", "Python proficiency"]
}}

RULES:
- Score 0-100 based on how well the candidate meets requirements
- Strong evidence = skill explicitly mentioned in resume with context
- Partial evidence = skill implied but not explicitly stated
- Missing = no evidence of the skill at all
- Do NOT inflate the score. Be objective.
"""


class JDExtractor:
    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def extract(self, jd_text: str) -> dict[str, Any]:
        truncated = jd_text[:10000] if len(jd_text) > 10000 else jd_text
        prompt = JD_EXTRACTION_TEMPLATE.format(jd_text=truncated)

        for attempt in range(1, 3):
            try:
                raw = self.llm.generate(prompt=prompt, system_instruction=JD_EXTRACTION_SYSTEM)
                data = self._parse(raw)
                if data:
                    return self._normalize(data)
            except LLMProviderError:
                raise
            except Exception as e:
                logger.warning(f"JD extraction attempt {attempt} failed: {e}")

        return self._empty()

    def _parse(self, raw: str) -> dict | None:
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
            return None

    def _normalize(self, data: dict) -> dict:
        def as_list(v):
            return v if isinstance(v, list) else []
        def as_int(v):
            try:
                return int(v) if v is not None else None
            except Exception:
                return None

        return {
            "job_title": data.get("job_title") or "",
            "company": data.get("company"),
            "experience_min_years": as_int(data.get("experience_min_years")),
            "experience_max_years": as_int(data.get("experience_max_years")),
            "education_requirement": data.get("education_requirement"),
            "required_skills": as_list(data.get("required_skills")),
            "preferred_skills": as_list(data.get("preferred_skills")),
            "technical_requirements": as_list(data.get("technical_requirements")),
            "responsibilities": as_list(data.get("responsibilities")),
            "domain_knowledge": as_list(data.get("domain_knowledge")),
            "soft_skills": as_list(data.get("soft_skills")),
            "requirements_list": as_list(data.get("requirements_list")),
        }

    @staticmethod
    def _empty() -> dict:
        return {
            "job_title": "", "company": None,
            "experience_min_years": None, "experience_max_years": None,
            "education_requirement": None,
            "required_skills": [], "preferred_skills": [], "technical_requirements": [],
            "responsibilities": [], "domain_knowledge": [], "soft_skills": [],
            "requirements_list": [],
        }


class MatchingService:
    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def analyze(
        self,
        resume_extraction: dict[str, Any],
        jd_extraction: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a comprehensive resume-JD compatibility report."""
        # Build candidate profile summary
        candidate_profile = json.dumps({
            "name": resume_extraction.get("candidate_name"),
            "technical_skills": resume_extraction.get("technical_skills", []),
            "programming_languages": resume_extraction.get("programming_languages", []),
            "frameworks": resume_extraction.get("frameworks", []),
            "databases": resume_extraction.get("databases", []),
            "tools": resume_extraction.get("tools", []),
            "experience_count": len(resume_extraction.get("experience", [])),
            "projects": [
                {"title": p.get("title"), "technologies": p.get("technologies", [])}
                for p in resume_extraction.get("projects", [])[:5]
            ],
            "certifications": resume_extraction.get("certifications", []),
        }, indent=2)

        job_requirements = json.dumps({
            "required_skills": jd_extraction.get("required_skills", []),
            "preferred_skills": jd_extraction.get("preferred_skills", []),
            "experience_required": f"{jd_extraction.get('experience_min_years', 0)}-{jd_extraction.get('experience_max_years', 'any')} years",
            "technical_requirements": jd_extraction.get("technical_requirements", []),
            "domain_knowledge": jd_extraction.get("domain_knowledge", []),
        }, indent=2)

        prompt = MATCHING_TEMPLATE.format(
            candidate_profile=candidate_profile,
            job_requirements=job_requirements,
        )

        try:
            raw = self.llm.generate(prompt=prompt, system_instruction=MATCHING_SYSTEM)
            data = self._parse(raw)
            if data:
                return self._normalize_match(data)
        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"Matching analysis failed: {e}")

        return {
            "compatibility_score": 0.0,
            "matching_skills": [], "missing_skills": [], "partial_matches": [],
            "weak_areas": [], "strengths": [], "recommendations": [],
            "interview_focus": [],
        }

    def _parse(self, raw: str) -> dict | None:
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
            return None

    def _normalize_match(self, data: dict) -> dict:
        def as_list(v):
            return v if isinstance(v, list) else []

        score = data.get("compatibility_score", 0)
        try:
            score = float(score)
            score = max(0.0, min(100.0, score))
        except Exception:
            score = 0.0

        return {
            "compatibility_score": score,
            "matching_skills": as_list(data.get("matching_skills")),
            "missing_skills": as_list(data.get("missing_skills")),
            "partial_matches": as_list(data.get("partial_matches")),
            "weak_areas": as_list(data.get("weak_areas")),
            "strengths": as_list(data.get("strengths")),
            "recommendations": as_list(data.get("recommendations")),
            "interview_focus": as_list(data.get("interview_focus")),
        }
