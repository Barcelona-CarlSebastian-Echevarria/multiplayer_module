class Stack:
    """ Stack (LIFO) implementation (Project ADT demonstration)"""
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("Error: Stack is empty")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("Error: Stack is empty")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0
    
    