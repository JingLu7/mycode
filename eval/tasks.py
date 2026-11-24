"""评估任务集定义 — 12 个任务，3 个难度级别。

每个任务包含：
- id: 任务 ID
- difficulty: easy/medium/hard
- prompt: 给 agent 的提示词
- setup_files: 任务前创建的文件 {path: content}
- setup_cmds: 任务前执行的命令
- scoring: 评分方法 + 参数
"""
import os
import json
import shutil

TASKS = [
    # ==================== EASY ====================
    {
        "id": "e1_file_read",
        "difficulty": "easy",
        "prompt": "读取文件 config.json 并告诉我里面有多少个键值对，以及每个键的名字。",
        "setup_files": {
            "config.json": json.dumps({"name": "myapp", "version": "1.0.0", "debug": True, "port": 8080, "host": "localhost"}, indent=2),
        },
        "scoring": {"method": "regex", "pattern": r"(name|version|debug|port|host)", "min_matches": 5, "description": "应提到所有 5 个键名"},
    },
    {
        "id": "e2_glob_search",
        "difficulty": "easy",
        "prompt": "在当前目录下找到所有 Python 文件（.py 结尾），列出它们的文件名。",
        "setup_files": {
            "main.py": "print('hello')\n",
            "utils.py": "def add(a,b): return a+b\n",
            "test.py": "assert True\n",
            "readme.md": "# README\n",
            "config.json": "{}\n",
        },
        "scoring": {"method": "regex", "pattern": r"(main\.py|utils\.py|test\.py)", "min_matches": 3, "description": "应找到 3 个 .py 文件"},
    },
    {
        "id": "e3_simple_code",
        "difficulty": "easy",
        "prompt": "写一个 Python 函数 bubble_sort(arr)，实现对列表的冒泡排序。写入文件 sort.py。不要写测试。",
        "setup_files": {},
        "scoring": {"method": "test_pass", "test_code": "from sort import bubble_sort\nassert bubble_sort([3,1,2]) == [1,2,3]\nassert bubble_sort([5,4,3,2,1]) == [1,2,3,4,5]\nassert bubble_sort([]) == []\nassert bubble_sort([1]) == [1]\nprint('PASS')\n", "description": "bubble_sort 应正确排序"},
    },
    {
        "id": "e4_text_replace",
        "difficulty": "easy",
        "prompt": "读取文件 data.txt，把里面所有的 'foo' 替换成 'bar'，结果写回 data.txt。",
        "setup_files": {
            "data.txt": "foo is foo\nfoo bar foo\nthe foo bar\n",
        },
        "scoring": {"method": "file_match", "expected_file": "data.txt", "expected_content": "bar is bar\nbar bar bar\nthe bar bar\n", "description": "所有 foo 应替换为 bar"},
    },
    # ==================== MEDIUM ====================
    {
        "id": "m1_bug_fix",
        "difficulty": "medium",
        "prompt": "文件 calculator.py 中有一个 bug：除法函数在除以 0 时没有处理。修复 divide 函数使其在除以 0 时返回 None 而不是崩溃。修改后不要破坏其他函数。",
        "setup_files": {
            "calculator.py": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n\ndef multiply(a, b):\n    return a * b\n\ndef divide(a, b):\n    return a / b\n",
        },
        "scoring": {"method": "test_pass", "test_code": "from calculator import divide, add, multiply\nassert divide(10, 2) == 5.0\nassert divide(10, 0) is None\nassert add(1, 2) == 3\nassert multiply(3, 4) == 12\nprint('PASS')\n", "description": "divide(10,0) 应返回 None，其他函数不受影响"},
    },
    {
        "id": "m2_multi_file",
        "difficulty": "medium",
        "prompt": "读取 users.json 和 orders.json 两个文件，找出所有有订单的用户名字，按字母排序后写入 active_users.txt，每行一个名字。",
        "setup_files": {
            "users.json": json.dumps([
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
                {"id": 4, "name": "Diana"},
            ], indent=2),
            "orders.json": json.dumps([
                {"order_id": 101, "user_id": 3, "amount": 50},
                {"order_id": 102, "user_id": 1, "amount": 30},
                {"order_id": 103, "user_id": 3, "amount": 20},
            ], indent=2),
        },
        "scoring": {"method": "file_match", "expected_file": "active_users.txt", "expected_content": "Alice\nCharlie\n", "description": "只有 Alice(id=1) 和 Charlie(id=3) 有订单"},
    },
    {
        "id": "m3_shell_parse",
        "difficulty": "medium",
        "prompt": "执行命令 `python3 -c \"print(list(range(1,21)))\"` 然后从输出中提取所有偶数，把结果写入 evens.txt，每行一个数字。",
        "setup_files": {},
        "scoring": {"method": "file_match", "expected_file": "evens.txt", "expected_content": "2\n4\n6\n8\n10\n12\n14\n16\n18\n20\n", "description": "应提取 1-20 中的所有偶数"},
    },
    {
        "id": "m4_refactor",
        "difficulty": "medium",
        "prompt": "重构文件 messy.py：把重复的打印逻辑提取成一个函数 print_result(label, value)，保持功能不变。修改后写入同一文件。",
        "setup_files": {
            "messy.py": "def process_a(x):\n    result = x * 2\n    print(f'A: {result}')\n    return result\n\ndef process_b(x):\n    result = x + 10\n    print(f'B: {result}')\n    return result\n\ndef process_c(x):\n    result = x - 5\n    print(f'C: {result}')\n    return result\n",
        },
        "scoring": {"method": "test_pass", "test_code": "import messy\nassert messy.process_a(5) == 10\nassert messy.process_b(5) == 15\nassert messy.process_c(10) == 5\n# 检查是否有 print_result 函数\nassert hasattr(messy, 'print_result'), '应提取 print_result 函数'\nprint('PASS')\n", "description": "功能不变 + 提取了 print_result 函数"},
    },
    # ==================== HARD ====================
    {
        "id": "h1_project_analyze",
        "difficulty": "hard",
        "prompt": "分析当前目录下的项目结构，生成一个分析报告写入 analysis.md。报告应包含：1) 所有文件列表 2) 每个文件的行数 3) 代码中定义的所有函数名。用 markdown 格式。",
        "setup_files": {
            "app.py": "def main():\n    print('running')\n\ndef helper():\n    return 42\n",
            "models.py": "class User:\n    def __init__(self, name):\n        self.name = name\n    \n    def greet(self):\n        return f'Hi {self.name}'\n",
            "utils.py": "def format_date(d):\n    return str(d)\n\ndef parse_int(s):\n    return int(s)\n",
        },
        "scoring": {"method": "regex_all", "patterns": [r"analysis\.md", r"main", r"helper", r"greet", r"format_date", r"parse_int", r"app\.py", r"models\.py", r"utils\.py"], "min_matches": 7, "description": "报告应包含文件列表、行数和函数名"},
    },
    {
        "id": "h2_tool_chain",
        "difficulty": "hard",
        "prompt": "1. 读取 config.yaml 获取配置 2. 根据配置中的 enabled_modules 列表，为每个模块创建一个空文件 <module_name>.py 3. 在每个文件中写入一个函数 def init(): pass 4. 验证所有文件都已创建",
        "setup_files": {
            "config.yaml": "app_name: myapp\nenabled_modules:\n  - auth\n  - database\n  - api\n  - cache\ndisable_modules: []\n",
        },
        "scoring": {"method": "files_exist", "expected_files": ["auth.py", "database.py", "api.py", "cache.py"], "check_content": "def init():", "description": "应为 4 个模块各创建 .py 文件含 init 函数"},
    },
    {
        "id": "h3_debug_test",
        "difficulty": "hard",
        "prompt": "文件 stack.py 实现了一个栈，但测试文件 test_stack.py 中的测试失败了。请定位 bug 并修复 stack.py，使所有测试通过。不要修改测试文件。",
        "setup_files": {
            "stack.py": "class Stack:\n    def __init__(self):\n        self.items = []\n    \n    def push(self, item):\n        self.items.append(item)\n    \n    def pop(self):\n        if self.is_empty():\n            return None\n        return self.items.pop(0)  # bug: should pop from end\n    \n    def peek(self):\n        if self.is_empty():\n            return None\n        return self.items[-1]\n    \n    def is_empty(self):\n        return len(self.items) == 0\n    \n    def size(self):\n        return len(self.items)\n",
            "test_stack.py": "from stack import Stack\n\ndef test_push_pop():\n    s = Stack()\n    s.push(1)\n    s.push(2)\n    s.push(3)\n    assert s.pop() == 3  # LIFO: last in first out\n    assert s.pop() == 2\n    assert s.pop() == 1\n\ndef test_peek():\n    s = Stack()\n    s.push(10)\n    s.push(20)\n    assert s.peek() == 20  # should see top\n    s.pop()\n    assert s.peek() == 10\n\ndef test_empty():\n    s = Stack()\n    assert s.is_empty()\n    assert s.pop() is None\n    assert s.peek() is None\n\ntest_push_pop()\ntest_peek()\ntest_empty()\nprint('ALL TESTS PASS')\n",
        },
        "scoring": {"method": "test_pass", "test_code": "from stack import Stack\ns = Stack()\ns.push(1); s.push(2); s.push(3)\nassert s.pop() == 3\nassert s.pop() == 2\nassert s.pop() == 1\nassert s.pop() is None\nprint('PASS')\n", "description": "栈应为 LIFO（后进先出）"},
    },
    {
        "id": "h4_design_impl",
        "difficulty": "hard",
        "prompt": "设计并实现一个简单的键值存储模块 kvstore.py，要求：1) KVStore 类支持 get/set/delete/exists/keys 五个方法 2) set(key, value) 存储键值对 3) get(key) 返回值，不存在返回 None 4) delete(key) 删除键，不存在不报错 5) exists(key) 返回 bool 6) keys() 返回所有键的列表。写入文件 kvstore.py，不要写测试。",
        "setup_files": {},
        "scoring": {"method": "test_pass", "test_code": "from kvstore import KVStore\nstore = KVStore()\nassert store.get('x') is None\nstore.set('x', 100)\nstore.set('y', 200)\nassert store.get('x') == 100\nassert store.exists('x')\nassert not store.exists('z')\nassert sorted(store.keys()) == ['x', 'y']\nstore.delete('x')\nassert store.get('x') is None\nassert not store.exists('x')\nassert store.keys() == ['y']\nstore.delete('nonexistent')  # should not raise\nprint('PASS')\n", "description": "KVStore 应实现 get/set/delete/exists/keys 且行为正确"},
    },
]


def setup_workspace(task, workspace_dir):
    """为任务创建工作目录和初始文件。"""
    os.makedirs(workspace_dir, exist_ok=True)
    for filepath, content in task.get("setup_files", {}).items():
        full_path = os.path.join(workspace_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True) if os.path.dirname(full_path) else None
        with open(full_path, "w") as f:
            f.write(content)
    return workspace_dir


def get_tasks_by_difficulty(difficulty=None):
    """按难度过滤任务。"""
    if difficulty is None:
        return TASKS
    return [t for t in TASKS if t["difficulty"] == difficulty]