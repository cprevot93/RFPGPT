import logging
import os

import openai
# from typing import Any, Dict, List, Optional, Tuple, Union
from colorama import Fore
from langchain.agents import AgentExecutor, load_tools
from langchain.agents.conversational_chat.base import ConversationalChatAgent
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
# from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from openai.error import (AuthenticationError, InvalidRequestError,
                          RateLimitError)

from tools import RFPIO, FortiDocs, ingest_file
from tools.custom_agent import ConversationalChatAgentContext

log = logging.getLogger()

os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = "9ded0c35cb5f9933a84c7bb93ee17514de7bd01582c5a111474f464e35631623"

MAX_TOKENS = 512
TOOLS = ["serpapi"]
LLM_TOOLS = ["llm-math"]

SYSTEM_PROMPT = "Assistant is a helpful pre-sales network & security engineer assistant, working for Fortinet. Assistant use english technical terms in any language like 'MSSP' or 'VNP'. Assistant MUST reply in the same language as the question."


def load_agent(tools_name, chat_llm, verbose=False):
    tools = load_tools(tools_name)
    tools.append(RFPIO())
    tools.append(FortiDocs())
    log.info("\ntools_list: %s", [t.name for t in tools])

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    qa_agent = ConversationalChatAgentContext.from_llm_and_tools(
        chat_llm, tools, memory=memory, system_message=SYSTEM_PROMPT)

    return AgentExecutor.from_agent_and_tools(agent=qa_agent, tools=tools, verbose=verbose, memory=memory)


def run_chain(chain, inp):
    output = ""
    error_msg = ""
    try:
        output = chain.run(input=inp)
    except AuthenticationError as ae:
        error_msg = "AuthenticationError: " + str(ae)
    except RateLimitError as rle:
        error_msg = "\nRateLimitError: " + str(rle)
    except ValueError as ve:
        error_msg = "\nValueError: " + str(ve)
    except InvalidRequestError as ire:
        error_msg = "\nInvalidRequestError: " + str(ire)
    except Exception as e:
        error_msg = f"\nError: {e}\n"

    if error_msg != "":
        return error_msg
    return output


def get_language(text: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    lang = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"In one word, what's the language of the following: '{input}'?"},
        ]
    )
    return lang["choices"][0]["message"]["content"].strip().replace(".", "").replace("\n", "")


def chat(user_input: str, verbose: bool = False, interactive: bool = False):
    """
    Entry point for the FortiGPT assistant
    """
    chat_llm = ChatOpenAI(client=None, model_kwargs={"temperature": 0}, model_name="gpt-3.5-turbo")
    agent_chain = load_agent(TOOLS, chat_llm, verbose=verbose)

    if agent_chain:
        if interactive:
            print("\nWelcome to FortiGPT, your pre-sales assistant! How can I help you?")
            print("Type 'exit' to quit.")
            while True:
                user_input = input("> ")
                if user_input == "exit":
                    break
                elif user_input == "help":
                    print("Type 'exit' to quit.")
                elif user_input.strip() != "":
                    output = run_chain(agent_chain, user_input)
                    print(Fore.YELLOW + "FortiGPT: " + output + Fore.RESET)
                else:
                    continue
        else:
            output = run_chain(agent_chain, user_input)
            if not args.verbose or not args.debug:
                print(output)


if __name__ == "__main__":
    # arvg parsing with argparse
    import argparse
    parser = argparse.ArgumentParser(
        prog='FortiGPT',
        description='Fortinet pre-sales assistant',
    )
    parser.add_argument("-q", "--query", type=str, help="Query to search for")
    parser.add_argument("-n", "--filename", type=str, help="Filename for ingest file")
    parser.add_argument("-i", "--ingest", type=str, help="Ingest a file")
    parser.add_argument("-c", "--collection", type=str, help="Ingest a file to a specific collection")
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
    parser.add_argument("-vv", "--debug", action='store_true', help="Verbose mode")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.ingest:
        ingest_file(args.ingest, args.filename, args.collection)
        exit(0)

    if args.query:
        chat(args.query, verbose=(args.verbose or args.debug))
    else:
        # interactive mode
        chat(args.query, verbose=(args.verbose or args.debug), interactive=True)
