import datetime
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import openai
import sys

from langchain import ConversationChain, LLMChain
from langchain.agents import initialize_agent, load_tools, Tool
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from openai.error import (AuthenticationError, InvalidRequestError,
                          RateLimitError)
from tools.rfpio import RFPIO

log = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = "9ded0c35cb5f9933a84c7bb93ee17514de7bd01582c5a111474f464e35631623"

MAX_TOKENS = 512
TOOLS = ["serpapi", "llm-math"]

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["original_words", "num_words", "translate_to"],
    template="Restate {num_words}{translate_to}the following: \n{original_words}\n",
)


def load_chain(tools_name, llm, agent="zero-shot-react-description", verbose=False):
    chain = None
    express_chain = None
    if llm:
        log.info("\ntools_list:", tools_name)
        tools = load_tools(tools_name, llm)
        tools.append(RFPIO())

        # memory = ConversationBufferMemory(memory_key="chat_history")

        chain = initialize_agent(tools, llm, agent=agent, verbose=verbose)
        express_chain = LLMChain(
            llm=llm, prompt=PROMPT_TEMPLATE, verbose=verbose)

    return chain, express_chain


def transform_text(desc, express_chain, num_words=0, translate_to=""):
    num_words_prompt = ""
    if num_words and int(num_words) != 0:
        num_words_prompt = "using up to " + str(num_words) + " words, "

    translate_to_str = ""
    if translate_to != "":
        if translate_to == "auto":
            translate_to = get_language(desc)
        translate_to_str = "translated to " + translate_to + ", "

    trans_instr = num_words_prompt + translate_to_str
    if express_chain and len(trans_instr.strip()) > 0:
        generated_text = express_chain.run(
            {'original_words': desc, 'num_words': num_words_prompt,
             'translate_to': translate_to_str}).strip()
    else:
        log.info("Not transforming text")
        generated_text = desc

    return generated_text


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


def question(input: str, product: str = ""):
    llm = OpenAI(temperature=0, max_tokens=MAX_TOKENS, client=None)
    chain, express_chain = load_chain(TOOLS, llm, verbose=True)

    if chain:
        output = run_chain(chain, input)
        transformed_output = transform_text(
            output, express_chain, num_words=200, translate_to="french")
        return transformed_output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a query")
        sys.exit(1)

    query = sys.argv[1]
    print(question(query))
