import sentence_transformers
import torch
import numpy as np

def cosine_similarity(embedding1, embedding2):
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

def test_sentence_transformer():
    print("Testing sentence transformer model...")
    model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded successfully.")
    sentences = ['This framework generates embeddings for each input sentence',
                 'Sentences are passed as a list of string.',
                 'The quick brown fox jumps over the lazy dog.',
                 'the library can create vectors from text.'
                 ]
    sentence_embeddings = model.encode(sentences)
    assert isinstance(sentence_embeddings, np.ndarray)
    assert sentence_embeddings.shape == (4, 384)

    # test with torch
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    sentence_embeddings = sentence_embeddings.cpu().detach()
    assert isinstance(sentence_embeddings, torch.Tensor)
    assert sentence_embeddings.shape == (4, 384)

    # find cosine similarity between the first and other sentences
    similarity = cosine_similarity(sentence_embeddings[0], sentence_embeddings[1])
    assert 0 <= similarity <= 1

    similarity2 = cosine_similarity(sentence_embeddings[0], sentence_embeddings[2])
    similarity3 = cosine_similarity(sentence_embeddings[0], sentence_embeddings[3])

    similarities = [
        (sentences[1], similarity),
        (sentences[2], similarity2),
        (sentences[3], similarity3)
    ]

    # sort the similarities
    similarities.sort(key=lambda x: x[1], reverse=True)

    for sentence, sim in similarities:
        print(f"{sentence} - similarity: {sim}")

if __name__ == '__main__':
    test_sentence_transformer()

