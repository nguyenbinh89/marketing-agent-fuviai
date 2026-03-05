"""
FuviAI Marketing Agent — Compliance Agent (M12)
Kiểm tra content theo Nghị định 13/2023/NĐ-CP + Luật Quảng cáo VN
Auto-flag trước khi đăng
"""

from __future__ import annotations

import re
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent


COMPLIANCE_SYSTEM = """Bạn là Legal Compliance Specialist của FuviAI, chuyên rà soát content \
marketing theo quy định pháp luật Việt Nam.

## Quy định chính cần tuân thủ

### Nghị định 13/2023/NĐ-CP — Bảo vệ dữ liệu cá nhân
- Không thu thập, xử lý dữ liệu cá nhân khi chưa có sự đồng ý
- Phải có chính sách privacy rõ ràng khi dùng data khách hàng
- Không share/sell dữ liệu khách cho bên thứ 3 không được phép

### Luật Quảng cáo 2012 (sửa đổi 2023)
- Không được quảng cáo sai sự thật, gây nhầm lẫn
- Quảng cáo thực phẩm, thuốc, TPCN phải có giấy phép
- Không dùng từ "nhất", "tốt nhất", "đứng đầu" khi chưa được chứng nhận
- Phải ghi rõ "QUẢNG CÁO" cho paid content
- Không được sử dụng hình ảnh người nổi tiếng khi chưa được phép

### Quy định platform
- Facebook: Không quảng cáo thuốc lá, vũ khí, gambling
- TikTok: Không claim y tế không có căn cứ
- Shopee: Không cạnh tranh không lành mạnh

### Cam kết ROI / Doanh thu
- Không được cam kết con số doanh thu / lợi nhuận cụ thể
- Phải có disclaimer khi nêu case study / testimonial

## Output
- Mức độ: PASS / WARNING / FAIL
- Lý do cụ thể + điều luật vi phạm
- Cách sửa để compliant"""


# ─── Rule-based Pre-check ─────────────────────────────────────────────────────

# Từ ngữ cần cảnh báo
WARNING_PATTERNS = [
    (r"\bsố\s*1\b|đứng\s*đầu|hàng\s*đầu|tốt\s*nhất|duy\s*nhất\s*tại\s*vn", "Superlative claim — cần chứng nhận"),
    (r"đảm\s*bảo|cam\s*kết\s*\d+%|hoàn\s*tiền\s*100%", "Cam kết tuyệt đối — cần disclaimer"),
    (r"chữa\s*bệnh|trị\s*bệnh|khỏi\s*bệnh|điều\s*trị", "Claim y tế — cần giấy phép"),
    (r"giảm\s*cân\s*nhanh|giảm\s*\d+\s*kg", "Claim thực phẩm chức năng — cần kiểm tra"),
    (r"lãi\s*suất|lợi\s*nhuận\s*\d+%|sinh\s*lời", "Claim tài chính — cần disclaimer đầy tư"),
    (r"miễn\s*phí\s*mãi\s*mãi|trọn\s*đời|vĩnh\s*viễn", "Cam kết quá hạn — cần điều khoản rõ"),
    (r"không\s*cần\s*giấy\s*tờ|lách\s*luật|né\s*thuế", "Nội dung vi phạm pháp luật"),
]

# Từ ngữ fail ngay (nghiêm trọng)
FAIL_PATTERNS = [
    (r"lừa\s*đảo|scam|chiếm\s*đoạt", "Nội dung lừa đảo"),
    (r"cờ\s*bạc|cá\s*độ|sòng\s*bài|casino", "Quảng cáo cờ bạc — vi phạm nghiêm trọng"),
    (r"súng|vũ\s*khí|chất\s*nổ|ma\s*túy", "Sản phẩm bị cấm"),
    (r"phân\s*biệt\s*chủng\s*tộc|phân\s*biệt\s*giới\s*tính", "Nội dung phân biệt đối xử"),
    (r"hạ\s*thấp\s*danh\s*dự|bôi\s*nhọ|vu\s*khống", "Nội dung bôi nhọ — vi phạm Luật Dân sự"),
]

# Từ ngữ trong Nghị định 13
PERSONAL_DATA_PATTERNS = [
    (r"số\s*CMND|số\s*CCCD|số\s*hộ\s*chiếu", "Dữ liệu nhạy cảm — NĐ 13/2023"),
    (r"địa\s*chỉ\s*nhà|số\s*điện\s*thoại\s*cá\s*nhân", "Dữ liệu cá nhân — cần consent"),
    (r"dữ\s*liệu\s*sức\s*khỏe|bệnh\s*án|tình\s*trạng\s*sức\s*khỏe", "Dữ liệu sức khỏe — NĐ 13 điều 9"),
]


