from . import ancestry_tree, window



class Context:

    def __init__(self,
                 chunk,
                 history) -> None:
        self.__window = window.SlidingWindow(3, history)
        self.__ancestry = ancestry_tree.Ancestry(chunk, history)
        chunk.set_context(self.get_context())


    # return list of chunks in context
    def get_context(self) -> list:
        context = []
        window   = self.__window.get_window()
        ancestry = self.__ancestry.get_ancestry()
        for item in window:
            if item not in context:
                context.append(item)
        for item in ancestry:
            if item not in context:
                context.append(item)
        return context


    def __len__(self) -> int:
        return len(self.get_context())


    def __iter__(self):
        return iter(self.get_context())


    def get_form(self):
        return [f'{chunk}' for chunk in self.get_context()]
