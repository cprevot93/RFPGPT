import re
import json
from typing import Any, Dict, List, Optional, Tuple, Union, Sequence


from langchain.agents.conversational_chat.base import ConversationalChatAgent
from langchain.agents.conversational_chat.prompt import TEMPLATE_TOOL_RESPONSE
from langchain.schema import (
    AgentAction,
    AIMessage,
    BaseLanguageModel,
    BaseMessage,
    BaseOutputParser,
    HumanMessage,
)
from langchain.agents.conversational_chat.prompt import (
    FORMAT_INSTRUCTIONS,
    PREFIX,
    SUFFIX,
    TEMPLATE_TOOL_RESPONSE,
)
from langchain.callbacks.base import BaseCallbackManager
from langchain.chains import LLMChain
from langchain.prompts.base import BasePromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.tools.base import BaseTool

CONTEXT_PATTERN = re.compile(r"^CONTEXT:")


class AgentOutputParser(BaseOutputParser):
    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Any:
        cleaned_output = text.strip()
        if "```json" in cleaned_output:
            _, cleaned_output = cleaned_output.split("```json")
        if "```" in cleaned_output:
            cleaned_output, _ = cleaned_output.split("```")
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[len("```json"):]
        if cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[len("```"):]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[: -len("```")]
        cleaned_output = cleaned_output.strip()
        response = json.loads(cleaned_output)
        return {"action": response["action"], "action_input": response["action_input"]}


class ConversationalChatAgentContext(ConversationalChatAgent):
    """
    An agent designed to hold a conversation in addition to using tools.
    This agent can ask for context from the user. To ask for context, tools have to return a prefix 'CONTEXT:' followed by the context question.
    """
    @property
    def _agent_type(self) -> str:
        raise NotImplementedError

    # @classmethod
    # def create_prompt(
    #     cls,
    #     tools: Sequence[BaseTool],
    #     system_message: str = PREFIX,
    #     human_message: str = SUFFIX,
    #     input_variables: Optional[List[str]] = None,
    #     output_parser: Optional[BaseOutputParser] = None,
    # ) -> BasePromptTemplate:
    #     tool_strings = "\n".join(
    #         [f"> {tool.name}: {tool.description}" for tool in tools]
    #     )
    #     tool_names = ", ".join([tool.name for tool in tools])
    #     _output_parser = output_parser or AgentOutputParser()
    #     format_instructions = human_message.format(
    #         format_instructions=_output_parser.get_format_instructions()
    #     )
    #     final_prompt = format_instructions.format(
    #         tool_names=tool_names, tools=tool_strings
    #     )
    #     if input_variables is None:
    #         input_variables = ["input", "chat_history", "agent_scratchpad"]
    #     messages = [
    #         SystemMessagePromptTemplate.from_template(system_message + "\n\n" + final_prompt),
    #         MessagesPlaceholder(variable_name="chat_history"),
    #         MessagesPlaceholder(variable_name="agent_scratchpad"),
    #     ]
    #     return ChatPromptTemplate(input_variables=input_variables, messages=messages)

    def _construct_scratchpad(
        self, intermediate_steps: List[Tuple[AgentAction, str]]
    ) -> List[BaseMessage]:
        """Construct the scratchpad that lets the agent continue its thought process."""
        thoughts: List[BaseMessage] = []
        for action, observation in intermediate_steps:
            thoughts.append(AIMessage(content=action.log))
            if re.match(CONTEXT_PATTERN, observation):
                # remove the prefix 'CONTEXT:' from the observation
                human_message = HumanMessage(
                    content=re.sub(CONTEXT_PATTERN, "", observation)
                )
            else:
                human_message = HumanMessage(
                    content=TEMPLATE_TOOL_RESPONSE.format(observation=observation)
                )
            thoughts.append(human_message)
        return thoughts
