import json
from typing import Any

from app.core.logging import logger
from app.models.quiz import QuizModel


class GoogleFormsService:
    """
    Groundwork for Google Forms API integration.
    Converts approved StudySet multiple-choice quizzes into Google Forms REST API JSON payload structures.
    Complies with Google Forms API v1 specifications:
    https://developers.google.com/forms/api/reference/rest/v1/forms
    """

    @staticmethod
    def build_google_form_payload(quiz: QuizModel) -> dict[str, Any]:
        """
        Builds the complete JSON payload conforming to Google Forms API v1.
        Includes title, description, and batchUpdate requests with CreateItemRequest
        containing choiceQuestion items and correct answer grading.
        """
        requests = []

        for idx, q in enumerate(sorted(quiz.questions, key=lambda x: x.order_index)):
            correct_opt = next((o for o in q.options if o.is_correct), None)
            correct_text = correct_opt.option_text if correct_opt else ""

            options_payload = []
            for o in sorted(q.options, key=lambda x: x.option_letter):
                options_payload.append({
                    "value": f"{o.option_letter}. {o.option_text}",
                })

            item_request = {
                "createItem": {
                    "item": {
                        "title": f"Q{idx + 1}. {q.question_text}",
                        "description": f"Topic: {q.topic} | Difficulty: {q.difficulty.title()}",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "grading": {
                                    "pointValue": 1,
                                    "correctAnswers": {
                                        "answers": [
                                            {"value": f"{correct_opt.option_letter}. {correct_text}"}
                                        ] if correct_opt else []
                                    },
                                    "generalFeedback": {
                                        "text": f"Explanation: {q.explanation}\nEvidence: \"{q.evidence}\""
                                    },
                                },
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": options_payload,
                                    "shuffle": False,
                                },
                            }
                        },
                    },
                    "location": {"index": idx},
                }
            }
            requests.append(item_request)

        return {
            "info": {
                "title": quiz.title,
                "documentTitle": f"StudySet Quiz - {quiz.title}",
            },
            "batchUpdate": {
                "requests": requests,
            },
        }

    @classmethod
    def export_google_forms_json(cls, quiz: QuizModel) -> str:
        """Returns the serialized Google Forms API schema JSON for direct use or automated creation."""
        payload = cls.build_google_form_payload(quiz)
        return json.dumps(payload, indent=2)

    @classmethod
    def create_live_google_form(cls, quiz: QuizModel, access_token: str | None = None) -> dict[str, Any]:
        """
        Attempts to create a live Google Form via Google Forms API v1 if OAuth access token is provided.
        If credentials/token are missing, returns documented UNVERIFIED status with setup instructions.
        """
        if not access_token:
            logger.info("Google Forms OAuth token not provided. Returning schema payload and setup instructions.")
            return {
                "status": "unverified",
                "message": (
                    "Google Forms live API integration requires a Google Cloud OAuth2 Access Token with scope "
                    "'https://www.googleapis.com/auth/forms.body'. Configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                    "in backend/.env to enable direct one-click form generation."
                ),
                "form_payload": cls.build_google_form_payload(quiz),
            }

        # If a valid OAuth token is supplied, make real HTTP request to Google Forms API
        try:
            import urllib.request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            # 1. Create Form
            init_payload = json.dumps({"info": {"title": quiz.title}}).encode("utf-8")
            req = urllib.request.Request(
                "https://forms.googleapis.com/v1/forms",
                data=init_payload,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                created_form = json.loads(resp.read().decode("utf-8"))
                form_id = created_form.get("formId")

            # 2. Batch Update items
            batch_data = json.dumps(cls.build_google_form_payload(quiz)["batchUpdate"]).encode("utf-8")
            batch_req = urllib.request.Request(
                f"https://forms.googleapis.com/v1/forms/{form_id}:batchUpdate",
                data=batch_data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(batch_req) as b_resp:
                json.loads(b_resp.read().decode("utf-8"))

            return {
                "status": "success",
                "form_id": form_id,
                "form_url": f"https://docs.google.com/forms/d/{form_id}/viewform",
                "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
            }
        except Exception as e:
            logger.error(f"Failed to create live Google Form: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Encountered an error communicating with Google Forms API. Verify OAuth token scopes and permissions.",
            }
