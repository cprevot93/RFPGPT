import argparse
import os
import logging
from typing import Type

from langchain.document_loaders import UnstructuredPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import VectorDBQAWithSourcesChain
from langchain import OpenAI

log = logging.getLogger()

os.environ["OPENAI_API_KEY"] = "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"
PERSIST_DIRECTORY = 'db'


def embed_document(file: str, embeddings) -> Chroma:
    """
    Index a document with embeddings and save it to a Chroma DB.
    """
    docs = []
    metadatas = []

    if file:
        # files = glob.glob("pdfs/*.pdf")
        # for f in files:

        print(f"Parsing {file}")
        loader = UnstructuredPDFLoader(file)
        documents = loader.load()

        # We do this due to the context limits of the LLMs.
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, length_function=len)
        texts = text_splitter.split_documents(documents)
        docs.extend(texts)
        metadatas = [{"source": f"{file}-{i}-pl"} for i in range(len(texts))]

    # Here we create a vector store from the documents and save it to disk.
    docsearch = Chroma.from_documents(docs, embeddings, persist_directory=PERSIST_DIRECTORY, metadatas=metadatas)
    docsearch.persist()
    return docsearch


def main(query: str = "", file: str = ""):
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    docsearch = None
    embeddings = OpenAIEmbeddings(client=None)
    if file:
        docsearch = embed_document(file, embeddings=embeddings)
    if query:
        if docsearch is None:
            # Now we can load the persisted database from disk, and use it as normal.
            try:
                docsearch = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)
            except Exception:
                log.error("Error:", exc_info=True)
                return

        # search query in documents
        chain = VectorDBQAWithSourcesChain.from_chain_type(
            OpenAI(client=None, temperature=0), chain_type="stuff", vectorstore=docsearch)
        output = chain({"question": query}, return_only_outputs=True)
        print(bcolors.WARNING + "Answer:", output['answer'] + bcolors.ENDC)


if __name__ == "__main__":

    # arvg parsing with argparse
    import argparse
    parser = argparse.ArgumentParser(
        prog='FortiGPT PDF',
        description='Fortinet pre-sales assistant',
    )
    parser.add_argument("-q", "--query", type=str, help='Query to search for')
    parser.add_argument("-f", "--file", type=str, help='Select a file to parsing.')
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
    parser.add_argument("-vv", "--debug", action='store_true', help="Verbose mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode")
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    main(args.query, args.file)
