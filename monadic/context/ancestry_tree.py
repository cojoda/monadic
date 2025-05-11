import numpy



class Ancestry:

    def __init__(self,
                 target,
                 ancestors: list | None) -> None:
        if target is None: target = []
        if ancestors is None: ancestors = []
        self.__ancestors = self._resolve(target, ancestors)



    # return as list of chunks in ancestry
    def get_ancestry(self):
        if self.__ancestors is None: return []
        return [ancestor['chunk'] for ancestor in self.__ancestors]



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
    


    def _resolve(self,
                 target,
                 ancestors: list | None) -> list[dict]:
        if target is None or ancestors is None: return []

        distances = []
        for ancestor in ancestors:
            distances.append({'distance': self._distance(target, ancestor),
                              'chunk': ancestor})
        distances.sort(key=lambda i: i['distance'])
        return distances[-3:]
