from typing import Any, Dict, List, Optional, Tuple, Union

from langchain.agents import AgentExecutor
from langchain.output_parsers.base import BaseOutputParser
from langchain.prompts.base import BasePromptTemplate
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    MessagesPlaceholder,
                                    SystemMessagePromptTemplate)
from langchain.schema import (AgentAction, AgentFinish, AIMessage,
                              BaseLanguageModel, BaseMessage, HumanMessage)
from langchain.tools.base import BaseTool


class AgentExecutorContext(AgentExecutor):
    """
    An agent designed to hold a conversation in addition to using tools.
    This agent can ask for context from the user. To ask for context, tools have to return a tuple formed by the tool output and a boolean.
    True means that the tool need more context and the agent will ask for it by outputting directly.
    i-e questions for context are hardcorded in the tool.
    """

    def _take_next_step(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[AgentAction, str]],
    ) -> Union[AgentFinish, Tuple[AgentAction, str]]:
        """
        Take a single step in the thought-action-observation loop.
        """
        # Call the LLM to see what to do.
        output = self.agent.plan(intermediate_steps, **inputs)
        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, AgentFinish):
            return output
        self.callback_manager.on_agent_action(
            output, verbose=self.verbose, color="green"
        )
        # Otherwise we lookup the tool
        if output.tool in name_to_tool_map:
            tool = name_to_tool_map[output.tool]
            return_direct = tool.return_direct
            color = color_mapping[output.tool]
            llm_prefix = "" if return_direct else self.agent.llm_prefix
            # We then call the tool on the tool input to get an observation
            observation, ask_for_context = tool.run(
                output.tool_input,
                verbose=self.verbose,
                color=color,
                llm_prefix=llm_prefix,
                observation_prefix=self.agent.observation_prefix,
            )
            if ask_for_context:
                return AgentFinish({self.agent.return_values[0]: observation}, "Ask the user for more context")
        return output, observation
