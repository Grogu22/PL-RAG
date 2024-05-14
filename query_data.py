import argparse
from operator import itemgetter
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from env import openai_api_key
from paths import CHROMA_PATH
import os

os.environ['OPENAI_API_KEY'] = openai_api_key

promptsring = """
Answer the questions based only on the following context:
{context}
--------------------------------------------------------------------
Based on the above context, answer the following question : {question}
"""

def query(MODEL="gpt-4-turbo"):
    # Preparing CLI parser 
    parser = argparse.ArgumentParser()
    parser.add_argument("query_", type=str, help="Query text")
    args = parser.parse_args()
    query_text = args.query_

    # Preparing DB
    embedding_func = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_func)

    # Searching DB...
    results = db.similarity_search_with_relevance_scores(query_text, k = 4)
    #print(results)

    # The top 4 cosine similarity scores are returned, highest to lowest
    # If we notice a highest score less than 0.75, we will automatically discard all results
    if len(results) == 0 or results[0][1] < 0.75:
        print("Unable to find relevant results !!")
        return
    
    context_text = "\n----------------------\n".join([doc.page_content for doc, score in results])
    # print(context_text)
    prompt = PromptTemplate(
        template=promptsring,
        input_variables=["context", "question"]
    )

    # CHAIN
    model = ChatOpenAI(model_name=MODEL, temperature=0)
    str_output_parser = StrOutputParser()
    chain = (
        {"context": itemgetter("context"), "question": itemgetter("question")}
        | prompt
        | model
        | str_output_parser
    )

    chain_output = chain.invoke({"context": context_text, "question": query_text})
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    response_text = f"----------------------------\nResponse : {chain_output} \nSources: {sources} \n--------------------------"
    print(response_text)

if __name__ == "__main__":
    query()