"""
FuviAI Marketing Agent — Orchestrator (LangGraph)
Multi-agent workflow: phối hợp 12 agents để xử lý task phức tạp
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, TypedDict
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph chưa cài — orchestrator dùng fallback sequential mode")


# ─── State Schema ─────────────────────────────────────────────────────────────

class CampaignPlanState(TypedDict, total=False):
    """State dùng chung cho workflow lập kế hoạch campaign."""
    task: str                          # Task gốc từ user
    industry: str
    product: str
    budget: float
    season: str

    # Kết quả từng agent
    market_data: str                   # ResearchAgent
    competitor_data: str               # CompetitorAgent
    seo_keywords: str                  # SEOAgent
    content_plan: str                  # ContentAgent
    budget_allocation: str             # AdBudgetAgent
    compliance_check: str              # ComplianceAgent

    # Metadata
    completed_nodes: list[str]
    errors: list[str]
    final_report: str


# ─── Node Timeout Wrapper ─────────────────────────────────────────────────────

async def _run_with_timeout(coro, timeout: int = 60, node_name: str = "") -> Any:
    """Chạy coroutine với timeout. Retry 2 lần rồi skip."""
    for attempt in range(3):
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Node timeout | node={node_name} | attempt={attempt+1}/3")
            if attempt == 2:
                return f"[TIMEOUT] Node {node_name} timed out sau {timeout}s"
        except Exception as e:
            logger.error(f"Node error | node={node_name} | attempt={attempt+1}/3 | error={e}")
            if attempt == 2:
                return f"[ERROR] Node {node_name}: {str(e)}"
            await asyncio.sleep(2)
    return f"[FAILED] Node {node_name}"


# ─── Orchestrator Class ───────────────────────────────────────────────────────

class MarketingOrchestrator:
    """
    LangGraph multi-agent orchestrator cho FuviAI.

    Workflow mặc định (Campaign Planning):
      research → competitor → seo → content → budget → compliance → report

    Usage:
        orch = MarketingOrchestrator()

        # Stream response
        async for chunk in orch.stream_campaign_plan(
            task="Lập kế hoạch campaign Tết 2027 cho ngành F&B",
            product="FuviAI", budget=200_000_000
        ):
            print(chunk)

        # Sync (blocking)
        report = orch.run_campaign_plan(task=..., product=..., budget=...)
    """

    def __init__(self):
        self._graph = self._build_graph() if _LANGGRAPH_AVAILABLE else None

    # ─── Graph Construction ───────────────────────────────────────────────────

    def _build_graph(self):
        """Xây dựng LangGraph StateGraph."""
        graph = StateGraph(CampaignPlanState)

        # Add nodes
        graph.add_node("research", self._node_research)
        graph.add_node("competitor", self._node_competitor)
        graph.add_node("seo", self._node_seo)
        graph.add_node("content", self._node_content)
        graph.add_node("budget", self._node_budget)
        graph.add_node("compliance", self._node_compliance)
        graph.add_node("report", self._node_final_report)

        # Define edges (sequential với parallel options)
        graph.set_entry_point("research")
        graph.add_edge("research", "competitor")
        graph.add_edge("competitor", "seo")
        graph.add_edge("seo", "content")
        graph.add_edge("content", "budget")
        graph.add_edge("budget", "compliance")
        graph.add_edge("compliance", "report")
        graph.add_edge("report", END)

        return graph.compile()

    # ─── Agent Nodes ──────────────────────────────────────────────────────────

    async def _node_research(self, state: CampaignPlanState) -> CampaignPlanState:
        logger.info(f"[Orchestrator] Running node: research")
        try:
            from backend.agents.research_agent import ResearchAgent
            agent = ResearchAgent()

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.industry_analysis(
                        state.get("industry", "marketing"),
                        aspects=["xu hướng 2027", "cơ hội campaign", "consumer insight"]
                    )
                )

            result = await _run_with_timeout(_run(), timeout=60, node_name="research")
            state["market_data"] = result
            state.setdefault("completed_nodes", []).append("research")
        except Exception as e:
            state.setdefault("errors", []).append(f"research: {e}")
            state["market_data"] = f"[Research unavailable: {e}]"

        return state

    async def _node_competitor(self, state: CampaignPlanState) -> CampaignPlanState:
        logger.info("[Orchestrator] Running node: competitor")
        try:
            from backend.agents.competitor_agent import CompetitorAgent
            agent = CompetitorAgent()

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.chat(
                        f"Phân tích landscape cạnh tranh ngành {state.get('industry', 'marketing')} "
                        f"tại VN 2027. Top 3 đối thủ chính và điểm khác biệt của FuviAI.",
                        reset_history=True,
                    )
                )

            result = await _run_with_timeout(_run(), timeout=60, node_name="competitor")
            state["competitor_data"] = result
            state.setdefault("completed_nodes", []).append("competitor")
        except Exception as e:
            state.setdefault("errors", []).append(f"competitor: {e}")
            state["competitor_data"] = f"[Competitor unavailable: {e}]"

        return state

    async def _node_seo(self, state: CampaignPlanState) -> CampaignPlanState:
        logger.info("[Orchestrator] Running node: seo")
        try:
            from backend.agents.seo_agent import SEOAgent
            agent = SEOAgent()

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.keyword_research(
                        topic=state.get("product", "FuviAI"),
                        industry=state.get("industry", "marketing"),
                    )
                )

            result = await _run_with_timeout(_run(), timeout=60, node_name="seo")
            state["seo_keywords"] = result
            state.setdefault("completed_nodes", []).append("seo")
        except Exception as e:
            state.setdefault("errors", []).append(f"seo: {e}")
            state["seo_keywords"] = f"[SEO unavailable: {e}]"

        return state

    async def _node_content(self, state: CampaignPlanState) -> CampaignPlanState:
        logger.info("[Orchestrator] Running node: content")
        try:
            from backend.agents.content_agent import ContentAgent
            agent = ContentAgent()

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.campaign_content(
                        product=state.get("product", "FuviAI"),
                        campaign_name=state.get("task", "Campaign 2027"),
                        platforms=["facebook", "zalo", "tiktok"],
                    )
                )

            result = await _run_with_timeout(_run(), timeout=60, node_name="content")
            state["content_plan"] = result
            state.setdefault("completed_nodes", []).append("content")
        except Exception as e:
            state.setdefault("errors", []).append(f"content: {e}")
            state["content_plan"] = f"[Content unavailable: {e}]"

        return state

    async def _node_budget(self, state: CampaignPlanState) -> CampaignPlanState:
        logger.info("[Orchestrator] Running node: budget")
        try:
            from backend.agents.adbudget_agent import AdBudgetAgent
            agent = AdBudgetAgent()
            budget = state.get("budget", 100_000_000)
            season = state.get("season", "")

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.allocate_by_channel(
                        budget=budget,
                        goal="conversion",
                        industry=state.get("industry", "marketing"),
                    )
                )

            result = await _run_with_timeout(_run(), timeout=60, node_name="budget")
            state["budget_allocation"] = result
            state.setdefault("completed_nodes", []).append("budget")
        except Exception as e:
            state.setdefault("errors", []).append(f"budget: {e}")
            state["budget_allocation"] = f"[Budget unavailable: {e}]"

        return state

    async def _node_compliance(self, state: CampaignPlanState) -> CampaignPlanState:
        logger.info("[Orchestrator] Running node: compliance")
        try:
            from backend.agents.compliance_agent import ComplianceAgent
            agent = ComplianceAgent()

            # Lấy sample content từ content plan để check
            content_sample = state.get("content_plan", "")[:500]

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.chat(
                        f"Rà soát compliance cho campaign '{state.get('task', '')}'. "
                        f"Sample content:\n{content_sample}\n\n"
                        f"Ngành: {state.get('industry', 'marketing')}. "
                        f"Có điểm nào cần lưu ý về Luật Quảng cáo VN và NĐ 13/2023 không?",
                        reset_history=True,
                    )
                )

            result = await _run_with_timeout(_run(), timeout=60, node_name="compliance")
            state["compliance_check"] = result
            state.setdefault("completed_nodes", []).append("compliance")
        except Exception as e:
            state.setdefault("errors", []).append(f"compliance: {e}")
            state["compliance_check"] = f"[Compliance unavailable: {e}]"

        return state

    async def _node_final_report(self, state: CampaignPlanState) -> CampaignPlanState:
        """Tổng hợp tất cả outputs thành báo cáo hoàn chỉnh."""
        logger.info("[Orchestrator] Running node: final_report")
        try:
            from backend.agents.base_agent import BaseAgent
            agent = BaseAgent(max_tokens=8096, temperature=0.3)

            completed = state.get("completed_nodes", [])
            errors = state.get("errors", [])

            prompt = f"""Tổng hợp campaign plan hoàn chỉnh cho FuviAI:

