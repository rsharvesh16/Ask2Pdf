import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import fitz

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader= PdfReader(pdf)
        for page in pdf_reader.pages:
            text+= page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.4)
    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain(
        {"input_documents":docs, "question": user_question}
        , return_only_outputs=True)

    print(response)
    st.write("Reply: ", response["output_text"])


def get_pdf_text(pdf_docs):
    text = ''
    for pdf_doc in pdf_docs:
        try:
            # Create a BytesIO object from the file content
            file_contents = pdf_doc.read()

            # Use the BytesIO object as the file argument in fitz.open
            document = fitz.open(stream=file_contents, filetype="pdf")

            # Loop through each page and extract the text
            for page in document:
                text += page.get_text()
        except Exception as e:
            text = f"Error reading PDF: {str(e)}"
    return text

def main():
    # HTML/CSS for custom styling
    html_temp = """
    <style>
    .section-header {
        background-color: #F0F0F0;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .section-header2 {
        background-color: #F0F0F0;
        padding: 4px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    </style>
    <div class="section-header">
    <h1 style="color:#333333;text-align:center;">PDF ChatBot</h1>
    </div>
    """
    st.markdown(html_temp, unsafe_allow_html=True)
    st.markdown("<h2 style='color:#F0F0F0;'>Chat With PDFs - Made with Love ❤️ by Sharrr</h2>", unsafe_allow_html=True)

    st.sidebar.header("Menu:")
    pdf_docs = st.sidebar.file_uploader("Upload your PDF Files", accept_multiple_files=True)
    
    if pdf_docs:
        if st.sidebar.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")


    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)

    st.write("If you like my work, Consider")
    image_url = "https://i.etsystatic.com/32289224/r/il/294bb2/3603423963/il_1588xN.3603423963_tuhu.jpg"
    st.markdown(f"<a href='https://www.buymeacoffee.com/rsharvesh16' target='_blank'><img src='{image_url}' width='700'></a>", unsafe_allow_html=True)



if __name__ == "__main__":
    main()