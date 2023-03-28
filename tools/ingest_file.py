import argparse
import logging
import os
import re
from typing import Any, Dict, Union, Tuple, Type
from colorama import Fore

from chromadb import errors as chromadb_errors
import requests
from langchain import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.document_loaders import PyMuPDFLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

log = logging.getLogger()

os.environ["OPENAI_API_KEY"] = "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"
PERSIST_DIRECTORY = 'db'
EMBEDDINGS = OpenAIEmbeddings(client=None)
DOCUMENTS_FOLDER = "documents"


def _loader(file: str) -> Tuple[Any, str]:
    """
    Lookup for file extension and return the correct loader.
    :param file: file to load
    :return: loader
    """
    if file.endswith(".pdf"):
        return PyMuPDFLoader(file), "pdf"
    elif file.endswith(".csv"):
        return CSVLoader(file), "csv"
    else:
        raise ValueError(f"File {file} has an unsupported extension.")


def ingest_file(file: str, filename: str, collection_name: str = "langchain") -> Union[Chroma, None]:
    """
    Index a document with embeddings and save it to a Chroma DB.
    :param file: file to ingest. Can be a path on the filesystem or an URL.
    :param collection_name: name of the collection to ingest the file into.
    :return: Chroma DB
    """
    docs = []
    metadatas = []

    pattern = re.compile(r'^https?:\/{2}([\d\w-]+(?:\.[\d\w-]+)*)(?:\/[^\s/]*)*\/([^\s]*.pdf)$')
    if re.match(pattern, file):
        url = file
        regex_search = re.search(pattern, file)
        fqdn = str(regex_search.group(1))
        if filename is None:
            filename = str(regex_search.group(2))
        file = os.path.join(DOCUMENTS_FOLDER, filename)
        if os.path.exists(file):
            log.info(f"File {file} already exists, skipping download.")
        else:
            log.info(f"Downloading {filename} from {fqdn}")
            try:
                result = requests.get(url, stream=True, timeout=10)
                with open(file, 'wb') as fd:
                    for chunk in result.iter_content(chunk_size=512):
                        fd.write(chunk)
            except Exception:
                log.error("ERROR while download file %s:\n", file, exc_info=True)
                return None

    if file:
        if filename is None:
            filename = os.path.basename(file)

        log.info("Parsing %s", file)
        loader, document_type = _loader(file)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, length_function=len)
        texts = loader.load_and_split(text_splitter)

        log.debug("Splitted %s:\n%d", file, texts)

        docs.extend(texts)
        if document_type == "pdf":
            metadatas = [{"source": f"{filename}-{i}-pl"} for i in range(len(texts))]

    # Here we create a vector store from the documents and save it to disk.
    if collection_name is None:
        collection_name = "langchain"
    docsearch = Chroma.from_documents(docs, EMBEDDINGS, persist_directory=PERSIST_DIRECTORY,
                                      metadatas=metadatas, collection_name=collection_name)
    docsearch.persist()
    return docsearch


def search_file(query: str,
                collection_name: str = "langchain",
                qa_response: bool = False,
                with_sources: bool = False,
                model_name="text-davinci-003",
                verbose: bool = False
                ):
    """
    Search a query in a document.
    """
    try:
        # Now we can load the persisted database from disk, and use it as normal.
        docsearch = Chroma(persist_directory=PERSIST_DIRECTORY,
                           embedding_function=EMBEDDINGS, collection_name=collection_name)

        # search query in documents with qa
        if qa_response:
            chain = RetrievalQAWithSourcesChain.from_chain_type(
                OpenAI(client=None, temperature=0, model_name=model_name), chain_type="stuff", retriever=docsearch.as_retriever())
            return chain({"question": query}, return_only_outputs=not verbose)
        else:
            return docsearch.similarity_search_with_score(query)
    except chromadb_errors.NoIndexException:
        log.info("No index found in collection %s.", collection_name)
        return {}
    except Exception as exp:
        log.error("Error:", exc_info=True)
        return {}


def main(query: str = "", file: str = "", collection_name: str = "langchain", verbose: bool = False) -> Dict[str, Any]:
    """
    Ingest file and search query in a ChromaDB
    """
    # ingest file
    if file:
        ingest_file(file, collection_name)

    # search query
    if query:
        return search_file(query, collection_name, verbose=verbose)
    return {}


if __name__ == "__main__":
    # arvg parsing with argparse
    import argparse

    parser = argparse.ArgumentParser(
        prog='FortiGPT PDF',
        description='Fortinet pre-sales assistant',
    )
    parser.add_argument("-q", "--query", type=str, help='Query to search for')
    parser.add_argument("-f", "--file", type=str, help='Select a file to parsing.')
    parser.add_argument("-c", "--collection", type=str,
                        help='Select a collection to ingest file in or search query in.')
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
    parser.add_argument("-vv", "--debug", action='store_true', help="Verbose mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode")
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    collection = args.collection if args.collection else "langchain"
    output = main(args.query, args.file, collection)
    if output:
        print(Fore.YELLOW + "Answer:", output['answer'], "\nSources:", output["sources"])
