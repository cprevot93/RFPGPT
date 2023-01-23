import datetime
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain import ConversationChain, LLMChain
from langchain.agents import initialize_agent, load_tools
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from openai.error import (AuthenticationError, InvalidRequestError,
                          RateLimitError)

os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = "9ded0c35cb5f9933a84c7bb93ee17514de7bd01582c5a111474f464e35631623"

MAX_TOKENS = 512

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["original_words", "num_words", "translate_to"],
    template="Restate {num_words}{translate_to}the following: \n{original_words}\n",
)
TRANSLATE_TO_DEFAULT = "N/A"


def load_chain(tools_list, llm, agent="zero-shot-react-description"):
    chain = None
    express_chain = None
    if llm:
        print("\ntools_list", tools_list)
        tool_names = tools_list
        tools = load_tools(tool_names, llm=llm)

        memory = ConversationBufferMemory(memory_key="chat_history")

        chain = initialize_agent(
            tools, llm, agent=agent, verbose=True, memory=memory)
        express_chain = LLMChain(llm=llm, prompt=PROMPT_TEMPLATE, verbose=True)

    return chain, express_chain


def transform_text(desc, express_chain, num_words=0, translate_to=""):
    num_words_prompt = ""
    if num_words and int(num_words) != 0:
        num_words_prompt = "using up to " + str(num_words) + " words, "

    translate_to_str = ""
    if translate_to != "":
        translate_to_str = "translated to " + translate_to + ", "

    formatted_prompt = PROMPT_TEMPLATE.format(
        original_words=desc,
        num_words=num_words_prompt,
        translate_to=translate_to_str
    )

    trans_instr = num_words_prompt + translate_to_str
    if express_chain and len(trans_instr.strip()) > 0:
        generated_text = express_chain.run(
            {'original_words': desc, 'num_words': num_words_prompt,
             'translate_to': translate_to_str}).strip()
    else:
        print("Not transforming text")
        generated_text = desc

    # replace all newlines with <br> in generated_text
    # generated_text = generated_text.replace("\n", "\n\n")

    prompt_plus_generated = "GPT prompt: " + \
        formatted_prompt + "\n" + generated_text

    print("prompt_plus_generated: " + prompt_plus_generated)

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


def main():
    llm = OpenAI(temperature=0, max_tokens=MAX_TOKENS)
    chain, express_chain = load_chain(["serpapi"], llm)

    if chain:
        output = run_chain(chain, "What is the weather in New York?")
        transformed_output = transform_text(
            output, express_chain, translate_to="French")

        # print transformed_output
        # print(transformed_output)


if __name__ == "__main__":
    main()