def _quick_check(text: str) -> dict[str, Any]:
    """Rule-based pre-check nhanh trước khi gọi Claude."""
    issues = []
    text_lower = text.lower()

    for pattern, reason in FAIL_PATTERNS:
        if re.search(pattern, text_lower):
            issues.append({"level": "FAIL", "reason": reason, "pattern": pattern})

    for pattern, reason in WARNING_PATTERNS:
        if re.search(pattern, text_lower):
            issues.append({"level": "WARNING", "reason": reason, "pattern": pattern})

    for pattern, reason in PERSONAL_DATA_PATTERNS:
        if re.search(pattern, text_lower):
            issues.append({"level": "WARNING", "reason": f"NĐ 13/2023: {reason}", "pattern": pattern})

    has_fail = any(i["level"] == "FAIL" for i in issues)
    return {
        "quick_check_passed": not has_fail,
        "issues_found": len(issues),
        "issues": issues,
    }


class ComplianceAgent(BaseAgent):
    """
    Agent rà soát compliance content marketing trước khi đăng.

    Usage:
        agent = ComplianceAgent()

        # Check 1 content
        result = agent.check_content("Caption quảng cáo...")

        # Batch check nhiều content
        results = agent.batch_check([content1, content2, content3])

        # Tự động sửa content vi phạm
        fixed = agent.fix_content("Caption vi phạm...")
    """

    def __init__(self):
        super().__init__(
            system_prompt=COMPLIANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.1,  # Thấp nhất để nhất quán
        )

    # ─── Single Content Check ─────────────────────────────────────────────────

    def check_content(
        self,
        content: str,
        platform: str = "facebook",
        content_type: str = "social_post",
        industry: str = "general",
    ) -> dict[str, Any]:
        """
        Kiểm tra compliance đầy đủ cho 1 nội dung.

        Returns:
            {
                "verdict": "PASS" / "WARNING" / "FAIL",
                "risk_score": 0-100,
                "issues": [...],
                "suggestions": "...",
                "safe_to_publish": bool
            }
        """
        # Bước 1: Rule-based quick check
        quick = _quick_check(content)

        # Bước 2: Nếu fail rõ ràng → không cần gọi Claude
        if any(i["level"] == "FAIL" for i in quick["issues"]):
            logger.warning(f"Content FAILED quick check | issues={quick['issues_found']}")
            return {
                "verdict": "FAIL",
                "risk_score": 95,
                "issues": quick["issues"],
                "safe_to_publish": False,
                "ai_analysis": "Nội dung vi phạm nghiêm trọng — bị chặn bởi rule-based check.",
                "suggestions": "Xóa các từ ngữ vi phạm trước khi gửi AI review.",
            }

        # Bước 3: Claude deep check
        quick_issues_str = "\n".join(
            f"  ⚠️ {i['reason']}" for i in quick["issues"]
        ) if quick["issues"] else "  Không phát hiện vấn đề rõ ràng"

        prompt = f"""Rà soát compliance content marketing Việt Nam:

**Platform:** {platform} | **Loại content:** {content_type} | **Ngành:** {industry}

**Content cần kiểm tra:**
---
{content[:2000]}
---

**Pre-check đã phát hiện:**
{quick_issues_str}

Đánh giá theo:
1. **Luật Quảng cáo VN** — có claim sai sự thật không?
2. **Nghị định 13/2023** — có xử lý dữ liệu cá nhân không phù hợp không?
3. **Platform policy** ({platform}) — vi phạm policy đặc thù không?
4. **Đạo đức kinh doanh** — tạo FOMO giả, misleading không?

Trả về đánh giá theo format:
**VERDICT:** PASS / WARNING / FAIL
**RISK SCORE:** 0-100
**ISSUES:** (danh sách cụ thể nếu có)
**SAFE TO PUBLISH:** Yes / No
**SUGGESTIONS:** (cách sửa cụ thể nếu cần)"""

        ai_analysis = self.chat(prompt, reset_history=True)

        # Parse verdict từ response
        verdict = "PASS"
        risk_score = 10
        safe = True

        if "FAIL" in ai_analysis.upper()[:200]:
            verdict = "FAIL"
            risk_score = 85
            safe = False
        elif "WARNING" in ai_analysis.upper()[:200]:
            verdict = "WARNING"
            risk_score = 45
            safe = True  # Warning nhưng vẫn publish được (với chỉnh sửa)

        # Override nếu quick check đã có warning
        if quick["issues"] and verdict == "PASS":
            verdict = "WARNING"
            risk_score = max(risk_score, 30)

        logger.info(f"Content compliance check | verdict={verdict} | platform={platform}")

        return {
            "verdict": verdict,
            "risk_score": risk_score,
            "quick_check_issues": quick["issues"],
            "ai_analysis": ai_analysis,
            "safe_to_publish": safe,
            "content_length": len(content),
            "platform": platform,
        }

    def batch_check(
        self,
        contents: list[str],
        platform: str = "facebook",
    ) -> list[dict[str, Any]]:
        """
        Kiểm tra nhiều content cùng lúc (dùng rule-based để nhanh,
        chỉ gọi Claude cho những content có warning).
        """
        results = []
        for i, content in enumerate(contents):
            quick = _quick_check(content)

            if quick["issues"]:
                # Có vấn đề → Claude deep check
                result = self.check_content(content, platform)
            else:
                # Clean → PASS nhanh không tốn token
                result = {
                    "verdict": "PASS",
                    "risk_score": 5,
                    "quick_check_issues": [],
                    "safe_to_publish": True,
                    "content_index": i,
                }

            result["content_index"] = i
            result["content_preview"] = content[:80] + "..." if len(content) > 80 else content
            results.append(result)

        failed = sum(1 for r in results if r["verdict"] == "FAIL")
        warnings = sum(1 for r in results if r["verdict"] == "WARNING")
        logger.info(f"Batch compliance check | total={len(contents)} | fail={failed} | warning={warnings}")

        return results

    # ─── Auto-fix ────────────────────────────────────────────────────────────

    def fix_content(
        self,
        content: str,
        issues: list[dict] | None = None,
        platform: str = "facebook",
    ) -> dict[str, str]:
        """
        Tự động sửa content vi phạm để compliant.

        Returns:
            {"original": "...", "fixed": "...", "changes_made": "..."}
        """
        issues_str = ""
        if issues:
            issues_str = "\n".join(f"  - {i.get('reason', '')}" for i in issues)
        else:
            quick = _quick_check(content)
            issues_str = "\n".join(f"  - {i['reason']}" for i in quick["issues"])

        prompt = f"""Sửa content vi phạm để compliant với luật VN:

**Content gốc:**
---
{content[:2000]}
---

**Vấn đề cần sửa:**
{issues_str or 'Chưa rõ — rà soát toàn bộ'}

Yêu cầu:
- Giữ nguyên ý nghĩa và tone gốc
- Chỉ thay đổi những phần vi phạm
- Thêm disclaimer phù hợp nếu cần
- Không làm content kém hấp dẫn hơn

Trả về:
**FIXED CONTENT:**
[Nội dung đã sửa]

**CHANGES MADE:**
[Danh sách thay đổi cụ thể]"""

        raw = self.chat(prompt, reset_history=True)

        # Parse fixed content và changes
        fixed = raw
        changes = ""
        if "FIXED CONTENT:" in raw:
            parts = raw.split("CHANGES MADE:")
            fixed_part = parts[0].replace("FIXED CONTENT:", "").strip()
            fixed = fixed_part
            changes = parts[1].strip() if len(parts) > 1 else ""

        logger.info(f"Content auto-fixed | platform={platform}")
        return {
            "original": content,
            "fixed": fixed,
            "changes_made": changes,
        }

    # ─── Policy Reference ─────────────────────────────────────────────────────

    def get_platform_policies(self, platform: str) -> str:
        """Tóm tắt policy cấm quảng cáo của platform."""
        policies = {
            "facebook": """**Facebook Ads Policy (key points):**
- Cấm: Thuốc lá, vũ khí, gambling, adult content
- Hạn chế: Rượu bia (cần age gating), tài chính (cần disclaimer), sức khỏe
- Phải có: Landing page liên quan, không clickbait, không misleading
- Hình ảnh: Không được > 20% text trong ảnh (khuyến nghị)""",

            "tiktok": """**TikTok Ads Policy (key points):**
- Cấm: Thuốc lá, vũ khí, ma túy, gambling
- Hạn chế: Y tế (cần giấy phép), tài chính
- Đặc thù: Không claim y tế không có căn cứ, không weight-loss extreme
- Phải label: Paid partnership, sponsored content""",

            "shopee": """**Shopee Ads Policy (key points):**
- Không được cạnh tranh không lành mạnh (chỉ trích đối thủ)
- Sản phẩm phải đúng category
- Không dùng từ "authentic", "genuine" sai sự thật
- Phải có đủ rating và review thật""",

            "zalo": """**Zalo OA Policy (key points):**
- Không spam: Max 1 broadcast/ngày/follower
- Không thu thập dữ liệu khi chưa có consent (NĐ 13)
- Phải có nút unsubscribe rõ ràng
- Không phát tán tin giả, nội dung chính trị""",

            "google": """**Google Ads Policy (key points):**
- Cấm: Vũ khí, drugs, adult content, counterfeit goods
- Hạn chế: Y tế, tài chính, gambling (cần verification)
- Không misleading ads, phải match landing page
- Healthcare: cần certification từ Google""",
        }

        return policies.get(platform.lower(), f"Chưa có policy guide cho platform: {platform}")

    def pre_publish_checklist(
        self,
        content: str,
        platform: str,
        industry: str = "general",
    ) -> str:
        """Tạo checklist kiểm tra trước khi đăng."""
        prompt = f"""Tạo pre-publish checklist cho content {platform.upper()} ngành {industry}:

**Content:**
{content[:500]}...

Checklist theo format:
✅ / ❌ / ⚠️ [Mục kiểm tra] — [Trạng thái với content này]

Bao gồm:
- Compliance pháp lý (Luật QC, NĐ 13)
- Platform policy
- Brand safety
- Factual accuracy
- CTA compliance
- Disclaimer cần thiết

Kết luận: SAFE TO PUBLISH / NEEDS REVISION / DO NOT PUBLISH"""

        return self.chat(prompt, reset_history=True)
