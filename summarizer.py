from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Load your full Marathi+English document
with open("sample_input.txt", "r", encoding="utf-8") as f:
    full_text = f.read()

# 2. Split text into chunks (to avoid token limit issues)
splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
docs = splitter.create_documents([full_text])

# 3. Setup GPT-4 model
llm = ChatOpenAI(temperature=0, model_name="gpt-4")

# 4. Load summarization chain (map-reduce)
chain = load_summarize_chain(llm, chain_type="map_reduce")

# 5. Run summarization
summary = chain.run(docs)
print("\nDETAILED SUMMARY:\n", summary)
