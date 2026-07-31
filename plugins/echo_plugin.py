from moza.plugins.interfaces import ToolInterface


class EchoTool(ToolInterface):
    @property
    def name(self) -> str:
        return "echo_tool"

    @property
    def description(self) -> str:
        return "Echoes back whatever text is provided, for testing the plugin pipeline"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def actions(self) -> list[str]:
        return ["echo"]

    @property
    def is_destructive(self) -> bool:
        return False

    async def execute(self, action: str, args: dict) -> dict:
        return {"success": True, "result": f"Echo: {args.get('text', '')}"}

    async def validate_action(self, action: str, args: dict) -> tuple[bool, str]:
        if action not in self.actions:
            return False, f"Invalid action: {action}"
        return True, ""
