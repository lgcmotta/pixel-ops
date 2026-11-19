from pixel_ops.data_sources.codex_account import CodexAccountSource
from pixel_ops.events.observation_sources import ObservationEventSource
from pixel_ops.integration_plugins.base import IntegrationContribution


class CodexAccountIntegrationPlugin:
    name = "codex_account"

    def enabled(self, ctx):
        return ctx.plugin_enabled(self.name, "PIXEL_OPS_CODEX_ACCOUNT_ENABLED", False)

    def build(self, ctx):
        cfg = ctx.plugin_config(self.name)
        source = CodexAccountSource(**{key: cfg[key] for key in ("account_home", "executable", "poll_seconds", "timeout_seconds", "stale_seconds") if key in cfg})
        return IntegrationContribution(event_sources=[ObservationEventSource("ai.quota_updated", self.name, source)], closers=[source.close])


def plugin():
    return CodexAccountIntegrationPlugin()
