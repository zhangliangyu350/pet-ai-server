import logging

from app.core.logging import SensitiveDataFilter, mask_sensitive_text


def test_mask_sensitive_text_redacts_wechat_query_values():
    text = (
        "GET https://api.weixin.qq.com/sns/jscode2session?"
        "appid=wx123&secret=abc&js_code=login_code&grant_type=authorization_code"
    )

    masked = mask_sensitive_text(text)

    assert "wx123" not in masked
    assert "abc" not in masked
    assert "login_code" not in masked
    assert "appid=***" in masked
    assert "secret=***" in masked
    assert "js_code=***" in masked


def test_mask_sensitive_text_redacts_bearer_token():
    masked = mask_sensitive_text("Authorization: Bearer secret_token_value")

    assert "secret_token_value" not in masked
    assert "Bearer ***" in masked


def test_sensitive_filter_masks_record_message_args():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request %s",
        args=("appid=wx123&secret=abc",),
        exc_info=None,
    )

    assert SensitiveDataFilter().filter(record) is True
    assert "wx123" not in record.getMessage()
    assert "abc" not in record.getMessage()

