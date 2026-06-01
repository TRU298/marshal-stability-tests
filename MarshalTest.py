#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marshal 模块稳定性与正确性测试套件
测试目标：相同输入是否总是产生相同的 marshal 字节流
"""

import marshal
import sys
import platform
from datetime import datetime


# ============================================================
# 颜色输出（仅在终端支持时生效，不影响结果）
# ============================================================
try:
    from colorama import init, Fore, Style
    init()
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = RESET = ""


def cprint(color, text):
    """带颜色的打印"""
    print(f"{color}{text}{RESET}")


# ============================================================
# 测试框架
# ============================================================
class MarshalStabilityTest:
    """marshal 稳定性测试类"""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results = []

    def assert_stable(self, name, obj, compare_twice=True):
        """
        核心断言：同一对象两次序列化结果必须完全相同
        """
        self.total += 1
        try:
            b1 = marshal.dumps(obj)
            b2 = marshal.dumps(obj)

            if compare_twice and b1 != b2:
                raise AssertionError(
                    f"两次序列化结果不同\n"
                    f"  第一次: {b1[:50]}...\n"
                    f"  第二次: {b2[:50]}..."
                )

            self.passed += 1
            self.results.append((name, True, None))
            cprint(GREEN, f"  ✅ PASS: {name}")
            return True

        except Exception as e:
            self.failed += 1
            self.results.append((name, False, str(e)))
            cprint(RED, f"  ❌ FAIL: {name}")
            print(f"      错误: {e}")
            return False

    def assert_roundtrip(self, name, obj):
        """
        额外测试：序列化 -> 反序列化 后是否与原始对象逻辑相等
        """
        try:
            dumped = marshal.dumps(obj)
            loaded = marshal.loads(dumped)

            # 对于 NaN，使用 math.isnan 特殊处理
            if isinstance(obj, float) and obj != obj:  # NaN 特性
                if loaded != loaded:
                    self.passed += 1
                    cprint(GREEN, f"  ✅ PASS (roundtrip): {name} (NaN handled)")
                    return True
                else:
                    raise AssertionError("NaN roundtrip failed")
            else:
                if loaded == obj:
                    self.passed += 1
                    cprint(GREEN, f"  ✅ PASS (roundtrip): {name}")
                    return True
                else:
                    raise AssertionError(f"Roundtrip mismatch: {obj} -> {loaded}")
        except Exception as e:
            self.failed += 1
            self.results.append((name, False, str(e)))
            cprint(RED, f"  ❌ FAIL (roundtrip): {name}")
            print(f"      错误: {e}")
            return False

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"总测试数: {self.total}")
        print(f"通过: {GREEN}{self.passed}{RESET}")
        print(f"失败: {RED}{self.failed}{RESET}")
        print(f"通过率: {self.passed / self.total * 100:.1f}%")

        # 列出失败的测试
        failed_tests = [name for name, passed, _ in self.results if not passed]
        if failed_tests:
            print(f"\n{RED}失败的测试:{RESET}")
            for name in failed_tests:
                print(f"  - {name}")

    def print_environment(self):
        """打印测试环境信息"""
        print("=" * 70)
        print("测试环境")
        print("=" * 70)
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"Python 版本: {sys.version}")
        print(f"架构: {platform.machine()}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)


# ============================================================
# 测试用例定义
# ============================================================
def run_all_tests():
    """运行所有测试用例"""
    tester = MarshalStabilityTest()
    tester.print_environment()

    print("\n" + "=" * 70)
    print("稳定性测试（两次序列化结果是否相同）")
    print("=" * 70)

    # ----- 1. 基本类型 -----
    print("\n--- 1. 基本类型 ---")
    tester.assert_stable("None", None)
    tester.assert_stable("True", True)
    tester.assert_stable("False", False)
    tester.assert_stable("整数 0", 0)
    tester.assert_stable("整数 42", 42)
    tester.assert_stable("整数 -1", -1)
    tester.assert_stable("大整数 2**100", 2**100)
    tester.assert_stable("字符串 'hello'", "hello")
    tester.assert_stable("空字符串 ''", "")
    tester.assert_stable("字节串 b'hello'", b"hello")
    tester.assert_stable("空字节串 b''", b"")

    # ----- 2. 浮点数 -----
    print("\n--- 2. 浮点数 ---")
    tester.assert_stable("浮点数 0.0", 0.0)
    tester.assert_stable("浮点数 3.14159", 3.14159)
    tester.assert_stable("浮点数 -2.5", -2.5)
    tester.assert_stable("负零 -0.0", -0.0)

    # ----- 3. 特殊浮点数（重点！）-----
    print("\n--- 3. 特殊浮点数（关键测试）---")
    tester.assert_stable("NaN", float('nan'))
    tester.assert_stable("正无穷 Inf", float('inf'))
    tester.assert_stable("负无穷 -Inf", float('-inf'))

    # ----- 4. 容器类型 -----
    print("\n--- 4. 容器类型 ---")
    tester.assert_stable("空列表 []", [])
    tester.assert_stable("单元素列表 [1]", [1])
    tester.assert_stable("多层列表 [1, [2, 3]]", [1, [2, 3]])
    tester.assert_stable("空元组 ()", ())
    tester.assert_stable("单元素元组 (1,)", (1,))
    tester.assert_stable("元组 (1,2,3)", (1, 2, 3))
    tester.assert_stable("空字典 {}", {})
    tester.assert_stable("字典 {'a': 1}", {"a": 1})
    tester.assert_stable("空集合 set()", set())
    tester.assert_stable("集合 {1,2,3}", {1, 2, 3})
    tester.assert_stable("空冻结集合 frozenset()", frozenset())
    tester.assert_stable("冻结集合 frozenset({1,2})", frozenset({1, 2}))

    # ----- 5. 边界值 -----
    print("\n--- 5. 边界值 ---")
    tester.assert_stable("极大整数 2**100000", 2**100000)
    tester.assert_stable("极小整数 -2**100000", -2**100000)
    tester.assert_stable("长字符串 'a' * 10000", "a" * 10000)
    tester.assert_stable("大列表 list(range(1000))", list(range(1000)))

    # ----- 6. 递归/循环结构 -----
    print("\n--- 6. 递归/循环结构 ---")
    recursive_list = []
    recursive_list.append(recursive_list)
    tester.assert_stable("自引用列表", recursive_list)

    recursive_dict = {}
    recursive_dict["self"] = recursive_dict
    tester.assert_stable("自引用字典", recursive_dict)

    # 相互引用的列表
    a = [1]
    b = [2]
    a.append(b)
    b.append(a)
    tester.assert_stable("互相引用的列表", a)

    # ----- 7. 复合类型组合 -----
    print("\n--- 7. 复合类型组合 ---")
    complex_obj = {
        "int": 42,
        "float": 3.14,
        "nan": float('nan'),
        "list": [1, 2, [3, 4]],
        "tuple": (5, 6),
        "nested_dict": {"key": "value"}
    }
    tester.assert_stable("复合字典对象", complex_obj)

    # ----- 8. 模糊随机测试 -----
    print("\n--- 8. 模糊随机测试 ---")
    import random
    random.seed(42)  # 固定种子，保证可复现
    for i in range(20):
        rand_val = random.random()
        tester.assert_stable(f"随机浮点数 #{i+1}", rand_val)

    # ============================================================
    # 反序列化正确性测试
    # ============================================================
    print("\n" + "=" * 70)
    print("反序列化正确性测试（序列化 -> 反序列化 后是否相等）")
    print("=" * 70)

    tester.assert_roundtrip("None", None)
    tester.assert_roundtrip("整数 42", 42)
    tester.assert_roundtrip("大整数", 2**100)
    tester.assert_roundtrip("浮点数 3.14", 3.14)
    tester.assert_roundtrip("NaN", float('nan'))
    tester.assert_roundtrip("字符串 'hello'", "hello")
    tester.assert_roundtrip("列表 [1,2,3]", [1, 2, 3])
    tester.assert_roundtrip("字典 {'a':1}", {"a": 1})
    tester.assert_roundtrip("空列表", [])
    tester.assert_roundtrip("空字典", {})

    # ============================================================
    # 打印总结
    # ============================================================
    tester.print_summary()

    return tester


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    run_all_tests()