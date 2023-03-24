from typing import Any, Dict, List, Optional, Tuple, Union
from langchain.tools import BaseTool
from abc import abstractmethod


class ContextTool(BaseTool):
    """
    Base class for context tools. A context tool is a tool that can ask user for more context directly.
    """

    def run(
        self,
        tool_input: str,
        verbose: Optional[bool] = None,
        start_color: Optional[str] = "green",
        color: Optional[str] = "green",
        **kwargs: Any
    ) -> Tuple[str, bool]:
        """Run the tool."""
        if verbose is None:
            verbose = self.verbose
        self.callback_manager.on_tool_start(
            {"name": self.name, "description": self.description},
            tool_input,
            verbose=verbose,
            color=start_color,
            **kwargs,
        )
        try:
            observation, ask_for_context = self._run(tool_input)
        except (Exception, KeyboardInterrupt) as e:
            self.callback_manager.on_tool_error(e, verbose=verbose)
            raise e
        self.callback_manager.on_tool_end(
            observation, verbose=verbose, color=color, **kwargs
        )
        return observation, ask_for_context

    @abstractmethod
    def _run(self, tool_input: str) -> Tuple[str, bool]:
        """Run the tool."""
        raise NotImplementedError

    @abstractmethod
    def _arun(self, tool_input: str) -> Tuple[str, bool]:
        """Run the tool async."""
        raise NotImplementedError
