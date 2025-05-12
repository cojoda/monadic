import numpy
from monadic.history import data_chunk 



class Ancestry:

    def __init__(self,
                 target:    data_chunk.Chunk       | None,
                 ancestors: list[data_chunk.Chunk] | None) -> None:
        self.__ancestors: list[dict] = []

        if target is None: return
        if ancestors is None: ancestors = []
        
        self.__ancestors = self._resolve(target, ancestors)



    # return as list of chunks in ancestry
    def get_ancestry(self):
        if self.__ancestors is None: return []
        ancestor_chunks = [ancestor['chunk'] for ancestor in self.__ancestors]
        next_gen = self._get_next_gen(ancestor_chunks)
        # print(f'\033[93m{next_gen}\033[0m')
        return next_gen


    def _distance(self,
                  chunk_1,
                  chunk_2) -> float:
        embed_1 = chunk_1.get_embed()
        embed_2 = chunk_2.get_embed()
        v1 = numpy.array(embed_1)
        v2 = numpy.array(embed_2)
        dot_product = numpy.dot(v1, v2)
        norm_1 = numpy.linalg.norm(v1)
        norm_2 = numpy.linalg.norm(v2)
        return dot_product / (norm_1 * norm_2)
    


    # calculate ancestors
    def _resolve(self,
                 target,
                 ancestors: list | None) -> list[dict]:
        if target is None or ancestors is None: return []

        distances = []
        for ancestor in ancestors:
            distances.append({'distance': self._distance(target, ancestor),
                              'chunk':    ancestor})
        distances.sort(key=lambda i: i['distance'])
        return distances[-3:]



    def _get_next_gen(self, chunks):
        results = []
        for chunk in chunks:
            results.extend(chunk.get_context())
        return results
