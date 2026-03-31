"""最小竖直流管道 - 端到端流程编排器."""

from pathlib import Path
from typing import Any

from loguru import logger

from ikos.core import OllamaProvider, PlaywrightSearchProvider
from ikos.stage1_requirement import RequirementParser, SideSupervisor
from ikos.stage2_search import MemoManager, SearchExecutor, TaskSplitter
from ikos.stage3_filter import DataMerger, DataRefiner, InitialFilter
from ikos.stage4_output import FileOutputter, OutputDispatcher
from ikos.utils.logger import setup_logger


class IkosPipeline:
    """Ikos 最小竖直流管道。

    编排四个阶段的完整流程：
    1. 需求解析
    2. 智能检索
    3. 数据筛选
    4. 输出分流
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化管道。

        Args:
            config_path: 配置文件路径
        """
        # 设置日志
        setup_logger(log_file="./data/logs/ikos.log", level="INFO")

        logger.info("初始化 Ikos 管道")

        # 加载配置
        self.config = self._load_config(config_path)

        # 初始化核心组件
        self.model_provider = OllamaProvider(
            base_url=self.config.get("model", {})
            .get("ollama", {})
            .get("base_url", "http://localhost:11434"),
            timeout=self.config.get("model", {}).get("ollama", {}).get("timeout", 120),
        )

        self.search_provider = PlaywrightSearchProvider(
            headless=self.config.get("search", {}).get("browser", {}).get("headless", True),
            timeout=self.config.get("search", {}).get("browser", {}).get("timeout", 30000),
            default_engine=self.config.get("search", {}).get("default_engine", "auto"),
        )

        # 初始化各阶段组件
        self._init_stage1()
        self._init_stage2()
        self._init_stage3()
        self._init_stage4()

        logger.info("Ikos 管道初始化完成")

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """加载配置文件。

        Args:
            config_path: 配置文件路径

        Returns:
            dict: 配置字典
        """
        import yaml

        path = Path(config_path)
        if not path.exists():
            logger.warning(f"配置文件不存在：{path}，使用默认配置")
            return {}

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _init_stage1(self) -> None:
        """初始化第一阶段组件。"""
        self.stage1_parser = RequirementParser(self.model_provider)
        self.stage1_supervisor = SideSupervisor(self.model_provider)

    def _init_stage2(self) -> None:
        """初始化第二阶段组件。"""
        self.stage2_splitter = TaskSplitter(self.model_provider)
        self.stage2_searcher = SearchExecutor(self.model_provider, self.search_provider)
        self.stage2_memo = MemoManager(self.model_provider)

    def _init_stage3(self) -> None:
        """初始化第三阶段组件。"""
        self.stage3_filter = InitialFilter(self.model_provider)
        self.stage3_merger = DataMerger(self.model_provider)
        self.stage3_refiner = DataRefiner(self.model_provider)

    def _init_stage4(self) -> None:
        """初始化第四阶段组件。"""
        self.stage4_dispatcher = OutputDispatcher(self.model_provider)
        self.stage4_outputter = FileOutputter()

    def run(self, user_input: str, output_config: dict[str, Any] | None = None) -> dict[str, Any]:
        """运行完整流程。

        Args:
            user_input: 用户自然语言输入
            output_config: 输出配置（可选）

        Returns:
            dict: 执行结果
        """
        logger.info(f"开始执行流程，用户输入：{user_input[:50]}...")

        try:
            # 第一阶段：需求解析
            stage1_result = self._run_stage1(user_input)

            # 第二阶段：智能检索
            stage2_result = self._run_stage2(stage1_result)

            # 第三阶段：数据筛选
            stage3_result = self._run_stage3(stage2_result, stage1_result)

            # 第四阶段：输出分流
            stage4_result = self._run_stage4(stage3_result, output_config)

            # 汇总结果
            final_result = {
                "status": "success",
                "stage1": "completed",
                "stage2": "completed",
                "stage3": "completed",
                "stage4": "completed",
                "output_files": stage4_result.get("files", []),
                "output_summary": {
                    "total_files": len(stage4_result.get("files", [])),
                    "database_records": stage4_result.get("database_records", 0),
                },
            }

            logger.info("流程执行完成")
            return final_result

        except Exception as e:
            logger.error(f"流程执行失败：{e}")
            return {"status": "error", "error": str(e), "stage": "unknown"}

    def _run_stage1(self, user_input: str) -> dict[str, Any]:
        """执行第一阶段：需求解析。

        Args:
            user_input: 用户输入

        Returns:
            dict: 阶段结果
        """
        logger.info("=== 第一阶段：需求解析 ===")

        # 初始解析
        parse_result = self.stage1_parser.parse(user_input)
        core_topic = parse_result.get("key_concepts", ["unknown"])[0]

        # 简化实现：只执行一轮解析
        engineered_prompt = self.stage1_parser.generate_final_prompt(
            core_topic=core_topic, core_circle={"core": core_topic}
        )

        result = {
            "core_topic": core_topic,
            "parse_result": parse_result,
            "engineered_prompt": engineered_prompt.get("final_prompt", ""),
        }

        logger.info("第一阶段完成，核心主题：%s", core_topic)
        return result

    def _run_stage2(self, stage1_result: dict[str, Any]) -> dict[str, Any]:
        """执行第二阶段：智能检索。

        Args:
            stage1_result: 第一阶段结果

        Returns:
            dict: 阶段结果
        """
        logger.info("=== 第二阶段：智能检索 ===")

        core_topic = stage1_result["core_topic"]
        engineered_prompt = stage1_result["engineered_prompt"]

        # 任务拆分
        tasks = self.stage2_splitter.split(engineered_prompt, core_topic)

        # 执行搜索任务（简化：只执行第一个任务）
        if tasks.get("tasks"):
            first_task = tasks["tasks"][0]
            self.stage2_searcher.execute_task(first_task, core_topic)

        # 获取搜索数据
        found_data, memo_items = self.stage2_searcher.get_all_data()

        result = {"tasks": tasks, "found_data": found_data, "memo_items": memo_items}

        logger.info("第二阶段完成，找到 %d 个数据项", len(found_data))
        return result

    def _run_stage3(
        self, stage2_result: dict[str, Any], stage1_result: dict[str, Any]
    ) -> dict[str, Any]:
        """执行第三阶段：数据筛选。

        Args:
            stage2_result: 第二阶段结果
            stage1_result: 第一阶段结果

        Returns:
            dict: 阶段结果
        """
        logger.info("=== 第三阶段：数据筛选 ===")

        core_topic = stage1_result["core_topic"]
        found_data = stage2_result["found_data"]

        # 初筛
        filtered_data = self.stage3_filter.filter_batch(found_data, core_topic)

        # 合并
        merge_result = self.stage3_merger.merge(filtered_data, core_topic)
        knowledge_graph = self.stage3_merger.get_knowledge_graph()

        # 精筛与重写
        refined = self.stage3_refiner.refine(
            merge_result["merged_data"], knowledge_graph, core_topic
        )

        rewritten_content = self.stage3_refiner.rewrite(refined, knowledge_graph, core_topic)

        result = {
            "filtered_data": filtered_data,
            "merged_data": merge_result,
            "knowledge_graph": knowledge_graph,
            "refined_data": refined,
            "rewritten_content": rewritten_content,
        }

        logger.info("第三阶段完成，知识图谱节点：%d", len(knowledge_graph.get("nodes", [])))
        return result

    def _run_stage4(
        self, stage3_result: dict[str, Any], output_config: dict[str, Any] | None
    ) -> dict[str, Any]:
        """执行第四阶段：输出分流。

        Args:
            stage3_result: 第三阶段结果
            output_config: 输出配置

        Returns:
            dict: 阶段结果
        """
        logger.info("=== 第四阶段：输出分流 ===")

        # 配置输出
        if output_config is None:
            output_config = {"output_type": "file", "formats": ["json", "markdown"]}

        self.stage4_dispatcher.configure(output_config)

        # 执行分流
        knowledge_graph = stage3_result["knowledge_graph"]
        structured_data = stage3_result["merged_data"]
        rewritten_content = stage3_result["rewritten_content"]

        dispatch_result = self.stage4_dispatcher.dispatch(
            structured_data, knowledge_graph, rewritten_content
        )

        logger.info("第四阶段完成，输出 %d 个文件", len(dispatch_result.get("files", [])))
        return dispatch_result

    def reset(self) -> None:
        """重置管道状态。"""
        logger.info("重置管道状态")

        self.stage1_parser.reset()
        self.stage1_supervisor.reset()
        self.stage2_splitter.reset()
        self.stage2_searcher.reset()
        self.stage2_memo.reset()
        self.stage3_filter.reset()
        self.stage3_merger.reset()
        self.stage3_refiner.reset()
        self.stage4_dispatcher.reset()
        self.stage4_outputter.reset()
