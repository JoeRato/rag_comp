import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

def question_re_engineer(llm, question): 
    """Take a user questions and returns the question a reworded version of the question and
    four close questions in extend to ensure relevant chunks retrieval"""
        
    prompt_template = ChatPromptTemplate.from_template("""Tu es un assisant dans le domaine de la conformité financière.
                                                       propose quatre questions pertinentes qui couvrent des sujets proches de la question suivante. 
                                                       Utilise si possible des synonymes.
                                                       Voici la question : {question}
                                                         """)
    
    chain = (
    {"question": RunnablePassthrough()} 
    | prompt_template
    | llm
    | StrOutputParser()
    )
    
    return f'0. {question}\n {chain.invoke(question)}'


def vector_db_search(db_path, question, embedding, search_type='mmr', k=10, score_threshold=0.5):
    """Perform a simple similarity search based on a question in a Chroma Vector DB"""
    
    db = Chroma(persist_directory=db_path, embedding_function=embedding)
    
    retriever = db.as_retriever(search_type=search_type,
                                search_kwargs={"k": k,
                                               "score_threshold": score_threshold,
                                               #"filter": {"type": "acpr_sanc"}
                                               } 
                                )
    
    return retriever.get_relevant_documents(question)

def answer_generation(question, docs, llm):
    """Generate an answer based on a question and a list of relevants docs"""
    
    prompt_template = ChatPromptTemplate.from_template("""Tu es un assistant specialisé dans la conformité financière. 
                                          Réponse à la question posée en utilisant uniquement les éléments de contexte.
                                          Si la réponse ne se trouve pas dans le contexte, dis juste que tu ne sais pas. 
                                          Assure toi de ne donner chaque information qu'une seule fois et de répondre précisemment. 
                                          Utilise cinq phrases maximum et garde les réponse courte.
                                          Question: {question}
                                          Context: {context}
                                          Réponse:""")
    
    formatted_docs = "\n\n".join([doc.page_content for doc in docs])
    
    chain = (
        {"context": lambda x: formatted_docs, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
        )
    
    return chain.invoke(question)

def open_ai_acpr_rag(db_path, question):
    
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=os.environ['OPENAI_API_KEY'])
    embedding = OpenAIEmbeddings()
    
    question_v2 = question_re_engineer(llm, question)
    docs= vector_db_search(db_path, question_v2, embedding)
    answer = answer_generation(question, docs, llm)
    
    return answer
    


    
