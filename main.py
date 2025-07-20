import os
import streamlit as st
from dotenv import load_dotenv
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAI, OpenAIEmbeddings

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

st.title("URLyzer: News Research Tool 📈")
st.sidebar.title("News Article URLs")

# Input: Up to 3 URLs
urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i+1}")
    if url.strip():
        urls.append(url.strip())

process_url_clicked = st.sidebar.button("Process URLs")
index_dir = "faiss_index"  # Folder to store FAISS index

main_placeholder = st.empty()

# Initialize LLM
llm = OpenAI(temperature=0.9, max_tokens=500)

if process_url_clicked:
    if not urls:
        st.warning("Please enter at least one valid URL.")
    else:
        try:
            # Load data from URLs
            loader = UnstructuredURLLoader(urls=urls)
            main_placeholder.text("🔄 Loading data from URLs...")
            data = loader.load()

            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                separators=['\n\n', '\n', '.', ','],
                chunk_size=1000
            )
            main_placeholder.text("🔄 Splitting text into chunks...")
            docs = text_splitter.split_documents(data)

            # Generate embeddings and build FAISS index
            embeddings = OpenAIEmbeddings()
            vectorstore_openai = FAISS.from_documents(docs, embeddings)
            main_placeholder.text("🔄 Building FAISS index...")

            # Save index locally
            vectorstore_openai.save_local(index_dir)
            st.success("✅ URL processing complete!")
        except Exception as e:
            st.error(f"Processing failed: {str(e)}")

# User query input
query = main_placeholder.text_input("Ask a question about the content:")

if query:
    if os.path.exists(index_dir):
        try:
            # Load FAISS index with safe deserialization enabled
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.load_local(
                index_dir,
                embeddings,
                allow_dangerous_deserialization=True  # ✅ Important fix
            )

            # Run RetrievalQA chain
            chain = RetrievalQAWithSourcesChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever()
            )
            result = chain({"question": query}, return_only_outputs=True)

            # Display answer
            st.header("Answer")
            st.write(result.get("answer", "No answer found."))

            # Display sources
            sources = result.get("sources", "")
            if sources:
                st.subheader("Sources:")
                for source in sources.split("\n"):
                    st.write(source)
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
    else:
        st.error("⚠️ No index found. Please process URLs first.")
