"""
FuviAI Marketing Agent — Celery Tasks: Social Listening
Chạy mỗi 30 phút, detect trends và crisis
"""

from __future__ import annotations

from loguru import logger

from backend.tasks.celery_app import app


@app.task(name="backend.tasks.listening_tasks.run_social_listening", bind=True, max_retries=2)
def run_social_listening(self, industry: str = "marketing", alert_zalo_user: str = ""):
    """
    Task Celery: Chạy social listening scan mỗi 30 phút.

    Args:
        industry: Ngành theo dõi (marketing, fmcg, fb, realestate, ecommerce)
        alert_zalo_user: User ID Zalo để nhận crisis alert
    """
    try:
        from backend.agents.listening_agent import ListeningAgent
        agent = ListeningAgent()
        result = agent.run_scheduled_scan(
            industry=industry,
            crisis_alert_zalo=alert_zalo_user,
        )
        logger.info(
            f"Social listening completed | industry={industry} "
            f"| articles={result.get('articles_found', 0)}"
        )
        return result
    except Exception as exc:
        logger.error(f"Social listening task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(name="backend.tasks.listening_tasks.process_scheduled_posts", bind=True)
def process_scheduled_posts(self):
    """
    Task Celery: Xử lý hàng đợi lịch đăng bài mỗi 5 phút.
    Đăng các bài đã đến giờ (status=pending, scheduled_time <= now).
    """
    try:
        from datetime import datetime
        from backend.agents.social_agent import SocialAgent
        from backend.agents.content_agent import Platform

        agent = SocialAgent()
        pending = agent.get_schedule(status="pending")
        now = datetime.now()
        posted = 0

        for post_data in pending:
            scheduled = datetime.fromisoformat(post_data["scheduled_time"])
            if scheduled <= now:
                # Tìm post trong schedule list và đăng
                for post in agent._schedule:
                    if (
                        post.status == "pending"
                        and post.scheduled_time == scheduled
                    ):
                        result = agent.post_now(
                            post.content,
                            Platform(post.platform),
                        )
                        post.status = result.get("status", "failed")
                        post.post_id = result.get("data", {}).get("id", "")
                        posted += 1
                        break

        if posted > 0:
            logger.info(f"Scheduled posts processed: {posted} posts published")
        return {"posted": posted}

    except Exception as exc:
        logger.error(f"Scheduled posts task failed: {exc}")
        return {"error": str(exc)}


@app.task(name="backend.tasks.listening_tasks.scan_keywords")
def scan_keywords(keywords: list[str], industry: str = "marketing"):
    """
    Task on-demand: Scan danh sách keywords cụ thể.
    """
    try:
        from backend.agents.listening_agent import ListeningAgent
        agent = ListeningAgent()
        results = agent.monitor_keywords(keywords)
        logger.info(f"Keywords scan done | count={len(keywords)} | trends={len(results)}")
        return {"keywords": keywords, "trends": results}
    except Exception as exc:
        logger.error(f"Keywords scan failed: {exc}")
        return {"error": str(exc)}
