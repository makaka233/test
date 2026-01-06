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
        "img": "data:image/webp;base64,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"
    },
    {
        "id": 2,
        "name": "轻薄商务本 Air",
        "config": "锐龙R7 + 8GB内存 + 256GB固态",
        "battery": "12小时续航",
        "price": "¥2999",
        "phone": "13900139000",
        "img": "https://tse3.mm.bing.net/th/id/OIP.fVpzNCHV20ExP_ZhIbVrrQHaE7?w=248&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3"
    },
    {
        "id": 3,
        "name": "游戏本 Max",
        "config": "酷睿i7 + 32GB内存 + 1TB固态 + RTX4060",
        "battery": "8小时续航",
        "price": "¥6999",
        "phone": "13700137000",
        "img": "data:image/webp;base64,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"
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