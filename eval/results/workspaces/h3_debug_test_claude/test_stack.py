from stack import Stack

def test_push_pop():
    s = Stack()
    s.push(1)
    s.push(2)
    s.push(3)
    assert s.pop() == 3  # LIFO: last in first out
    assert s.pop() == 2
    assert s.pop() == 1

def test_peek():
    s = Stack()
    s.push(10)
    s.push(20)
    assert s.peek() == 20  # should see top
    s.pop()
    assert s.peek() == 10

def test_empty():
    s = Stack()
    assert s.is_empty()
    assert s.pop() is None
    assert s.peek() is None

test_push_pop()
test_peek()
test_empty()
print('ALL TESTS PASS')
