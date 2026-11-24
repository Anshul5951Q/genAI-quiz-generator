from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attempt import QuizAttemptModel
from app.models.quiz import QuizModel
from app.services.export_service import ExportService

router = APIRouter(tags=["Export"])


@router.get("/quizzes/{quiz_id}/export")
def export_quiz(
    quiz_id: str,
    format: str = Query(
        "student_pdf",
        pattern="^(student_pdf|instructor_pdf|student_docx|instructor_docx|csv|google_forms_json)$",
    ),
    version: str = Query("A", max_length=5),
    db: Session = Depends(get_db),
):
    """
    Exports a quiz in chosen format:
    - 'student_pdf': Printable test without answers or explanations
    - 'instructor_pdf': Complete exam with highlighted correct answers and evidence
    - 'student_docx': Word (.docx) student question paper
    - 'instructor_docx': Word (.docx) instructor answer key and evidence
    - 'csv': Standard spreadsheet containing all questions and keys
    - 'google_forms_json': Google Forms API v1 compatible JSON schema
    """
    quiz = db.query(QuizModel).filter(QuizModel.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    clean_title = "".join(c for c in quiz.title if c.isalnum() or c in (" ", "_", "-")).strip() or "Quiz"

    if format == "student_pdf":
        pdf_bytes = ExportService.generate_quiz_pdf(quiz, include_answers=False)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_Student_V{version}.pdf"'},
        )
    elif format == "instructor_pdf":
        pdf_bytes = ExportService.generate_quiz_pdf(quiz, include_answers=True)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_Instructor_Key_V{version}.pdf"'},
        )
    elif format == "student_docx":
        docx_bytes = ExportService.generate_quiz_docx(quiz, include_answers=False, version_label=version)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_Student_V{version}.docx"'},
        )
    elif format == "instructor_docx":
        docx_bytes = ExportService.generate_quiz_docx(quiz, include_answers=True, version_label=version)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_Instructor_Key_V{version}.docx"'},
        )
    elif format == "google_forms_json":
        from app.services.google_forms_service import GoogleFormsService
        json_data = GoogleFormsService.export_google_forms_json(quiz)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_Google_Forms_Schema.json"'},
        )
    else:  # csv
        csv_data = ExportService.generate_quiz_csv(quiz)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_Questions.csv"'},
        )


@router.get("/attempts/{attempt_id}/export")
def export_attempt_results(
    attempt_id: str,
    format: str = Query("csv", pattern="^(csv)$"),
    db: Session = Depends(get_db),
):
    """Exports student attempt performance and answers to CSV."""
    attempt = db.query(QuizAttemptModel).filter(QuizAttemptModel.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found.")

    csv_data = ExportService.generate_attempt_results_csv(attempt)
    title = attempt.quiz.title if attempt.quiz else "Quiz"
    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip() or "Quiz"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{clean_title}_Attempt_Results.csv"'},
    )


@router.get("/publications/{publication_id}/export")
def export_publication_batch_results(
    publication_id: str,
    format: str = Query("csv", pattern="^(csv)$"),
    db: Session = Depends(get_db),
):
    """Exports all student submissions for a given published assessment to CSV."""
    from app.models.publication import PublicationModel
    pub = db.query(PublicationModel).filter(PublicationModel.id == publication_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found.")

    attempts = (
        db.query(QuizAttemptModel)
        .filter(QuizAttemptModel.publication_id == publication_id)
        .order_by(QuizAttemptModel.completed_at.desc())
        .all()
    )

    clean_title = "".join(c for c in pub.quiz.title if c.isalnum() or c in (" ", "_", "-")).strip() or "Assessment"
    csv_data = ExportService.export_batch_results_csv(attempts, pub.quiz.title)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{clean_title}_Batch_Results.csv"'},
    )
