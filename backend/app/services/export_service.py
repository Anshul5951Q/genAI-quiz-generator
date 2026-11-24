import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.models.attempt import QuizAttemptModel
from app.models.quiz import QuizModel


class ExportService:
    @staticmethod
    def generate_quiz_pdf(quiz: QuizModel, include_answers: bool = False) -> bytes:
        """
        Generates a PDF quiz document using ReportLab.
        If include_answers is False -> Clean Printable Student Version.
        If include_answers is True -> Complete Instructor Version with Answer Key & Explanations.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "QuizTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=6,
        )

        subtitle_style = ParagraphStyle(
            "QuizSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15,
        )

        q_stem_style = ParagraphStyle(
            "QuestionStem",
            parent=styles["Normal"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )

        opt_style = ParagraphStyle(
            "OptionText",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
        )

        correct_opt_style = ParagraphStyle(
            "CorrectOptionText",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#15803d"),
            fontName="Helvetica-Bold",
        )

        answer_box_style = ParagraphStyle(
            "AnswerBox",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#e2e8f0"),
            borderWidth=1,
            borderPadding=6,
            spaceBefore=6,
        )

        story = []

        # Header
        edition_type = "Instructor Copy — with Answer Key & Explanations" if include_answers else "Student Copy"
        story.append(Paragraph(f"StudySet: {quiz.title}", title_style))
        meta_line = (
            f"Difficulty: {quiz.difficulty.capitalize()} | Questions: {len(quiz.questions)} | Edition: {edition_type}"
        )
        story.append(Paragraph(meta_line, subtitle_style))
        story.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#cbd5e1"),
                spaceAfter=15,
            )
        )

        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)

        for i, q in enumerate(sorted_questions, start=1):
            q_elements = []

            # Question stem with topic and difficulty badges
            badge = f"[{q.difficulty.upper()} | {q.topic}]" if q.topic else f"[{q.difficulty.upper()}]"
            q_elements.append(
                Paragraph(
                    f"<b>{i}.</b> {q.question_text} &nbsp; <font color='#64748b' size='8'>{badge}</font>",
                    q_stem_style,
                )
            )

            # Options
            sorted_opts = sorted(q.options, key=lambda o: o.option_letter)
            for opt in sorted_opts:
                if include_answers and opt.is_correct:
                    opt_line = f"<b>({opt.option_letter})</b> {opt.option_text} &nbsp; [CORRECT]"
                    q_elements.append(Paragraph(opt_line, correct_opt_style))
                else:
                    opt_line = f"({opt.option_letter}) {opt.option_text}"
                    q_elements.append(Paragraph(opt_line, opt_style))
                q_elements.append(Spacer(1, 2))

            if include_answers:
                correct_opt = next((o for o in sorted_opts if o.is_correct), None)
                correct_letter = correct_opt.option_letter if correct_opt else "None"
                page_info = f" (Page {q.source_page})" if q.source_page else ""
                ans_text = (
                    f"<b>Correct Answer:</b> Option {correct_letter}<br/>"
                    f"<b>Explanation:</b> {q.explanation}<br/>"
                    f'<b>Source Evidence{page_info}:</b> <i>"{q.evidence}"</i>'
                )
                q_elements.append(Paragraph(ans_text, answer_box_style))

            q_elements.append(Spacer(1, 14))
            story.append(KeepTogether(q_elements))

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    @staticmethod
    def generate_quiz_csv(quiz: QuizModel) -> str:
        """Generates a CSV export of the quiz questions and answers."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "Question Number",
                "Question Stem",
                "Option A",
                "Option B",
                "Option C",
                "Option D",
                "Correct Option",
                "Explanation",
                "Source Evidence",
                "Source Page",
                "Difficulty",
                "Topic",
            ]
        )

        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)
        for i, q in enumerate(sorted_questions, start=1):
            opts_map = {opt.option_letter: opt.option_text for opt in q.options}
            correct_opt = next((opt.option_letter for opt in q.options if opt.is_correct), "")

            writer.writerow(
                [
                    i,
                    q.question_text,
                    opts_map.get("A", ""),
                    opts_map.get("B", ""),
                    opts_map.get("C", ""),
                    opts_map.get("D", ""),
                    correct_opt,
                    q.explanation,
                    q.evidence,
                    q.source_page or "",
                    q.difficulty,
                    q.topic,
                ]
            )

        return output.getvalue()

    @staticmethod
    def generate_attempt_results_csv(attempt: QuizAttemptModel) -> str:
        """Generates CSV export of a specific student attempt's answers and scores."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Quiz Title", attempt.quiz.title if attempt.quiz else "Quiz"])
        writer.writerow(
            [
                "Score",
                f"{attempt.score} / {attempt.total_questions} ({attempt.score_percentage}%)",
            ]
        )
        writer.writerow(["Unanswered Questions", attempt.unanswered_count])
        writer.writerow(["Completed At", str(attempt.completed_at or "")])
        writer.writerow([])

        writer.writerow(
            [
                "Question Number",
                "Question Stem",
                "Selected Option",
                "Correct Option",
                "Is Correct",
                "Explanation",
                "Source Evidence",
            ]
        )

        answers_map = {ans.question_id: ans for ans in attempt.answers}
        sorted_questions = sorted(attempt.quiz.questions, key=lambda q: q.order_index) if attempt.quiz else []

        for i, q in enumerate(sorted_questions, start=1):
            ans = answers_map.get(q.id)
            selected_letter = ""
            if ans and ans.selected_option_id:
                sel_opt = next((o for o in q.options if o.id == ans.selected_option_id), None)
                if sel_opt:
                    selected_letter = f"{sel_opt.option_letter}: {sel_opt.option_text}"
            else:
                selected_letter = "Unanswered"

            corr_opt = next((o for o in q.options if o.is_correct), None)
            corr_text = f"{corr_opt.option_letter}: {corr_opt.option_text}" if corr_opt else ""

            is_correct_str = "Yes" if ans and ans.is_correct else "No"

            writer.writerow(
                [
                    i,
                    q.question_text,
                    selected_letter,
                    corr_text,
                    is_correct_str,
                    q.explanation,
                    q.evidence,
                ]
            )

        return output.getvalue()

    @staticmethod
    def generate_quiz_docx(quiz: QuizModel, include_answers: bool = False, version_label: str = "A") -> bytes:
        """Generates a professional Word (.docx) document for student or instructor usage."""
        import io

        from docx import Document
        from docx.shared import Inches, Pt, RGBColor

        doc = Document()

        # Title
        title_p = doc.add_paragraph()
        title_run = title_p.add_run(quiz.title)
        title_run.font.size = Pt(20)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(15, 23, 42)

        # Subtitle
        edition = (
            f"Instructor Copy — Version {version_label} (with Answer Key & Explanations)"
            if include_answers
            else f"Student Question Paper — Version {version_label}"
        )
        sub_p = doc.add_paragraph()
        sub_run = sub_p.add_run(
            f"{edition} • Total Questions: {len(quiz.questions)} • Difficulty: {quiz.difficulty.title()}"
        )
        sub_run.font.size = Pt(10)
        sub_run.font.italic = True
        sub_run.font.color.rgb = RGBColor(100, 116, 139)

        if not include_answers:
            meta_table = doc.add_table(rows=1, cols=2)
            meta_table.rows[0].cells[0].text = "Learner Name: _______________________"
            meta_table.rows[0].cells[1].text = "Date / Batch: _______________________"
            doc.add_paragraph()

        # Questions
        for idx, q in enumerate(sorted(quiz.questions, key=lambda x: x.order_index), start=1):
            q_p = doc.add_paragraph()
            q_run = q_p.add_run(f"{idx}. {q.question_text}")
            q_run.font.bold = True
            q_run.font.size = Pt(11)

            for opt in sorted(q.options, key=lambda x: x.option_letter):
                opt_p = doc.add_paragraph()
                opt_p.paragraph_format.left_indent = Inches(0.25)
                opt_run = opt_p.add_run(f"({opt.option_letter}) {opt.option_text}")
                opt_run.font.size = Pt(10)

                if include_answers and opt.is_correct:
                    corr_tag = opt_p.add_run("  [CORRECT]")
                    corr_tag.font.bold = True
                    corr_tag.font.color.rgb = RGBColor(21, 128, 61)

            if include_answers:
                exp_p = doc.add_paragraph()
                exp_p.paragraph_format.left_indent = Inches(0.25)
                exp_run = exp_p.add_run(
                    f"Explanation: {q.explanation}\nEvidence: \"{q.evidence}\" (Source Page/Slide: {q.source_page or 'N/A'})"
                )
                exp_run.font.size = Pt(9)
                exp_run.font.italic = True
                exp_run.font.color.rgb = RGBColor(71, 85, 105)

            doc.add_paragraph()

        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

    @staticmethod
    def export_batch_results_csv(attempts: list[QuizAttemptModel], quiz_title: str) -> str:
        """Generates a CSV export of all learner submissions for a given published assessment."""
        from datetime import UTC, datetime

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Assessment Title", quiz_title])
        writer.writerow(["Exported At", str(datetime.now(UTC))])
        writer.writerow([])
        writer.writerow([
            "Learner Name",
            "Learner Email",
            "Learner ID",
            "Score",
            "Total Questions",
            "Score Percentage",
            "Marks Obtained",
            "Total Marks",
            "Version",
            "Status",
            "Submitted At",
        ])
        for a in attempts:
            writer.writerow([
                a.learner_name or "Anonymous",
                a.learner_email or "N/A",
                a.learner_id or "",
                a.score,
                a.total_questions,
                f"{a.score_percentage}%",
                a.marks_obtained,
                a.total_marks,
                a.version_label or "A",
                a.status,
                str(a.completed_at or a.started_at),
            ])
        return output.getvalue()
