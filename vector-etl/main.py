import boto3
from llama_index import download_loader
import nbib
from llama_index.vector_stores import PineconeVectorStore
import pinecone
import os
from dotenv import load_dotenv


load_dotenv()

client = boto3.client("s3")
S3Reader = download_loader("S3Reader")


bucket = "ncbi-safetyandhealth-nbib"
key = "PMC10024226.nbib"
pinecone_key = os.getenv['PINECONE_API_KEY']

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

try:
    pinecone.create_index("ncib-safetyandhealth-abstracts", dimension=1536,
                          metric="cosine", pod_type="Starter")
except Exception:
    pass
pinecone_index = pinecone.Index("ncib-safetyandhealth-abstracts")
