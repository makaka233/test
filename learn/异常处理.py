try:
    num = int(input("请输入数字："))
    print(10 / num)
except ValueError:
    print("输入不是有效数字！")
except ZeroDivisionError:
    print("不能除以0！")
else:
    print("无异常执行")
finally:
    print("无论是否异常都执行")

# 定义类
class Person:
    def __init__(self, name, age): # 初始化方法
        self.name = name  # 实例属性
        self.age = age

    def say_hello(self): # 实例方法
        print(f"我是{self.name}，{self.age}岁")

# 创建实例并调用方法
p = Person("小明", 18)
p.say_hello() # 输出：我是小明，18岁