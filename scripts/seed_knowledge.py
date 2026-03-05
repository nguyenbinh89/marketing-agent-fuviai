"""
FuviAI Marketing Agent — Seed knowledge base với dữ liệu marketing VN
Chạy: python scripts/seed_knowledge.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from backend.memory.vector_store import VectorStore

MARKETING_VN_KNOWLEDGE = [
    {
        "id": "fb-algo-001",
        "text": (
            "Facebook Algorithm 2026: Ưu tiên Reels (video ngắn 15-90s) hơn ảnh tĩnh 3x. "
            "Engagement trong 60 phút đầu quyết định reach. "
            "Comment có từ > 4 từ được tính cao hơn like. "
            "Page đăng 3-5 lần/tuần đạt reach tốt nhất. "
            "Giờ vàng VN: 7-9h sáng, 12-13h trưa, 20-22h tối."
        ),
        "metadata": {"category": "platform", "platform": "facebook", "year": 2026},
    },
    {
        "id": "tiktok-vn-001",
        "text": (
            "TikTok Việt Nam 2026: 50M+ người dùng, 90% dưới 35 tuổi. "
            "Video 15-30s đạt completion rate cao nhất. "
            "3 giây đầu quyết định 70% xem tiếp. "
            "Hashtag: mix trending (#foryou, #fyp) + niche (#review, #unboxing_vn). "
            "TikTok Shop tích hợp: sản phẩm FMCG, thời trang, mỹ phẩm bán tốt nhất."
        ),
        "metadata": {"category": "platform", "platform": "tiktok", "year": 2026},
    },
    {
        "id": "zalo-oa-001",
        "text": (
            "Zalo OA: 74M người dùng tại VN (2025), tỷ lệ đọc tin nhắn 85%+ (vs email ~20%). "
            "Tin nhắn broadcast: tối đa 1000 ký tự, gửi 4 lần/tháng miễn phí. "
            "Zalo Mini App: phù hợp loyalty program, đặt hàng, booking. "
            "Giờ gửi hiệu quả: 8-9h sáng và 19-21h tối. "
            "Tỷ lệ click ZNS (Zalo Notification Service) cao hơn SMS 5x."
        ),
        "metadata": {"category": "platform", "platform": "zalo", "year": 2026},
    },
    {
        "id": "ecom-vn-001",
        "text": (
            "Thương mại điện tử VN 2025: $22B GMV, tăng 18% YoY. "
            "Shopee dẫn đầu 65% thị phần, Lazada 20%, TikTok Shop 10% và đang tăng mạnh. "
            "Mobile commerce: 85% đơn hàng từ điện thoại. "
            "Giờ mua sắm cao điểm: 12h trưa và 21-23h tối. "
            "Flash sale hiệu quả nhất: 0h đêm (12/12, 11/11) và 12h trưa hàng ngày."
        ),
        "metadata": {"category": "market", "segment": "ecommerce", "year": 2025},
    },
    {
        "id": "fmcg-vn-001",
        "text": (
            "FMCG Việt Nam 2026: Tăng trưởng 8% YoY. "
            "Modern Trade (siêu thị, CVS) chiếm 35%, Traditional Trade 45%, Ecommerce 20%. "
            "Người tiêu dùng VN ngày càng chú trọng: sản phẩm organic, made-in-Vietnam, "
            "bao bì thân thiện môi trường. "
            "TikTok Shop và Shopee là kênh FMCG tăng trưởng nhanh nhất."
        ),
        "metadata": {"category": "market", "segment": "fmcg", "year": 2026},
    },
    {
        "id": "sme-marketing-001",
        "text": (
            "SME VN Marketing Budget 2026: Trung bình 5-15% doanh thu cho marketing. "
            "Phân bổ điển hình: Facebook Ads 40%, TikTok 25%, Google 20%, Zalo 10%, khác 5%. "
            "ROI trung bình: Facebook 3-4x, Google Search 5-8x, TikTok 2-4x. "
            "Điểm đau: thiếu nhân lực, khó đo lường ROI, content không đủ."
        ),
        "metadata": {"category": "strategy", "segment": "sme", "year": 2026},
    },
    {
        "id": "compliance-vn-001",
        "text": (
            "Luật Quảng cáo VN + NĐ 13/2023: "
            "Cấm quảng cáo gian dối, phóng đại công dụng. "
            "Quảng cáo y tế phải có xác nhận từ Bộ Y tế. "
            "Thu thập dữ liệu cá nhân phải có consent rõ ràng. "
            "Phạt vi phạm quảng cáo: 5-10 triệu đồng. "
            "Claim 'Số 1', 'Tốt nhất' cần bằng chứng từ tổ chức độc lập."
        ),
        "metadata": {"category": "compliance", "regulation": "VN-2023"},
    },
    {
        "id": "consumer-insight-vn-001",
        "text": (
            "Consumer Insight VN 2026: "
            "Gen Z (18-27): quyết định mua trong 3 giây khi xem TikTok, tin review KOC hơn KOL. "
            "Millennials (28-40): nghiên cứu kỹ trên Google trước khi mua, quan tâm value-for-money. "
            "Gen X (41-55): trung thành với brand, mua qua Zalo và Facebook. "
            "Xu hướng: mua trực tiếp qua live stream tăng 200% YoY."
        ),
        "metadata": {"category": "insight", "segment": "consumer", "year": 2026},
    },
    {
        "id": "fb-benchmark-001",
        "text": (
            "Benchmark quảng cáo Facebook VN 2026: "
            "CTR trung bình: 0.9-2.5% (tốt: >2%). "
            "CPC trung bình: 2,000-8,000đ (FMCG thấp hơn, BĐS cao hơn). "
            "CPM: 15,000-50,000đ tùy ngành. "
            "Conversion rate landing page: 1-3% (tốt: >3%). "
            "ROAS trung bình: 3-5x (ecommerce tốt: >5x)."
        ),
        "metadata": {"category": "benchmark", "platform": "facebook", "year": 2026},
    },
    {
        "id": "season-calendar-vn-001",
        "text": (
            "Lịch mùa vụ marketing VN quan trọng: "
            "Tháng 1-2: Tết Nguyên Đán (mùa cao điểm nhất, CPC tăng 50-60%). "
            "Tháng 3: 8/3 Quốc tế Phụ nữ (beauty, gift). "
            "Tháng 6: Mùa hè, back-to-school. "
            "Tháng 9-10: Trung thu, 20/10 Phụ nữ VN. "
            "Tháng 11: 11/11 Shopee (ecommerce cao điểm). "
            "Tháng 11-12: Black Friday, 12/12 year-end sale."
        ),
        "metadata": {"category": "calendar", "market": "VN"},
    },
]


def seed():
    logger.info("Seeding FuviAI knowledge base...")
    store = VectorStore()

    texts = [item["text"] for item in MARKETING_VN_KNOWLEDGE]
    ids = [item["id"] for item in MARKETING_VN_KNOWLEDGE]
    metadatas = [item["metadata"] for item in MARKETING_VN_KNOWLEDGE]

    store.add_documents(texts, ids=ids, metadatas=metadatas)
    logger.success(f"✅ Seeded {len(MARKETING_VN_KNOWLEDGE)} documents vào knowledge base")

    # Verify
    results = store.search("Facebook marketing Việt Nam", n_results=2)
    logger.info(f"Verify search: tìm thấy {len(results)} kết quả")
    for r in results:
        logger.info(f"  → {r['id']}: {r['text'][:80]}...")


if __name__ == "__main__":
    seed()
