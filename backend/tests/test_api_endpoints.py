

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_model" in data
    assert data["demo_mode_available"] is True


def test_quiz_lifecycle_and_exports(client):
    # 1. Generate quiz in demo mode
    source_material = (
        "Operating systems manage hardware resources through abstraction layers. "
        "The kernel serves as the core program interfacing between software and the CPU. "
        "Process scheduling ensures fair access to execution cores. "
        "Memory paging divides memory into physical frames and virtual pages. "
        "Deadlocks occur when processes hold mutual exclusive resources in circular wait."
    )
    generate_payload = {
        "title": "OS Core Concepts",
        "source_text": source_material,
        "source_type": "pasted",
        "num_questions": 5,
        "difficulty": "mixed",
        "topic_focus": "Operating Systems",
        "use_demo_mode": True
    }

    gen_resp = client.post("/api/quizzes/generate", json=generate_payload)
    assert gen_resp.status_code == 201
    quiz_data = gen_resp.json()
    quiz_id = quiz_data["id"]
    assert quiz_data["title"] == "OS Core Concepts"
    assert len(quiz_data["questions"]) == 5
    assert quiz_data["status"] == "draft"

    # 2. List quizzes in history
    list_resp = client.get("/api/quizzes")
    assert list_resp.status_code == 200
    quizzes = list_resp.json()
    assert any(q["id"] == quiz_id for q in quizzes)

    # 3. Edit question 1 stem and explanation
    first_q = quiz_data["questions"][0]
    patch_payload = {
        "question_text": "Updated Question Stem on OS Architecture",
        "explanation": "Updated detailed explanation on kernel abstractions."
    }
    patch_resp = client.patch(f"/api/quizzes/{quiz_id}/questions/{first_q['id']}", json=patch_payload)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["question_text"] == "Updated Question Stem on OS Architecture"

    # 4. Delete question 5
    last_q = quiz_data["questions"][-1]
    del_q_resp = client.delete(f"/api/quizzes/{quiz_id}/questions/{last_q['id']}")
    assert del_q_resp.status_code == 204

    # Verify quiz now has 4 questions
    detail_resp = client.get(f"/api/quizzes/{quiz_id}")
    assert detail_resp.status_code == 200
    assert len(detail_resp.json()["questions"]) == 4

    # 5. Publish quiz
    pub_resp = client.post(f"/api/quizzes/{quiz_id}/publish")
    assert pub_resp.status_code == 200
    assert pub_resp.json()["status"] == "published"

    # 6. Test exports
    # Student PDF export
    export_stud = client.get(f"/api/quizzes/{quiz_id}/export?format=student_pdf")
    assert export_stud.status_code == 200
    assert export_stud.headers["content-type"] == "application/pdf"
    assert len(export_stud.content) > 1000

    # Instructor PDF export
    export_inst = client.get(f"/api/quizzes/{quiz_id}/export?format=instructor_pdf")
    assert export_inst.status_code == 200
    assert export_inst.headers["content-type"] == "application/pdf"
    assert len(export_inst.content) > 1000

    # CSV export
    export_csv = client.get(f"/api/quizzes/{quiz_id}/export?format=csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    assert "Question Number,Question Stem" in export_csv.text

    # 7. Delete quiz
    del_resp = client.delete(f"/api/quizzes/{quiz_id}")
    assert del_resp.status_code == 204

    # Confirm 404 after deletion
    get_after_del = client.get(f"/api/quizzes/{quiz_id}")
    assert get_after_del.status_code == 404
