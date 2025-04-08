from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader


from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from flask import Flask, request, jsonify



from flask_cors import CORS


# Initialize the embedding model
embedding = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')


def preprocess_pdf(path, embedding, text_splitter, vector_store_path="faiss_index"):
    """
    Process a PDF file and add it to a single FAISS vector store.
    
    Args:
        path (str): Path to the PDF file
        embedding: Embedding model to use
        text_splitter: Text splitter instance
        vector_store_path (str): Path where the vector store is saved
        
    Returns:
        FAISS: The updated vector store containing all documents
    """
    
    pdf_loader = PyPDFLoader(path)
    pdf_documents = pdf_loader.load()
    chunks = text_splitter.split_documents(pdf_documents)
    
    
    import os
    filename = os.path.basename(path)
    for chunk in chunks:
        chunk.metadata["source"] = filename
    
    
    import os
    if os.path.exists(vector_store_path):
        
        from langchain_community.vectorstores import FAISS
        vectorstore = FAISS.load_local(vector_store_path, embedding,allow_dangerous_deserialization=True)
       
        vectorstore.add_documents(chunks)
    else:
        
        from langchain_community.vectorstores import FAISS
        vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=embedding
        )
    
    
    vectorstore.save_local(vector_store_path)
    
    return vectorstore
vectorstore = FAISS.load_local("faiss_index", embedding,allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(
    search_type="similarity",  
    search_kwargs={"k": 15}    
)


from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import AIMessage, HumanMessage
from huggingface_hub import InferenceClient
from pydantic import PrivateAttr


class HFInferenceLLM(SimpleChatModel):
    model_name: str
    api_key: str
    provider: str = "nebius"

    
    _client: InferenceClient = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = InferenceClient(provider=self.provider, api_key=self.api_key)

    def _call(self, messages, **kwargs):
        hf_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                hf_messages.append({"role": "user", "content": [{"type": "text", "text": msg.content}]})
            elif isinstance(msg, AIMessage):
                hf_messages.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})

        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=hf_messages,
            max_tokens=kwargs.get("max_tokens", 500)
        )

        return completion.choices[0].message["content"]

    @property
    def _llm_type(self) -> str:
        return "hf-inference-client"

llm = HFInferenceLLM(
    model_name="Qwen/QwQ-32B",
    api_key=""
)
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnableLambda

# 1. Load LLM
# llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# 2. Prompt template with expected variables: 'context' and 'question'
prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Answer the question based only on the following context:

Context:
{context}

Question: {question}

Answer the question using only the provided context. If the answer is not in the context, say "I don't have enough information to answer this question."
""")

# 3. Create the document answering chain (stuff method)
document_chain = create_stuff_documents_chain(llm, prompt)

# 4. Connect retriever (assuming you already have a retriever object)
# Example: retriever = vectorstore.as_retriever()
custom_retriever_chain = RunnableLambda(lambda x: x["question"]) | retriever
# retriever_chain = retriever

rag_chain = create_retrieval_chain(
    retriever=custom_retriever_chain,
    combine_docs_chain=document_chain
)
# rag_chain = create_retrieval_chain(retriever, document_chain)

# 5. Question answering function
def ask_question(question):
    response = rag_chain.invoke({"question": question})
    return {
        "answer": response["answer"],
        "source_documents": response.get("context", [])  # Optional: shows what was retrieved
    }


app = Flask(__name__)
CORS(app)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Missing 'question' in request"}), 400

    try:
        print(f" Received question: {question}")  

        response = rag_chain.invoke({"question": question})
        sources = [doc.page_content for doc in response.get("context", [])]

        print(f" Answer: {response['answer']}")  
        return jsonify({
            "answer": response["answer"],
            "sources": sources
        })
    except Exception as e:
        print(f"Error while answering: {str(e)}") 
        return jsonify({"error": str(e)}), 500



@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "RAG API is running. POST to /ask with a question."})

# -----------------------------
# Run Server
# -----------------------------
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))  
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Optionally process it immediately
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        preprocess_pdf(filepath, embedding, text_splitter)

        return jsonify({"message": "File uploaded and processed successfully."}), 200
    else:
        return jsonify({"error": "Only PDF files are allowed."}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
