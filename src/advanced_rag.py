import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class AdvancedRAG:
    """Clean + Working RAG system (no deprecated LangChain APIs)"""

    def __init__(self, documents_path):
        # Embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        # Vector DB
        self.vector_store = self._setup_vector_store(documents_path)

        # Chain
        self.qa_chain = self._setup_chain()

    # =========================
    # LOAD + INDEX DOCUMENTS
    # =========================
    def _setup_vector_store(self, documents_path):
        loader = DirectoryLoader(
            documents_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )

        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_documents(documents)

        vector_store = FAISS.from_documents(chunks, self.embeddings)
        return vector_store

    # =========================
    # CREATE RAG CHAIN
    # =========================
    def _setup_chain(self):

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert AI assistant. Use only the provided context to answer."),
            ("human",
             "Context:\n{context}\n\nQuestion:\n{question}")
        ])

        def format_docs(docs):
            return "\n\n".join([d.page_content for d in docs])

        chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
        )

        return chain

    # =========================
    # QUERY FUNCTION
    # =========================
    def query(self, question):
        response = self.qa_chain.invoke(question)

        return {
            "answer": response.content
        }


# =========================
# RUN TEST
# =========================
if __name__ == "__main__":

    # 🔑 Make sure API key is set:
    # setx OPENAI_API_KEY "your-key"

    rag = AdvancedRAG("data/knowledge_base")

    print("\n🚀 Advanced RAG Ready\n")

    while True:
        q = input("\nAsk question (or type exit): ")

        if q.lower() == "exit":
            break

        result = rag.query(q)
        print("\n🤖 Answer:\n", result["answer"])