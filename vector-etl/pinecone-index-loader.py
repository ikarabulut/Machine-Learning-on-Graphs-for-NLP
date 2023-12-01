from llama_index import ServiceContext
from llama_index.node_parser import SentenceWindowNodeParser
import os
import boto3
from dotenv import load_dotenv
from awsutils import bedrock

from llama_index import ServiceContext, VectorStoreIndex, Document, download_loader
from llama_index.vector_stores import PineconeVectorStore
from llama_index.storage.storage_context import StorageContext


from langchain.llms import Bedrock
from langchain.embeddings import BedrockEmbeddings

import pinecone


load_dotenv()
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_PROFILE"] = "default"

bucket = "ncbi-safetyandhealth-pdfs"
pinecone_key = os.getenv("PINECONE_API_KEY")
index_name = "ncbi-safetyandhealth-pdfs"

pinecone.init(api_key=pinecone_key,
              environment="gcp-starter")
pinecone_index = pinecone.Index(index_name)

S3Reader = download_loader("S3Reader")
client = boto3.client("s3")

paginator = client.get_paginator('list_objects')
page_iterator = paginator.paginate(Bucket=bucket)
documents = []
i = 0
for page in page_iterator:
    for obj in page['Contents']:
        loader = S3Reader(bucket=bucket, key=f"{obj['Key']}")
        print(f"Loading {obj['Key']}")
        split_documents = loader.load_data()
        document = Document(text="\n\n".join(
            [doc.text for doc in split_documents]), metadata={"source": f"s3://ncbi-safetyandhealth-pdfs/{obj['Key']}"})
        documents.append(document)
        i = i + 1


vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

model_id = "anthropic.claude-v2"
model_kwargs = {
    "max_tokens_to_sample": 4096,
    "temperature": 0.5,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman:"],
}

bedrock_client = bedrock.get_bedrock_client(assumed_role=os.environ.get(
    "BEDROCK_ASSUME_ROLE", None), region=os.environ.get("AWS_DEFAULT_REGION", None))

llm = Bedrock(
    client=bedrock_client,
    model_id=model_id,
    model_kwargs=model_kwargs
)

bedrock_embedding = BedrockEmbeddings(
    client=bedrock_client,
    model_id="amazon.titan-embed-text-v1",
)

node_parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,
    window_metadata_key="window",
    original_text_metadata_key="original_text",
)

for document in documents:
    nodes = node_parser.get_nodes_from_documents([document])
    print(f"Node created for source:: {nodes[0].metadata['source']}")

sentence_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model=bedrock_embedding,
    node_parser=node_parser,
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

for document in documents:
    print(f"creating embedding for {document.metadata['source']}")
    document_index = VectorStoreIndex.from_documents(
        [document], service_context=sentence_context, storage_context=storage_context
    )
    print(f"embedding created for {document.metadata['source']}")
    i = i - 1
    print(f"{i} embeddings remain")
