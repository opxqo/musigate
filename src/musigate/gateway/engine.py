import asyncio
from musigate.gateway.executor import Executor


class Engine:
    def __init__(self, bot_config: dict, telegram_client):
        self.config = bot_config
        self.client = telegram_client
        self.executor = Executor(bot_config, self.client)

    def run(self, command: str, return_context: bool = False, **kwargs):
        return asyncio.run(self._run_async(command, return_context=return_context, **kwargs))

    async def _run_async(self, command: str, return_context: bool = False, **kwargs):
        command_def = self.config["commands"].get(command)
        if not command_def:
            raise ValueError(f"机器人不支持命令: {command}")

        context = {
            "query": kwargs.get("query"),
            "url": kwargs.get("url"),
            "source": kwargs.get("source"),
            "search_command": kwargs.get("search_command", "/search"),
            "pick": kwargs.get("pick"),
            "output": kwargs.get("output", "./downloads"),
            "show_progress": kwargs.get("show_progress", False),
            "last_response": None,
            "extracted_data": {},
            "last_action_message_id": None,
            "result": None,
        }
        await self._run_steps(command_def["steps"], context)

        if return_context:
            return context
        return context["result"]

    async def _run_steps(self, steps: list[dict], context: dict):
        retries = self.config.get("settings", {}).get("retry", 0)
        for step in steps:
            attempt = 0
            while True:
                try:
                    await self.executor.run(step, context)
                    break
                except Exception:
                    attempt += 1
                    should_retry = step.get("action") == "wait_response"
                    if not should_retry or attempt > retries:
                        raise
