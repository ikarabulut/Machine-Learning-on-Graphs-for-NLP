import os
from dotenv import load_dotenv
from awsutils import bedrock

from llama_index import VectorStoreIndex
from llama_index.vector_stores import PineconeVectorStore
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.indices.postprocessor import MetadataReplacementPostProcessor
from llama_index.indices.postprocessor import SentenceTransformerRerank


from langchain.llms import Bedrock
from langchain.embeddings import BedrockEmbeddings

import pinecone


load_dotenv()
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_PROFILE"] = "default"

pinecone_key = os.getenv("PINECONE_API_KEY")
index_name = "ncbi-safetyandhealth-pdfs"


pinecone.init(api_key=pinecone_key,
              environment="gcp-starter")
pinecone_index = pinecone.Index(index_name)

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

vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

service_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model=bedrock_embedding
)

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store, service_context=service_context)


def get_sentence_window_query_engine(
    sentence_index, similarity_top_k=6, rerank_top_n=2
):
    # define postprocessors
    postproc = MetadataReplacementPostProcessor(target_metadata_key="window")
    rerank = SentenceTransformerRerank(
        top_n=rerank_top_n, model="BAAI/bge-reranker-base"
    )

    sentence_window_engine = sentence_index.as_query_engine(
        similarity_top_k=similarity_top_k, node_postprocessors=[
            postproc, rerank]
    )
    return sentence_window_engine


sentence_query_engine = get_sentence_window_query_engine(sentence_index=index)

response = sentence_query_engine.query(
    "What are steps to take to avoid electrocution fatalities?"
)

print(str(response))
