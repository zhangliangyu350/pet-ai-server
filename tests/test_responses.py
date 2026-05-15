from app.core.responses import error_response, success_response


def test_success_response_matches_contract():
    response = success_response(data={"status": "ok"})

    assert response == {
        "success": True,
        "data": {"status": "ok"},
        "message": "",
    }


def test_success_response_preserves_null_data():
    response = success_response(data=None)

    assert response == {
        "success": True,
        "data": None,
        "message": "",
    }


def test_error_response_matches_contract():
    response = error_response(code="SERVER_ERROR", message="服务异常，请稍后再试")

    assert response == {
        "success": False,
        "data": None,
        "message": "服务异常，请稍后再试",
        "code": "SERVER_ERROR",
    }
