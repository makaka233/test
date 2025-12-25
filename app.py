from flask import Flask, render_template

app = Flask(__name__)

# 根路由，渲染游戏页面
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # 启动 Flask 服务，允许外部访问，调试模式开启
    app.run(debug=True, host='0.0.0.0', port=5000)