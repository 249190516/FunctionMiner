from sentence_transformers import SentenceTransformer


class Nlp:
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    @staticmethod
    def getSimilar(str1, str2):
        sentences = [str1, str2]
        embeddings = Nlp.model.encode(sentences)
        similarities = Nlp.model.similarity(embeddings, embeddings)
        similarity = similarities[0, 1].item()

        # print(f"Similarity between '{str1}' and '{str2}': {similarity}")
        if similarity > 0.50:
            return similarity * 10
        else:
            return 0


if __name__ == '__main__':

    word1 = "mainactivity clock_fragment"
    word2 = "clock interface"

    Nlp.getSimilar(word1, word2)
