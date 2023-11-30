import os
import boto3
from dotenv import load_dotenv
from awsutils import bedrock

from llama_index import ServiceContext, VectorStoreIndex, Document, download_loader
from llama_index.llms import LangChainLLM

from langchain.llms import Bedrock
from langchain.embeddings import BedrockEmbeddings


load_dotenv()
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_PROFILE"] = "default"

bucket = "ncbi-safetyandhealth-pdfs"
key = "pmc/articles/PMC10024166/main.pdf"

S3Reader = download_loader("S3Reader")
client = boto3.client("s3")

loader = S3Reader(bucket=bucket, key=key)

documents = loader.load_data()

document = Document(text="\n\n".join([doc.text for doc in documents]))
print(documents[0])


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

# bedrock_embeddings = BedrockEmbeddings(
#     client=bedrock_client, region_name="us-east-1", model_id="amazon.titan-embed-text-v1"

llm = Bedrock(
    client=bedrock_client,
    model_id=model_id,
    model_kwargs=model_kwargs
)

bedrock_embedding = BedrockEmbeddings(
    client=bedrock_client,
    model_id="amazon.titan-embed-text-v1",
)

service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model=bedrock_embedding)

index = VectorStoreIndex.from_documents([document],
                                        service_context=service_context)

query_engine = index.as_query_engine()

response = query_engine.query(
    "What are steps to take to avoid electrocution fatalities?"
)
print(str(response))
