import numpy
from sklearn.metrics.pairwise import cosine_similarity

from monadic.interaction.batch import embedding_batcher



class AncestryTree:

    # __slots__ = ("text", "_uid", "_ancestors", "_embedding", "_embedding_ready")

    def __init__(
            self,
            uid,
            data,
            history,
            size
    ):
        self.uid = uid
        self.text = data
        self.ancestors = []
        self.embedding = []
        embedding_batcher(data, self.embedding)
        


    # uid

    @property
    def uid(self):
        return self._uid
    
    @uid.setter
    def uid(self, uid):
        if uid is None:
            raise ValueError("'uid' cannot be None")
        if not isinstance(uid, int):
            raise TypeError(f"Expected an 'int' for 'uid', got '{type(uid).__name__}'")
        self._uid = uid


    # embedding

    @property
    def embedding(self):
        return self.__embedding
    
    @embedding.setter
    def embedding(self, embedding):
        if embedding is None:
            raise ValueError("'embedding' cannot be None")
        if not isinstance(embedding, list):
            raise TypeError(f"Expected a 'list' for 'embedding', got '{type(embedding).__name__}'")
        self.__embedding = embedding


    # ancestors
    
    @property
    def ancestors(self):
        return self._ancestors
    
    @ancestors.setter
    def ancestors(self, ancestors):
        if ancestors is None:
            raise ValueError("'ancestors' cannot be None")
        if not isinstance(ancestors, list):
            raise TypeError(f"Expected a 'list' for 'ancestors', got '{type(ancestors).__name__}'")
        self._ancestors = ancestors




    def _cosine_similarities(
            self,
            target_vectors,
            query_vector
    ):
        # Convert to NumPy arrays
        target_array = numpy.array(target_vectors)
        query_array = numpy.array(query_vector).reshape(1, -1)

        similarities = cosine_similarity(target_array, query_array).flatten()

        # Sort in descending order (most similar first)
        sorted_indices = numpy.argsort(-similarities)
        sorted_similarities = similarities[sorted_indices]

        return sorted_similarities
