from vertexai import rag
import vertexai

# TODO(developer): Update and un-comment below lines
PROJECT_ID = "bright-meridian-470215-h2"
display_name = "test_corpus"
description = "Corpus Description"

# Initialize Vertex AI API once per session
vertexai.init(project=PROJECT_ID, location="us-east4")

# Configure backend_config
backend_config = rag.RagVectorDbConfig(
    rag_embedding_model_config=rag.RagEmbeddingModelConfig(
        vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
            publisher_model="publishers/google/models/text-embedding-005"
        )
    )
)

corpus = rag.create_corpus(
    display_name=display_name,
    description=description,
    backend_config=backend_config,
)
print(corpus)
# Example response:
# RagCorpus(name='projects/1234567890/locations/us-central1/ragCorpora/1234567890',
# display_name='test_corpus', description='Corpus Description', embedding_model_config=...
# ...
