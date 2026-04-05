import re
from musigate.gateway.selector import Selector
from musigate.utils.helper import render_template
from musigate.utils.downloader import Downloader
from musigate.telegram.listener import Listener

class Executor:
    def __init__(self, config, client):
        self.config = config
        self.client = client
        self.selector = Selector()
        self.downloader = Downloader(client)
        self.listener = Listener(client.client, config["bot_username"])

    async def run(self, step: dict, context: dict):
        action = step["action"]
        render_context = self._build_render_context(context)

        if action == "send_message":
            content = render_template(step["content"], render_context)
            sent_message = await self.client.send_message(
                self.config["bot_username"], content
            )
            context["lastActionMessageId"] = getattr(sent_message, "id", None)

        elif action == "wait_response":
            timeout = step.get("timeout", self.config["settings"]["timeout"])
            response = await self.listener.wait(
                expect=step["expect"],
                timeout=timeout,
                after_message_id=context.get("lastActionMessageId"),
            )
            context["lastResponse"] = response
            context["last_response"] = response

            if "extract" in step and step["extract"]:
                extract_rule = step["extract"]
                pattern = extract_rule.get("pattern")
                save_as = extract_rule.get("save_as")
                if pattern and save_as and "text" in response:
                    match = re.search(pattern, response["text"], re.MULTILINE)
                    if match:
                        context["extractedData"][save_as] = match.group(1) if match.groups() else match.group(0)

        elif action == "click_button":
            if not context.get("lastResponse") or "buttons" not in context["lastResponse"]:
                raise ValueError("当前没有可点击的按钮响应")

            buttons = context["lastResponse"]["buttons"]
            button = self._select_button(step, context, render_context, buttons)
            await self.client.click_button(button)
            source_message = button.get("_message")
            context["lastActionMessageId"] = getattr(source_message, "id", context.get("lastActionMessageId"))

        elif action == "download":
            if not context.get("lastResponse") or "file" not in context["lastResponse"]:
                raise ValueError("当前没有可下载的文件响应")

            filename = render_template(
                step.get("output", "{title}.{ext}"), render_context
            )
            filename = self._ensure_extension(filename, context["lastResponse"].get("ext"))

            saved_path = await self.downloader.save(
                context["lastResponse"]["file"],
                context["output"],
                filename,
                show_progress=context.get("show_progress", False),
            )
            context["result"] = saved_path
            context["result_filename"] = filename

        elif action == "respond_list":
            if not context.get("lastResponse"):
                raise ValueError("当前没有可返回的搜索结果")

            response = context["lastResponse"]
            text = (response.get("text") or "").strip()
            if text:
                context["result"] = text
            elif response.get("buttons"):
                context["result"] = "\n".join(
                    button.get("text", "")
                    for row in response["buttons"]
                    for button in row
                    if button.get("text")
                )
            else:
                context["result"] = ""

        elif action == "respond_buttons":
            if not context.get("lastResponse") or "buttons" not in context["lastResponse"]:
                raise ValueError("当前没有可返回的按钮响应")
            context["result"] = context["lastResponse"]["buttons"]

        elif action == "branch":
            last_resp = context.get("lastResponse", {})
            matched = False
            for case in step.get("cases", []):
                when = case.get("when", {})
                match = True
                if "type" in when and when["type"] != last_resp.get("type"):
                    match = False

                if "contains" in when:
                    if when["contains"] not in last_resp.get("text", ""):
                        match = False

                if "not_contains" in when:
                    if when["not_contains"] in last_resp.get("text", ""):
                        match = False

                if match:
                    matched = True
                    for sub_step in case.get("steps", []):
                        await self.run(sub_step, context)
                    break
            if not matched:
                raise ValueError("branch 未匹配到任何 case")

        elif action == "error":
            message = render_template(step.get("message", "执行发生错误"), render_context)
            raise RuntimeError(message)
        else:
            raise ValueError(f"未知 action: {action}")

    def _build_render_context(self, context: dict) -> dict:
        render_context = {
            **context,
            **context.get("extractedData", {}),
            "extractedData": context.get("extractedData", {}),
        }
        last_response = context.get("lastResponse") or context.get("last_response")
        if last_response:
            render_context.update(last_response)
            render_context["lastResponse"] = last_response
            render_context["last_response"] = last_response
        return render_context

    def _ensure_extension(self, filename: str, ext: str | None) -> str:
        if not ext:
            return filename
        normalized_ext = ext.lstrip(".")
        if filename.lower().endswith(f".{normalized_ext.lower()}"):
            return filename
        return f"{filename}.{normalized_ext}"

    def _select_button(
        self,
        step: dict,
        context: dict,
        render_context: dict,
        buttons: list[list[dict]],
    ) -> dict:
        pick = context.get("pick")
        if pick is not None:
            try:
                pick_index = int(pick)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid pick value: {pick}") from error

            if pick_index <= 0:
                raise ValueError(f"Pick must be greater than 0, got {pick_index}")

            flat_buttons = [button for row in buttons for button in row]
            target_text = str(pick_index)
            for button in flat_buttons:
                if button.get("text") == target_text:
                    return button

            flat_index = pick_index - 1
            if 0 <= flat_index < len(flat_buttons):
                return flat_buttons[flat_index]

            raise ValueError(f"Could not find button number {pick_index}")

        query = step.get("query", context.get("query"))
        if query:
            query = render_template(query, render_context)

        return self.selector.select(
            buttons,
            strategy=step["strategy"],
            query=query,
            response_text=context["lastResponse"].get("text", ""),
        )
