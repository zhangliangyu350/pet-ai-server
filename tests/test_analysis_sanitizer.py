import pytest

from app.core.exceptions import BusinessError, ErrorCode
from app.services.analysis_sanitizer import sanitize_ai_result


def test_sanitize_ai_result_maps_fields_and_filters_medical_terms():
    result = sanitize_ai_result(
        {
            "score": 82,
            "riskLevel": "low",
            "summary": "不构成诊断，仅供观察。",
            "observationAdvice": ["不要自行治疗"],
            "dietAdvice": "不提供处方",
            "needVet": False,
        }
    )

    assert result.risk_text == "低风险"
    assert "诊断" not in result.summary
    assert "治疗" not in result.observation_advice[0]
    assert "处方" not in result.diet_advice


def test_sanitize_ai_result_rejects_bad_score():
    with pytest.raises(BusinessError) as exc_info:
        sanitize_ai_result({"score": 200, "riskLevel": "low"})

    assert exc_info.value.code == ErrorCode.analysis_failed

