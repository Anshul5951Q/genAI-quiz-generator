from app.models.quiz import OptionModel, QuestionModel, QuizModel


def test_answer_key_secrecy_and_deterministic_scoring(db_session, client):
    # 1. Create a quiz with 2 questions
    quiz = QuizModel(
        title="Operating Systems Memory Management",
        source_type="pasted",
        source_text_length=500,
        difficulty="mixed",
        target_count=2,
        status="published",
        version=1
    )
    db_session.add(quiz)
    db_session.commit()

    q1 = QuestionModel(
        quiz_id=quiz.id,
        question_text="What is virtual memory primarily used for?",
        explanation="Virtual memory allows addressing beyond physical RAM.",
        evidence="allows addressing beyond physical RAM",
        source_page=1,
        topic="Memory",
        difficulty="medium",
        order_index=1
    )
    db_session.add(q1)
    db_session.commit()

    opt1_a = OptionModel(question_id=q1.id, option_letter="A", option_text="Expanding addressable memory", is_correct=True)
    opt1_b = OptionModel(question_id=q1.id, option_letter="B", option_text="Overclocking the CPU", is_correct=False)
    opt1_c = OptionModel(question_id=q1.id, option_letter="C", option_text="Cooling system logic", is_correct=False)
    opt1_d = OptionModel(question_id=q1.id, option_letter="D", option_text="Rendering GPU shaders", is_correct=False)
    db_session.add_all([opt1_a, opt1_b, opt1_c, opt1_d])

    q2 = QuestionModel(
        quiz_id=quiz.id,
        question_text="What is paging in modern OS?",
        explanation="Paging is a memory management scheme eliminating contiguous physical allocation.",
        evidence="eliminating contiguous physical allocation",
        source_page=1,
        topic="Memory",
        difficulty="hard",
        order_index=2
    )
    db_session.add(q2)
    db_session.commit()

    opt2_a = OptionModel(question_id=q2.id, option_letter="A", option_text="Continuous magnetic storage", is_correct=False)
    opt2_b = OptionModel(question_id=q2.id, option_letter="B", option_text="Fixed-size memory block allocation", is_correct=True)
    opt2_c = OptionModel(question_id=q2.id, option_letter="C", option_text="Thread scheduling priority", is_correct=False)
    opt2_d = OptionModel(question_id=q2.id, option_letter="D", option_text="Network socket buffering", is_correct=False)
    db_session.add_all([opt2_a, opt2_b, opt2_c, opt2_d])
    db_session.commit()

    # 2. Check /take endpoint: verify NO answers, NO explanations, NO evidence leak!
    response = client.get(f"/api/quizzes/{quiz.id}/take")
    assert response.status_code == 200
    take_data = response.json()

    assert "questions" in take_data
    assert len(take_data["questions"]) == 2
    for q in take_data["questions"]:
        assert "explanation" not in q
        assert "evidence" not in q
        assert "validation_status" not in q
        for opt in q["options"]:
            assert "is_correct" not in opt, "SECURITY BREACH: is_correct found in quiz-taking view!"

    # 3. Start an attempt
    start_resp = client.post(f"/api/quizzes/{quiz.id}/attempts")
    assert start_resp.status_code == 201
    attempt_id = start_resp.json()["attempt_id"]

    # 4. Submit answers: Question 1 correct (opt1_a), Question 2 unanswered (None)
    submission_payload = {
        "answers": [
            {"question_id": q1.id, "selected_option_id": opt1_a.id},
            {"question_id": q2.id, "selected_option_id": None}
        ]
    }
    submit_resp = client.post(f"/api/attempts/{attempt_id}/submit", json=submission_payload)
    assert submit_resp.status_code == 200
    result = submit_resp.json()

    # Verify deterministic scoring
    assert result["score"] == 1
    assert result["total_questions"] == 2
    assert result["unanswered_count"] == 1
    assert result["score_percentage"] == 50.0

    # Only after submission are answers and explanations revealed
    assert len(result["questions"]) == 2
    res_q1 = next(q for q in result["questions"] if q["id"] == q1.id)
    assert res_q1["is_correct"] is True
    assert res_q1["correct_option_id"] == opt1_a.id
    assert "expanding addressable memory" in res_q1["explanation"].lower() or "virtual memory" in res_q1["explanation"].lower()

    res_q2 = next(q for q in result["questions"] if q["id"] == q2.id)
    assert res_q2["is_correct"] is False
    assert res_q2["selected_option_id"] is None
    assert res_q2["correct_option_id"] == opt2_b.id

    # 5. Verify double-submission is rejected
    double_resp = client.post(f"/api/attempts/{attempt_id}/submit", json=submission_payload)
    assert double_resp.status_code == 400
    assert "already been submitted" in double_resp.json()["detail"]


def test_invalid_option_id_submission(db_session, client):
    quiz = QuizModel(title="Test Quiz", source_type="pasted", target_count=1, status="published")
    db_session.add(quiz)
    db_session.commit()

    q = QuestionModel(quiz_id=quiz.id, question_text="Stem", explanation="Exp", evidence="Ev", order_index=1)
    db_session.add(q)
    db_session.commit()

    opt_a = OptionModel(question_id=q.id, option_letter="A", option_text="A", is_correct=True)
    opt_b = OptionModel(question_id=q.id, option_letter="B", option_text="B", is_correct=False)
    opt_c = OptionModel(question_id=q.id, option_letter="C", option_text="C", is_correct=False)
    opt_d = OptionModel(question_id=q.id, option_letter="D", option_text="D", is_correct=False)
    db_session.add_all([opt_a, opt_b, opt_c, opt_d])
    db_session.commit()

    start_resp = client.post(f"/api/quizzes/{quiz.id}/attempts")
    attempt_id = start_resp.json()["attempt_id"]

    # Submit an invalid foreign option ID
    invalid_submission = {
        "answers": [
            {"question_id": q.id, "selected_option_id": "totally-invalid-option-id"}
        ]
    }
    submit_resp = client.post(f"/api/attempts/{attempt_id}/submit", json=invalid_submission)
    assert submit_resp.status_code == 400
    assert "invalid for question" in submit_resp.json()["detail"]
