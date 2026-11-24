def print_result(label, value):
    print(f'{label}: {value}')


def process_a(x):
    result = x * 2
    print_result('A', result)
    return result


def process_b(x):
    result = x + 10
    print_result('B', result)
    return result


def process_c(x):
    result = x - 5
    print_result('C', result)
    return result