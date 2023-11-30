import boto3
from llama_index import download_loader
import nbib
from llama_index.vector_stores import PineconeVectorStore
from llama_index.storage.storage_context import StorageContext
import pinecone
import os
from dotenv import load_dotenv
from awsutils import bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain.vectorstores import Pinecone


load_dotenv()
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_PROFILE"] = "default"

client = boto3.client("s3")
S3Reader = download_loader("S3Reader")


bucket = "ncbi-safetyandhealth-nbib"
key = "PMC10024226.nbib"
pinecone_key = os.getenv("PINECONE_API_KEY")
index_name = "ncbi-safetyandhealth-abstracts"

# paginator = client.get_paginator('list_objects')
# page_iterator = paginator.paginate(Bucket=bucket)
# for page in page_iterator:
#     for obj in page['Contents']:
#         loader = S3Reader(bucket=bucket, key=f"{obj['Key']}")
#         print(f"Loading {obj['Key']}")
#         documents = loader.load_data()

loader = S3Reader(bucket=bucket, key=key)
documents = loader.load_data()
refs = nbib.read(documents[0].text)
ref_abstract = refs[0]["abstract"]


pinecone.init(api_key=pinecone_key,
              environment="gcp-starter")


# pinecone.create_index("ncbi-safetyandhealth-abstracts", dimension=1536,
#                       metric="cosine", pod_type="Starter")

pinecone_index = pinecone.Index("ncib-safetyandhealth-abstracts")


vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)


bedrock_client = bedrock.get_bedrock_client(assumed_role=os.environ.get(
    "BEDROCK_ASSUME_ROLE", None), region=os.environ.get("AWS_DEFAULT_REGION", None))

bedrock_embeddings = BedrockEmbeddings(
    client=bedrock_client, region_name="us-east-1", model_id="amazon.titan-embed-text-v1"
)

docsearch = Pinecone.from_texts(
    [ref_abstract],
    bedrock_embeddings,
    index_name=index_name
)
