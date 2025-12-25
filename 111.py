from flask import Flask, render_template_string, request, redirect, url_for
import pandas as pd
import os
from datetime import datetime

# 初始化Flask应用
app = Flask(__name__)

# ---------------------- 新增：产品数据（只需修改这里的产品信息） ----------------------
PRODUCTS = [
    {
        "id": 1,
        "name": "便携办公笔记本 Pro",
        "config": "酷睿i5 + 16GB内存 + 512GB固态",
        "battery": "15小时超长续航",
        "price": "¥3999",
        "phone": "13800138000",
        "img": "https://img10.360buyimg.com/n1/jfs/t1/20802/33/25333/333813/64830790F69908950/8c89978d40888888.jpg"
    },
    {
        "id": 2,
        "name": "轻薄商务本 Air",
        "config": "锐龙R7 + 8GB内存 + 256GB固态",
        "battery": "12小时续航",
        "price": "¥2999",
        "phone": "13900139000",
        "img": "https://img14.360buyimg.com/n1/jfs/t1/21608/19/24375/123456/648a7890F69908950/8c89978d40888888.jpg"
    },
    {
        "id": 3,
        "name": "游戏本 Max",
        "config": "酷睿i7 + 32GB内存 + 1TB固态 + RTX4060",
        "battery": "8小时续航",
        "price": "¥6999",
        "phone": "13700137000",
        "img": "https://img12.360buyimg.com/n1/jfs/t1/21800/13/25500/987654/649c7890F69908950/8c89978d40888888.jpg"
    }
]

# ---------------------- 网页模板（新增搜索、多产品、表单） ----------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>产品介绍平台</title>
    <style>
        body {font-family: 微软雅黑; max-width: 1000px; margin: 0 auto; padding: 20px;}
        .header {text-align: center; margin-bottom: 30px;}
        .search-box {margin: 20px 0;}
        .search-input {padding: 8px; width: 300px; border: 1px solid #ddd; border-radius: 4px;}
        .search-btn {padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;}
        .product-list {display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;}
        .product-card {width: 300px; border: 1px solid #ddd; padding: 20px; border-radius: 10px; box-shadow: 0 0 8px #f5f5f5;}
        .product-img {width: 100%; height: 200px; object-fit: cover; border-radius: 5px;}
        .param {font-size: 14px; line-height: 1.8; margin: 8px 0;}
        .form-box {margin: 40px auto; max-width: 500px; border: 1px solid #ddd; padding: 30px; border-radius: 10px;}
        .form-input {width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px;}
        .submit-btn {width: 100%; padding: 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;}
        .success {color: green; text-align: center; margin: 10px 0;}
    </style>
</head>
<body>
    <div class="header">
        <h1>产品介绍平台</h1>
        <!-- 新增：产品搜索框 -->
        <div class="search-box">
            <form method="GET" action="/">
                <input type="text" name="keyword" class="search-input" placeholder="输入产品名称搜索..." value="{{ keyword }}">
                <button type="submit" class="search-btn">搜索</button>
            </form>
        </div>
    </div>

    <!-- 新增：多产品展示 -->
    <div class="product-list">
        {% for product in products %}
        <div class="product-card">
            <h3>{{ product.name }}</h3>
            <img src="{{ product.img }}" class="product-img" alt="{{ product.name }}">
            <div class="param"><strong>配置：</strong>{{ product.config }}</div>
            <div class="param"><strong>续航：</strong>{{ product.battery }}</div>
            <div class="param"><strong>售价：</strong>{{ product.price }}</div>
            <div class="param"><strong>咨询电话：</strong>{{ product.phone }}</div>
        </div>
        {% else %}
        <p>未找到匹配的产品</p>
        {% endfor %}
    </div>

    <!-- 新增：客户咨询表单 -->
    <div class="form-box">
        <h2 style="text-align: center;">在线咨询</h2>
        {% if success_msg %}
        <p class="success">{{ success_msg }}</p>
        {% endif %}
        <form method="POST" action="/submit">
            <input type="text" name="name" class="form-input" placeholder="您的姓名" required>
            <input type="tel" name="phone" class="form-input" placeholder="您的电话" required>
            <input type="text" name="product" class="form-input" placeholder="感兴趣的产品" required>
            <textarea name="message" class="form-input" rows="3" placeholder="您的咨询内容"></textarea>
            <button type="submit" class="submit-btn">提交咨询</button>
        </form>
    </div>
</body>
</html>
"""

# ---------------------- 核心功能路由 ----------------------
# 首页：展示产品+搜索功能
@app.route('/')
def index():
    # 获取搜索关键词
    keyword = request.args.get('keyword', '').strip()
    # 筛选产品（支持模糊搜索）
    filtered_products = []
    for p in PRODUCTS:
        if keyword.lower() in p['name'].lower():
            filtered_products.append(p)
    # 渲染网页
    return render_template_string(HTML_TEMPLATE, products=filtered_products, keyword=keyword)

# 新增：表单提交+数据保存到Excel
@app.route('/submit', methods=['POST'])
def submit_form():
    # 获取表单数据
    name = request.form.get('name')
    phone = request.form.get('phone')
    product = request.form.get('product')
    message = request.form.get('message', '')
    submit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 准备保存的数据
    data = {
        '姓名': [name],
        '电话': [phone],
        '感兴趣产品': [product],
        '咨询内容': [message],
        '提交时间': [submit_time]
    }
    df = pd.DataFrame(data)

    # 保存到Excel（不存在则新建，存在则追加）
    excel_file = '客户咨询记录.xlsx'
    if os.path.exists(excel_file):
        # 追加数据
        existing_df = pd.read_excel(excel_file)
        new_df = pd.concat([existing_df, df], ignore_index=True)
        new_df.to_excel(excel_file, index=False)
    else:
        # 新建文件
        df.to_excel(excel_file, index=False)

    # 提交成功后返回首页并提示
    return render_template_string(HTML_TEMPLATE, 
                                   products=PRODUCTS, 
                                   keyword='',
                                   success_msg='咨询信息提交成功！我们会尽快联系您~')

# 启动服务
if __name__ == '__main__':
    # 安装pandas（如果没装过，先执行：pip install pandas openpyxl）
    app.run(host='0.0.0.0', port=5000, debug=True)