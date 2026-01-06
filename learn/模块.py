# 方式1：导入整个模块
import math
print(math.sqrt(16)) # 4.0（平方根）

# 方式2：导入指定函数
from random import randint
print(randint(1, 10)) # 1-10随机整数

# 方式3：自定义模块（新建test.py，写入def func(): print(1)）
import test_1
test_1.func() # 调用自定义模块函数

