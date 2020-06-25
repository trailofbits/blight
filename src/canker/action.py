import canker.tool


class Action:
    def __init__(self, config):
        self._config = config

    def _should_run_on(self, tool):
        return True

    def before_run(self, tool):
        pass

    def _before_run(self, tool):
        if self._should_run_on(tool):
            self.before_run(tool)

    def after_run(self, tool):
        pass

    def _after_run(self, tool):
        if self._should_run_on(tool):
            self.after_run(tool)


class CCAction(Action):
    def _should_run_on(self, tool):
        return isinstance(tool, canker.tool.CC)


class CXXAction(Action):
    def _should_run_on(self, tool):
        return isinstance(tool, canker.tool.CXX)


class CompilerAction(CCAction, CXXAction):
    def _should_run_on(self, tool):
        return isinstance(tool, canker.tool.CC) or isinstance(tool, canker.tool.CXX)


class CPPAction(Action):
    def _should_run_on(self, tool):
        return isinstance(tool, canker.tool.CPP)


class LDAction(Action):
    def _should_run_on(self, tool):
        return isinstance(tool, canker.tool.LD)


class ASAction(Action):
    def _should_run_on(self, tool):
        return isinstance(tool, canker.tool.AS)
