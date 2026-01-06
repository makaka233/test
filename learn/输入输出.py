# 输出（格式化3种方式）
name = "Python"
print("Hello, %s!" % name)          # 旧式格式化
print("Hello, {}!".format(name))    # format格式化
print(f"Hello, {name}!")            # f-string（推荐）

# 输入（默认返回字符串）
age = input("请输入年龄：")
age = int(age) # 转换为整数
print(f"年龄：{age+1}")