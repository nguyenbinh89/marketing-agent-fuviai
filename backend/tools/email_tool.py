"""
FuviAI Marketing Agent — SendGrid Email Tool
Gửi email transactional và marketing qua SendGrid API v3
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger


SENDGRID_API_URL = "https://api.sendgrid.com/v3"


@dataclass
class EmailRecipient:
    email: str
    name: str = ""


@dataclass
class EmailResult:
    success: bool
    message_id: str = ""
    error: str = ""
    status_code: int = 0


@dataclass
class BatchEmailResult:
    sent: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class EmailTool:
    """
    Gửi email qua SendGrid API v3.

    Env vars cần thiết:
        SENDGRID_API_KEY     — API key từ SendGrid dashboard
        SENDGRID_FROM_EMAIL  — Email người gửi (đã verify domain)
        SENDGRID_FROM_NAME   — Tên hiển thị người gửi

    Usage:
        tool = EmailTool()

        # Gửi 1 email
        result = tool.send_email(
            to_email="khach@example.com",
            to_name="Nguyễn Văn A",
            subject="Ưu đãi đặc biệt dành cho bạn",
            html_content="<p>Nội dung email</p>",
        )

        # Gửi hàng loạt (personalisation per recipient)
        result = tool.send_bulk(recipients=[...], subject="...", template="...")
    """

    def __init__(self):
        from backend.config.settings import get_settings
        settings = get_settings()
        self._api_key: str = settings.sendgrid_api_key
        self._from_email: str = settings.sendgrid_from_email
        self._from_name: str = settings.sendgrid_from_name
        self._enabled: bool = bool(self._api_key)

        if not self._enabled:
            logger.warning("SendGrid API key not configured — email sending disabled")

    # ─── Internal helpers ────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict) -> tuple[int, dict]:
        """POST to SendGrid API, returns (status_code, response_body)."""
        try:
            resp = httpx.post(
                f"{SENDGRID_API_URL}{endpoint}",
                json=payload,
                headers=self._headers(),
                timeout=15,
            )
            # SendGrid trả 202 khi thành công, không có body
            body: dict = {}
            if resp.content:
                try:
                    body = resp.json()
                except Exception:
                    pass
            return resp.status_code, body
        except httpx.TimeoutException:
            return 408, {"error": "Request timeout"}
        except Exception as e:
            return 500, {"error": str(e)}

    @staticmethod
    def _plain_from_html(html: str) -> str:
        """Strip HTML tags để tạo plain-text fallback."""
        return re.sub(r"<[^>]+>", "", html).strip()

    @staticmethod
    def _wrap_html(content: str, subject: str) -> str:
        """
        Bọc plain text thành HTML email đơn giản nếu content chưa có thẻ HTML.
        Giữ nguyên nếu đã có HTML.
        """
        if content.strip().startswith("<"):
            return content
        # Convert newlines → <br> / <p>
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        body = "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs)
        return f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><title>{subject}</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;color:#333">
{body}
<hr style="margin-top:32px;border:none;border-top:1px solid #eee">
<p style="font-size:12px;color:#999">
  Bạn nhận email này vì đã đăng ký nhận thông tin từ FuviAI.<br>
  <a href="{{{{unsubscribe}}}}" style="color:#999">Huỷ đăng ký</a>
</p>
</body>
</html>"""

    # ─── Core send ───────────────────────────────────────────────────────────

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: str = "",
        reply_to: str = "",
        categories: list[str] | None = None,
        custom_args: dict[str, str] | None = None,
    ) -> EmailResult:
        """
        Gửi 1 email đơn.

        Args:
            to_email: Email người nhận
            subject: Tiêu đề email
            html_content: Nội dung (HTML hoặc plain text — tự động wrap)
            to_name: Tên người nhận (hiển thị trong mail client)
            reply_to: Reply-to address (mặc định = from_email)
            categories: Tag để filter trong SendGrid dashboard
            custom_args: Metadata (VD: {"customer_id": "123", "trigger": "birthday"})
        """
        if not self._enabled:
            logger.warning(f"Email skipped (SendGrid disabled) | to={to_email} | subject={subject}")
            return EmailResult(success=False, error="SendGrid not configured")

        html = self._wrap_html(html_content, subject)
        plain = self._plain_from_html(html)

        payload: dict[str, Any] = {
            "personalizations": [{
                "to": [{"email": to_email, "name": to_name}],
            }],
            "from": {"email": self._from_email, "name": self._from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": plain},
                {"type": "text/html",  "value": html},
            ],
        }

        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        if categories:
            payload["categories"] = categories[:10]  # SendGrid max 10
        if custom_args:
            payload["custom_args"] = {k: str(v) for k, v in custom_args.items()}

        status, body = self._post("/mail/send", payload)

        if status == 202:
            logger.info(f"Email sent | to={to_email} | subject={subject}")
            return EmailResult(success=True, status_code=202)

        error_msg = str(body.get("errors", body.get("error", f"HTTP {status}")))
        logger.error(f"Email failed | to={to_email} | status={status} | error={error_msg}")
        return EmailResult(success=False, error=error_msg, status_code=status)

    # ─── Bulk send ───────────────────────────────────────────────────────────

    def send_bulk(
        self,
        recipients: list[dict[str, str]],
        subject: str,
        html_content: str,
        categories: list[str] | None = None,
    ) -> BatchEmailResult:
        """
        Gửi email hàng loạt với cùng nội dung (personalised subject header).

        Args:
            recipients: [{"email": "...", "name": "...", "substitutions": {...}}, ...]
                        substitutions: dict các biến thay thế trong html_content
                        VD: {"{{name}}": "Nguyễn Văn A", "{{offer}}": "20%"}
            subject: Tiêu đề chung
            html_content: Template HTML (có thể có {{biến}} để thay thế)
            categories: Tag SendGrid

        Returns:
            BatchEmailResult với số lượng sent/failed
        """
        if not self._enabled:
            return BatchEmailResult(
                sent=0,
                failed=len(recipients),
                errors=["SendGrid not configured"],
            )

        result = BatchEmailResult()

        for r in recipients:
            email = r.get("email", "")
            if not email:
                result.failed += 1
                result.errors.append("Missing email address")
                continue

            # Apply substitutions nếu có
            content = html_content
            subs = r.get("substitutions", {})
            for placeholder, value in subs.items():
                content = content.replace(placeholder, str(value))

            res = self.send_email(
                to_email=email,
                to_name=r.get("name", ""),
                subject=subject,
                html_content=content,
                categories=categories,
                custom_args={"segment": r.get("segment", ""), "campaign": r.get("campaign", "")},
            )

            if res.success:
                result.sent += 1
            else:
                result.failed += 1
                result.errors.append(f"{email}: {res.error}")

        logger.info(
            f"Bulk email done | sent={result.sent} | failed={result.failed} | "
            f"total={len(recipients)}"
        )
        return result

    # ─── Transactional helpers ────────────────────────────────────────────────

    def send_abandoned_cart(
        self,
        to_email: str,
        to_name: str,
        email_content: str,
        cart_value: float,
        step: int = 1,
    ) -> EmailResult:
        """Gửi abandoned cart email (step 1/2/3)."""
        subject_map = {
            1: f"Bạn còn quên gì trong giỏ hàng, {to_name}?",
            2: f"Giỏ hàng {cart_value:,.0f} VNĐ của bạn đang chờ",
            3: "Cơ hội cuối — giỏ hàng của bạn sắp hết hiệu lực",
        }
        subject = subject_map.get(step, f"Giỏ hàng của {to_name}")

        return self.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=email_content,
            categories=["abandoned_cart", f"step_{step}"],
            custom_args={"cart_value": str(cart_value), "step": str(step)},
        )

    def send_birthday(
        self,
        to_email: str,
        to_name: str,
        email_content: str,
    ) -> EmailResult:
        """Gửi birthday email."""
        return self.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=f"Chúc mừng sinh nhật {to_name}! Quà đặc biệt từ FuviAI",
            html_content=email_content,
            categories=["birthday"],
            custom_args={"trigger": "birthday"},
        )

    def send_win_back(
        self,
        to_email: str,
        to_name: str,
        email_content: str,
        days_inactive: int,
    ) -> EmailResult:
        """Gửi win-back email cho khách không hoạt động."""
        if days_inactive > 150:
            subject = f"Chúng tôi nhớ bạn, {to_name}"
        else:
            subject = f"Có điều mới dành cho bạn, {to_name}"

        return self.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=email_content,
            categories=["win_back"],
            custom_args={"days_inactive": str(days_inactive)},
        )

    # ─── Stats / Validation ────────────────────────────────────────────────

    def validate_email(self, email: str) -> bool:
        """Basic email format validation."""
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def get_stats(self, start_date: str, end_date: str) -> dict[str, Any]:
        """
        Lấy stats gửi email từ SendGrid.

        Args:
            start_date: "YYYY-MM-DD"
            end_date:   "YYYY-MM-DD"
        """
        if not self._enabled:
            return {"error": "SendGrid not configured"}

        try:
            resp = httpx.get(
                f"{SENDGRID_API_URL}/stats",
                params={"start_date": start_date, "end_date": end_date},
                headers=self._headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Aggregate totals
                totals: dict[str, int] = {}
                for day in data:
                    for stat in day.get("stats", []):
                        for k, v in stat.get("metrics", {}).items():
                            totals[k] = totals.get(k, 0) + v
                return {"period": f"{start_date}/{end_date}", "totals": totals, "daily": data}
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}
