import tkinter as tk  # 原生GUI库
import random  # 原生随机数库
import time  # 原生时间库

class SnakeGame:
    def __init__(self, root):
        # 游戏配置
        self.root = root
        self.root.title("Python原生贪吃蛇游戏")
        self.root.resizable(False, False)
        
        # 画布尺寸和格子大小
        self.grid_size = 20
        self.canvas_width = 400
        self.canvas_height = 400
        
        # 创建画布
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()
        
        # 游戏状态初始化
        self.snake = [(10, 10), (9, 10), (8, 10)]  # 蛇身坐标（x,y）
        self.direction = "Right"  # 初始方向
        self.food = self.generate_food()  # 食物坐标
        self.score = 0  # 得分
        self.game_over = False
        self.speed = 150  # 游戏速度（毫秒）
        
        # 得分标签
        self.score_label = tk.Label(root, text=f"得分：{self.score}", font=("Arial", 14))
        self.score_label.pack()
        
        # 绑定方向键
        self.root.bind("<Up>", lambda e: self.change_direction("Up"))
        self.root.bind("<Down>", lambda e: self.change_direction("Down"))
        self.root.bind("<Left>", lambda e: self.change_direction("Left"))
        self.root.bind("<Right>", lambda e: self.change_direction("Right"))
        self.root.bind("<space>", self.restart_game)  # 空格键重启
        
        # 启动游戏循环
        self.game_loop()

    def generate_food(self):
        """生成食物（避免出现在蛇身上）"""
        while True:
            x = random.randint(0, (self.canvas_width - self.grid_size) // self.grid_size)
            y = random.randint(0, (self.canvas_height - self.grid_size) // self.grid_size)
            food_pos = (x, y)
            if food_pos not in self.snake:
                return food_pos

    def change_direction(self, new_dir):
        """改变蛇的方向（禁止180度反向）"""
        if self.game_over:
            return
        # 禁止反向
        if new_dir == "Up" and self.direction != "Down":
            self.direction = new_dir
        elif new_dir == "Down" and self.direction != "Up":
            self.direction = new_dir
        elif new_dir == "Left" and self.direction != "Right":
            self.direction = new_dir
        elif new_dir == "Right" and self.direction != "Left":
            self.direction = new_dir

    def move_snake(self):
        """移动蛇的位置"""
        # 获取蛇头坐标
        head_x, head_y = self.snake[0]
        
        # 根据方向更新蛇头
        if self.direction == "Up":
            new_head = (head_x, head_y - 1)
        elif self.direction == "Down":
            new_head = (head_x, head_y + 1)
        elif self.direction == "Left":
            new_head = (head_x - 1, head_y)
        else:  # Right
            new_head = (head_x + 1, head_y)
        
        # 插入新蛇头
        self.snake.insert(0, new_head)
        
        # 判断是否吃到食物
        if new_head == self.food:
            self.score += 10
            self.score_label.config(text=f"得分：{self.score}")
            self.food = self.generate_food()  # 重新生成食物
        else:
            self.snake.pop()  # 没吃到食物则移除尾部
        
        # 判断游戏结束条件（撞墙/撞自己）
        if (new_head[0] < 0 or new_head[0] >= self.canvas_width // self.grid_size or
            new_head[1] < 0 or new_head[1] >= self.canvas_height // self.grid_size or
            new_head in self.snake[1:]):
            self.game_over = True

    def draw_game(self):
        """绘制游戏画面"""
        # 清空画布
        self.canvas.delete("all")
        
        # 绘制蛇
        for i, (x, y) in enumerate(self.snake):
            color = "green" if i == 0 else "darkgreen"  # 蛇头绿色，身体深绿
            self.canvas.create_rectangle(
                x * self.grid_size, y * self.grid_size,
                (x + 1) * self.grid_size, (y + 1) * self.grid_size,
                fill=color, outline="white"
            )
        
        # 绘制食物
        fx, fy = self.food
        self.canvas.create_rectangle(
            fx * self.grid_size, fy * self.grid_size,
            (fx + 1) * self.grid_size, (fy + 1) * self.grid_size,
            fill="red", outline="white"
        )
        
        # 游戏结束提示
        if self.game_over:
            self.canvas.create_text(
                self.canvas_width // 2, self.canvas_height // 2,
                text=f"游戏结束！得分：{self.score}\n按空格键重启",
                font=("Arial", 16), fill="red"
            )

    def game_loop(self):
        """游戏主循环"""
        if not self.game_over:
            self.move_snake()
        self.draw_game()
        # 定时刷新
        self.root.after(self.speed, self.game_loop)

    def restart_game(self, event=None):
        """重启游戏"""
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.direction = "Right"
        self.food = self.generate_food()
        self.score = 0
        self.score_label.config(text=f"得分：{self.score}")
        self.game_over = False

if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()