**Task:** {state.get('task', 'Campaign planning')}
**Sản phẩm:** {state.get('product', 'FuviAI')}
**Ngành:** {state.get('industry', 'marketing')}
**Budget:** {state.get('budget', 0):,.0f} VNĐ
**Nodes hoàn thành:** {', '.join(completed)}
{f'**Nodes lỗi:** {chr(10).join(errors)}' if errors else ''}

**Market Research:**
{state.get('market_data', 'N/A')[:800]}

**Competitor Analysis:**
{state.get('competitor_data', 'N/A')[:600]}

**SEO Keywords:**
{state.get('seo_keywords', 'N/A')[:600]}

**Content Plan:**
{state.get('content_plan', 'N/A')[:800]}

**Budget Allocation:**
{state.get('budget_allocation', 'N/A')[:600]}

**Compliance Notes:**
{state.get('compliance_check', 'N/A')[:400]}

Tạo báo cáo executive summary (1500-2000 chữ):

# CAMPAIGN PLAN: {state.get('task', '').upper()}

## 1. Tóm tắt Executive (5 bullet points)
## 2. Market Opportunity
## 3. Strategy & Positioning
## 4. Content Plan (highlights)
## 5. Budget Allocation (bảng)
## 6. KPI & Timeline
## 7. Compliance checklist
## 8. Next steps (3 action items với deadline)"""

            async def _run():
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.chat(prompt, reset_history=True)
                )

            result = await _run_with_timeout(_run(), timeout=90, node_name="final_report")
            state["final_report"] = result
            state.setdefault("completed_nodes", []).append("final_report")

        except Exception as e:
            state.setdefault("errors", []).append(f"final_report: {e}")
            state["final_report"] = self._fallback_report(state)

        return state

    def _fallback_report(self, state: CampaignPlanState) -> str:
        """Báo cáo fallback nếu final_report node lỗi."""
        sections = []
        if state.get("market_data"):
            sections.append(f"**Market Data:**\n{state['market_data'][:500]}")
        if state.get("content_plan"):
            sections.append(f"**Content Plan:**\n{state['content_plan'][:500]}")
        if state.get("budget_allocation"):
            sections.append(f"**Budget:**\n{state['budget_allocation'][:500]}")
        return "\n\n---\n\n".join(sections) or "Orchestrator gặp lỗi — vui lòng thử lại."

    # ─── Public Interface ─────────────────────────────────────────────────────

    async def run_campaign_plan_async(
        self,
        task: str,
        product: str,
        industry: str = "marketing",
        budget: float = 100_000_000,
        season: str = "",
    ) -> dict[str, Any]:
        """
        Chạy full multi-agent workflow bất đồng bộ.
        Trả về state đầy đủ sau khi hoàn thành.
        """
        initial_state: CampaignPlanState = {
            "task": task,
            "product": product,
            "industry": industry,
            "budget": budget,
            "season": season,
            "completed_nodes": [],
            "errors": [],
        }

        logger.info(f"[Orchestrator] Starting campaign plan | task={task[:50]}")

        if self._graph:
            # LangGraph mode
            final_state = await self._graph.ainvoke(initial_state)
        else:
            # Fallback: sequential mode
            final_state = await self._run_sequential(initial_state)

        logger.info(
            f"[Orchestrator] Completed | nodes={final_state.get('completed_nodes')} "
            f"| errors={len(final_state.get('errors', []))}"
        )
        return final_state

    async def _run_sequential(self, state: CampaignPlanState) -> CampaignPlanState:
        """Fallback sequential execution khi không có LangGraph."""
        nodes = [
            self._node_research,
            self._node_competitor,
            self._node_seo,
            self._node_content,
            self._node_budget,
            self._node_compliance,
            self._node_final_report,
        ]
        for node_fn in nodes:
            state = await node_fn(state)
        return state

    def run_campaign_plan(
        self,
        task: str,
        product: str,
        industry: str = "marketing",
        budget: float = 100_000_000,
        season: str = "",
    ) -> dict[str, Any]:
        """Sync wrapper cho async workflow."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Đang trong async context (FastAPI) — dùng run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.run_campaign_plan_async(task, product, industry, budget, season)
                    )
                    return future.result(timeout=360)
            else:
                return loop.run_until_complete(
                    self.run_campaign_plan_async(task, product, industry, budget, season)
                )
        except Exception as e:
            logger.error(f"Orchestrator sync run failed: {e}")
            raise

    async def stream_campaign_plan(
        self,
        task: str,
        product: str,
        industry: str = "marketing",
        budget: float = 100_000_000,
    ) -> AsyncIterator[str]:
        """
        Stream progress real-time — yield từng update khi mỗi node hoàn thành.
        """
        initial_state: CampaignPlanState = {
            "task": task,
            "product": product,
            "industry": industry,
            "budget": budget,
            "completed_nodes": [],
            "errors": [],
        }

        nodes = [
            ("research", "Nghiên cứu thị trường", self._node_research),
            ("competitor", "Phân tích đối thủ", self._node_competitor),
            ("seo", "Nghiên cứu từ khoá SEO", self._node_seo),
            ("content", "Lên kế hoạch content", self._node_content),
            ("budget", "Phân bổ ngân sách", self._node_budget),
            ("compliance", "Kiểm tra compliance", self._node_compliance),
            ("report", "Tổng hợp báo cáo", self._node_final_report),
        ]

        state = initial_state
        yield f"🚀 Bắt đầu lập kế hoạch: **{task}**\n\n"

        for node_id, node_name, node_fn in nodes:
            yield f"⏳ [{node_name}] đang xử lý...\n"
            state = await node_fn(state)
            if node_id in state.get("completed_nodes", []):
                yield f"✅ [{node_name}] hoàn thành\n"
            else:
                yield f"⚠️ [{node_name}] gặp lỗi — tiếp tục\n"

        yield f"\n---\n\n"
        yield state.get("final_report", "Không có báo cáo.")

    # ─── Quick Workflows ──────────────────────────────────────────────────────

    async def quick_content_workflow(
        self,
        product: str,
        platform: str = "facebook",
        tone: str = "than_thien",
    ) -> str:
        """
        Workflow đơn giản hơn: Research → Content → Compliance.
        Nhanh hơn full campaign plan (~30s).
        """
        state: CampaignPlanState = {
            "task": f"Tạo content {platform} cho {product}",
            "product": product,
            "industry": "general",
            "completed_nodes": [],
            "errors": [],
        }

        state = await self._node_research(state)
        state = await self._node_content(state)
        state = await self._node_compliance(state)

        return state.get("content_plan", "Không tạo được content.")

    def get_workflow_status(self, state: dict) -> dict[str, Any]:
        """Lấy trạng thái của workflow đang chạy."""
        nodes_total = 7
        completed = state.get("completed_nodes", [])
        errors = state.get("errors", [])

        return {
            "total_nodes": nodes_total,
            "completed": len(completed),
            "progress_percent": round(len(completed) / nodes_total * 100),
            "completed_nodes": completed,
            "errors": errors,
            "has_final_report": bool(state.get("final_report")),
        }
