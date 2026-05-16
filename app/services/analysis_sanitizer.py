from app.core.exceptions import BusinessError, ErrorCode
from app.schemas.analysis import CleanAnalysisResult

RISK_TEXTS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
    "observe": "待观察",
}
FORBIDDEN_MEDICAL_TERMS = ("诊断", "治疗", "处方")


def sanitize_ai_result(raw_result: dict) -> CleanAnalysisResult:
    """Validate and normalize raw AI output into the public analysis contract."""
    try:
        score = int(raw_result.get("score"))
        risk_level = str(raw_result.get("riskLevel") or raw_result.get("risk_level") or "").strip()
        summary = _sanitize_text(str(raw_result.get("summary") or "建议继续观察宠物日常状态。"))
        observation_advice = raw_result.get("observationAdvice") or raw_result.get("observation_advice")
        diet_advice = _sanitize_text(str(raw_result.get("dietAdvice") or raw_result.get("diet_advice") or "保持规律饮食和充足饮水。"))
        need_vet = bool(raw_result.get("needVet") or raw_result.get("need_vet") or False)
    except (TypeError, ValueError):
        raise BusinessError(ErrorCode.analysis_failed) from None

    if score < 1 or score > 100 or risk_level not in RISK_TEXTS:
        raise BusinessError(ErrorCode.analysis_failed)

    if not isinstance(observation_advice, list) or not observation_advice:
        observation_advice = ["建议观察 24 到 48 小时，注意饮食和精神状态变化"]

    clean_advice = [_sanitize_text(str(item)) for item in observation_advice[:5] if str(item).strip()]
    if not clean_advice:
        clean_advice = ["建议观察 24 到 48 小时，注意饮食和精神状态变化"]

    return CleanAnalysisResult(
        score=score,
        risk_level=risk_level,
        risk_text=RISK_TEXTS[risk_level],
        summary=summary,
        observation_advice=clean_advice,
        diet_advice=diet_advice,
        need_vet=need_vet,
    )


def _sanitize_text(text: str) -> str:
    """Remove high-risk medical wording from text returned to users."""
    clean_text = text.strip()
    for term in FORBIDDEN_MEDICAL_TERMS:
        clean_text = clean_text.replace(term, "健康参考")
    return clean_text
