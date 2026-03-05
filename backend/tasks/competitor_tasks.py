"""
FuviAI Marketing Agent — Celery Tasks: Competitor Intelligence
Chạy 1 lần/ngày, crawl và diff website đối thủ
"""

from __future__ import annotations

from loguru import logger

from backend.tasks.celery_app import app

# Singleton competitor agent (persist giữa các task runs)
_competitor_agent = None


def get_competitor_agent():
    global _competitor_agent
    if _competitor_agent is None:
        from backend.agents.competitor_agent import CompetitorAgent
        _competitor_agent = CompetitorAgent()
    return _competitor_agent


@app.task(name="backend.tasks.competitor_tasks.run_daily_competitor_scan", bind=True, max_retries=1)
def run_daily_competitor_scan(self):
    """
    Task Celery: Scan đối thủ hàng ngày lúc 8:00 AM.
    Phát hiện thay đổi giá, nội dung mới, campaign mới.
    """
    try:
        agent = get_competitor_agent()
        result = agent.daily_scan()

        alerts = result.get("alerts", [])
        if alerts:
            logger.warning(f"Competitor alerts: {alerts}")
        else:
            logger.info(f"Competitor scan clean | scanned={result.get('competitors_scanned', 0)}")

        return result
    except Exception as exc:
        logger.error(f"Competitor scan failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@app.task(name="backend.tasks.competitor_tasks.add_competitor_and_snapshot")
def add_competitor_and_snapshot(
    name: str,
    website: str,
    facebook_page: str = "",
    industry: str = "general",
):
    """
    Task on-demand: Thêm đối thủ mới và lấy snapshot ban đầu.
    """
    try:
        agent = get_competitor_agent()
        agent.add_competitor(name, website, facebook_page, industry)
        snapshot = agent.snapshot_competitor(name)
        logger.info(f"Competitor added + snapshot | name={name}")
        return {"name": name, "snapshot": snapshot}
    except Exception as exc:
        logger.error(f"Add competitor failed: {exc}")
        return {"error": str(exc)}


@app.task(name="backend.tasks.competitor_tasks.generate_counter_strategy")
def generate_counter_strategy_task(
    competitor_name: str,
    trigger_event: str,
    budget: float = 50_000_000,
):
    """
    Task on-demand: Tạo counter-strategy ngay khi phát hiện sự kiện lớn.
    Target: hoàn thành < 30 giây.
    """
    try:
        agent = get_competitor_agent()
        strategy = agent.generate_counter_strategy(
            competitor_name, trigger_event, budget
        )
        logger.info(f"Counter-strategy generated | competitor={competitor_name}")
        return {"competitor": competitor_name, "trigger": trigger_event, "strategy": strategy}
    except Exception as exc:
        logger.error(f"Counter-strategy task failed: {exc}")
        return {"error": str(exc)}
