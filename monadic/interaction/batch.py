from . import openai_services

from monadic.singleton import singleton



@singleton
class EmbeddingBatcher:
    def __init__(self):
        self.__batch = []

    def __call__(self, data, caller):
        self.__batch.append({
            'data': data,
            'caller': caller
        })
        return self.__batch

    def clear(self):
        self.__batch.clear()

    @property
    def batch(self):
        return self.__batch.copy()
    
    @batch.setter
    def batch(self, batch):
        if batch is None:
            raise ValueError("'batch' cannot be None")
        if not isinstance(batch, list):
            raise TypeError(f"Expected a 'list' for 'batch', got '{type(batch).__name__}'")
    

    def send(self):
        datas = []
        callers = []
        for data, caller in self.batch:
            datas.append(data)
            callers.append(caller)
        embeddings = openai_services.embeddings(datas).data
        for caller, embedding in zip(callers, embeddings):
            caller = embedding




embedding_batcher = EmbeddingBatcher()