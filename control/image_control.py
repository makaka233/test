# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import serial
import time
from threading import Thread
import math

class PathControllerGUI:
    def __init__(self, root):
        # 主窗口设置
        self.root = root
        self.root.title("设备路径控制器")
        # 设置最小窗口尺寸，避免缩放导致显示不全
        self.root.minsize(800, 600)
        # 使用网格布局替代pack，更好地控制界面比例
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 核心参数配置
        self.DEADZONE_X = (0, 1800)  # X轴死区范围
        self.DEADZONE_Y = (0, 1800)  # Y轴死区范围
        self.move_step = 1.0         # 单次移动步长(mm)
        self.path_points = []        # 存储绘制的路径点
        self.history_stack = []      # 撤销历史栈
        self.current_position = [0.0, 0.0]  # 当前坐标
        self.zero_offset = [0.0, 0.0]       # 零点偏移
        self.serial_port = None             # 串口对象
        self.is_executing = False           # 是否正在执行路径
        
        # 初始化界面
        self.create_widgets()
        # 初始化串口
        self.init_serial()
        
        # 绑定窗口大小变化事件，自动调整画布
        self.root.bind("<Configure>", self.on_window_resize)

    def create_widgets(self):
        # ========== 顶部控制面板 ==========
        top_frame = ttk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        # 让控制面板自适应宽度
        top_frame.grid_columnconfigure(10, weight=1)
        
        # 串口状态显示
        self.serial_status = tk.StringVar(value="串口未连接")
        status_label = ttk.Label(top_frame, textvariable=self.serial_status, relief="solid", padding=5)
        status_label.grid(row=0, column=0, padx=5, pady=2)
        
        # 零点设置按钮
        ttk.Button(top_frame, text="设置当前为零点", command=self.set_zero).grid(row=0, column=1, padx=5, pady=2)
        
        # 步长设置
        ttk.Label(top_frame, text="移动步长(mm):").grid(row=0, column=2, padx=5, pady=2)
        self.step_entry = ttk.Entry(top_frame, width=8)
        self.step_entry.insert(0, str(self.move_step))
        self.step_entry.grid(row=0, column=3, padx=5, pady=2)
        ttk.Button(top_frame, text="设置步长", command=self.set_step).grid(row=0, column=4, padx=5, pady=2)
        
        # 路径控制按钮
        ttk.Button(top_frame, text="清空路径", command=self.clear_path).grid(row=0, column=5, padx=5, pady=2)
        ttk.Button(top_frame, text="撤销上一步", command=self.undo_last).grid(row=0, column=6, padx=5, pady=2)
        
        # 执行控制按钮
        self.exec_btn = ttk.Button(top_frame, text="执行路径", command=self.execute_path)
        self.exec_btn.grid(row=0, column=7, padx=5, pady=2)
        self.stop_btn = ttk.Button(top_frame, text="停止执行", command=self.stop_execution, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=8, padx=5, pady=2)
        
        # ========== 坐标显示区域 ==========
        coord_frame = ttk.LabelFrame(self.root, text="当前坐标")
        coord_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        self.x_coord_var = tk.StringVar(value="X: 0.00 mm")
        self.y_coord_var = tk.StringVar(value="Y: 0.00 mm")
        x_label = ttk.Label(coord_frame, textvariable=self.x_coord_var, font=("Arial", 12))
        x_label.grid(row=0, column=0, padx=20, pady=5)
        y_label = ttk.Label(coord_frame, textvariable=self.y_coord_var, font=("Arial", 12))
        y_label.grid(row=0, column=1, padx=20, pady=5)
        
        # ========== 绘图区域 ==========
        draw_frame = ttk.LabelFrame(self.root, text="路径绘制区 (X:0-1900, Y:0-1900)")
        draw_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        # 让绘图区域自适应窗口大小
        draw_frame.grid_rowconfigure(0, weight=1)
        draw_frame.grid_columnconfigure(0, weight=1)
        
        # 画布设置（自适应大小）
        self.canvas = tk.Canvas(draw_frame, bg="white", highlightthickness=1, highlightbackground="gray")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 添加滚动条（防止画布内容超出显示）
        v_scroll = ttk.Scrollbar(draw_frame, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(draw_frame, orient="horizontal", command=self.canvas.xview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # 绘制死区边界
        self.draw_deadzone_border()
        
        # 绑定画布事件
        self.canvas.bind("<Button-1>", self.add_path_point)  # 左键添加点
        self.canvas.bind("<B1-Motion>", self.draw_line)      # 拖动绘制线
        
        # ========== 状态信息 ==========
        self.status_var = tk.StringVar(value="就绪 - 点击画布绘制路径点，拖动可绘制连续路径")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", padding=5)
        status_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

    def on_window_resize(self, event):
        """窗口大小变化时重新绘制界面"""
        if event.widget == self.root:
            # 重新绘制路径和边界
            self.draw_path()
            # 更新画布滚动区域
            self.update_canvas_scroll_region()

    def update_canvas_scroll_region(self):
        """更新画布滚动区域"""
        scale = min(self.canvas.winfo_width()/1900, self.canvas.winfo_height()/1900)
        canvas_width = 10 + 1900 * scale + 20
        canvas_height = 10 + 1900 * scale + 20
        self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

    def draw_deadzone_border(self):
        """绘制死区边界框（适配画布大小）"""
        # 清空边界标记
        self.canvas.delete("border")
        
        # 计算缩放系数，保证完整显示0-1900范围
        scale = min(self.canvas.winfo_width()/1900, self.canvas.winfo_height()/1900)
        if scale == 0:  # 避免初始时画布大小为0
            scale = 0.1
        
        # 绘制边界矩形
        border_padding = 10
        self.canvas.create_rectangle(
            border_padding, border_padding,
            border_padding + 1900*scale, border_padding + 1900*scale,
            outline="red", width=2, tag="border"
        )
        
        # 标注坐标轴（自适应位置）
        self.canvas.create_text(
            border_padding + 1900*scale/2, border_padding - 5, 
            text="X轴 (0-1900mm)", anchor=tk.N, tag="border"
        )
        self.canvas.create_text(
            border_padding - 5, border_padding + 1900*scale/2, 
            text="Y轴 (0-1900mm)", anchor=tk.E, angle=90, tag="border"
        )
        
        # 标注刻度（关键位置）
        for x in [0, 500, 1000, 1500, 1900]:
            self.canvas.create_line(
                border_padding + x*scale, border_padding - 5,
                border_padding + x*scale, border_padding + 5,
                tag="border", fill="red"
            )
            self.canvas.create_text(
                border_padding + x*scale, border_padding - 10,
                text=str(x), tag="border", font=("Arial", 8)
            )
        
        for y in [0, 500, 1000, 1500, 1900]:
            self.canvas.create_line(
                border_padding - 5, border_padding + y*scale,
                border_padding + 5, border_padding + y*scale,
                tag="border", fill="red"
            )
            self.canvas.create_text(
                border_padding - 10, border_padding + y*scale,
                text=str(y), tag="border", font=("Arial", 8)
            )
        
        self.update_canvas_scroll_region()

    def init_serial(self):
        """初始化串口连接"""
        try:
            self.serial_port = serial.Serial(
                port="COM4",
                baudrate=115200,
                timeout=0.1
            )
            self.serial_status.set("串口已连接 (COM3)")
            self.status_var.set("串口连接成功，可开始绘制路径")
        except Exception as e:
            self.serial_status.set(f"串口连接失败: {str(e)[:20]}...")
            messagebox.showwarning("串口警告", f"无法连接串口：{str(e)}\n程序将以模拟模式运行")

    def set_zero(self):
        """设置当前位置为零点"""
        # 记录当前绝对位置作为零点偏移
        self.zero_offset = [
            self.current_position[0] + self.zero_offset[0],
            self.current_position[1] + self.zero_offset[1]
        ]
        # 重置当前相对位置
        self.current_position = [0.0, 0.0]
        self.update_coord_display()
        messagebox.showinfo("零点设置", "已将当前位置设为坐标原点")
        self.status_var.set("已设置新的坐标原点")

    def set_step(self):
        """设置移动步长"""
        try:
            step = float(self.step_entry.get())
            if step <= 0 or step > 50:
                raise ValueError("步长必须在0-50mm之间")
            self.move_step = step
            self.status_var.set(f"移动步长已设置为 {step} mm")
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的步长值：{str(e)}")
            self.step_entry.delete(0, tk.END)
            self.step_entry.insert(0, str(self.move_step))

    def add_path_point(self, event):
        """添加路径点（点击画布）"""
        if self.is_executing:
            messagebox.showwarning("执行中", "路径执行中，无法编辑路径")
            return
            
        # 获取画布实际大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width == 0 or canvas_height == 0:
            return
            
        # 转换画布坐标到实际坐标（考虑缩放和偏移）
        scale = min(canvas_width/1900, canvas_height/1900)
        if scale == 0:
            scale = 0.1
        border_padding = 10
        
        x = (event.x - border_padding) / scale
        y = (event.y - border_padding) / scale
        
        # 死区检查
        if not (self.DEADZONE_X[0] <= x <= self.DEADZONE_X[1] and
                self.DEADZONE_Y[0] <= y <= self.DEADZONE_Y[1]):
            messagebox.showwarning("超出范围", f"该位置({x:.1f}, {y:.1f})超出设备运动范围(0-1900mm)")
            return
        
        # 记录历史（用于撤销）
        self.history_stack.append(self.path_points.copy())
        
        # 添加路径点
        self.path_points.append((x, y))
        self.draw_path()
        self.status_var.set(f"已添加路径点 ({x:.1f}, {y:.1f})，共{len(self.path_points)}个点")

    def draw_line(self, event):
        """拖动绘制连续路径"""
        if self.is_executing or len(self.path_points) == 0:
            return
            
        # 获取画布实际大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width == 0 or canvas_height == 0:
            return
            
        # 转换画布坐标到实际坐标
        scale = min(canvas_width/1900, canvas_height/1900)
        if scale == 0:
            scale = 0.1
        border_padding = 10
        
        x = (event.x - border_padding) / scale
        y = (event.y - border_padding) / scale
        
        # 死区检查
        if not (self.DEADZONE_X[0] <= x <= self.DEADZONE_X[1] and
                self.DEADZONE_Y[0] <= y <= self.DEADZONE_Y[1]):
            return
        
        # 计算与上一个点的距离，超过步长才添加新点
        last_x, last_y = self.path_points[-1]
        distance = math.hypot(x - last_x, y - last_y)
        
        if distance >= self.move_step:
            self.history_stack.append(self.path_points.copy())
            self.path_points.append((x, y))
            self.draw_path()

    def draw_path(self):
        """绘制所有路径点和连线（适配画布大小）"""
        # 清空画布（保留边界）
        self.canvas.delete("path")
        self.draw_deadzone_border()
        
        if len(self.path_points) == 0:
            return
        
        # 获取画布实际大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale = min(canvas_width/1900, canvas_height/1900)
        if scale == 0:
            scale = 0.1
        border_padding = 10
        
        # 绘制路径线
        if len(self.path_points) > 1:
            points = []
            for (x, y) in self.path_points:
                points.append(border_padding + x * scale)
                points.append(border_padding + y * scale)
            self.canvas.create_line(points, tag="path", fill="blue", width=2)
        
        # 绘制路径点
        for i, (x, y) in enumerate(self.path_points):
            cx = border_padding + x * scale
            cy = border_padding + y * scale
            # 第一个点标红，其他标蓝
            color = "red" if i == 0 else "blue"
            self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, tag="path", fill=color)
            # 标注点序号（自适应位置，避免超出画布）
            text_x = cx + 8 if cx + 8 < self.canvas.winfo_width() else cx - 15
            text_y = cy if cy < self.canvas.winfo_height() else cy - 10
            self.canvas.create_text(text_x, text_y, text=str(i+1), tag="path", font=("Arial", 8))

    def clear_path(self):
        """清空路径"""
        if self.is_executing:
            messagebox.showwarning("执行中", "路径执行中，无法清空路径")
            return
            
        self.history_stack.append(self.path_points.copy())
        self.path_points.clear()
        self.draw_path()
        self.status_var.set("路径已清空")

    def undo_last(self):
        """撤销上一步操作"""
        if not self.history_stack:
            messagebox.showinfo("撤销", "没有可撤销的操作")
            return
            
        if self.is_executing:
            messagebox.showwarning("执行中", "路径执行中，无法撤销")
            return
            
        self.path_points = self.history_stack.pop()
        self.draw_path()
        self.status_var.set(f"已撤销上一步，当前路径点数量：{len(self.path_points)}")

    def update_coord_display(self):
        """更新坐标显示"""
        self.x_coord_var.set(f"X: {self.current_position[0]:.2f} mm")
        self.y_coord_var.set(f"Y: {self.current_position[1]:.2f} mm")

    def execute_path(self):
        """执行绘制的路径"""
        if self.is_executing:
            return
            
        if len(self.path_points) == 0:
            messagebox.showwarning("空路径", "请先绘制路径再执行")
            return
            
        # 检查串口连接
        if not self.serial_port or not self.serial_port.is_open:
            if not messagebox.askyesno("串口未连接", "串口未连接，是否以模拟模式执行？"):
                return
        
        self.is_executing = True
        # 更新按钮状态
        self.exec_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("开始执行路径...")
        
        # 启动线程执行路径，避免界面卡死
        exec_thread = Thread(target=self._path_execution_worker, daemon=True)
        exec_thread.start()

    def _path_execution_worker(self):
        """路径执行工作线程"""
        # 获取画布参数
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale = min(canvas_width/1900, canvas_height/1900)
        if scale == 0:
            scale = 0.1
        border_padding = 10
        
        prev_x, prev_y = self.current_position
        
        for i, (target_x, target_y) in enumerate(self.path_points):
            if not self.is_executing:
                break
                
            # 更新状态
            self.status_var.set(f"执行路径点 {i+1}/{len(self.path_points)}: ({target_x:.1f}, {target_y:.1f})")
            
            # 绘制当前执行点
            self.canvas.delete("current")
            cx = border_padding + target_x * scale
            cy = border_padding + target_y * scale
            self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, tag="current", fill="green", width=2)
            
            # 死区最后检查
            if not (self.DEADZONE_X[0] <= target_x <= self.DEADZONE_X[1] and
                    self.DEADZONE_Y[0] <= target_y <= self.DEADZONE_Y[1]):
                self.status_var.set(f"路径点 {i+1} 超出运动范围，执行终止")
                messagebox.showerror("超出范围", f"路径点 {i+1} ({target_x:.1f}, {target_y:.1f}) 超出设备运动范围")
                break
            
            # 发送移动指令
            try:
                # 计算绝对坐标（考虑零点偏移）
                abs_x = target_x + self.zero_offset[0]
                abs_y = target_y + self.zero_offset[1]
                
                # 发送串口指令
                if self.serial_port and self.serial_port.is_open:
                    command = f"X{abs_x:.2f} Y{abs_y:.2f}\n"
                    self.serial_port.write(command.encode("utf-8"))
                    time.sleep(0.1)  # 等待设备响应
                
                # 更新当前位置
                self.current_position = [target_x, target_y]
                self.update_coord_display()
                prev_x, prev_y = target_x, target_y
                
                # 移动间隔
                time.sleep(0.2)
                
            except Exception as e:
                self.status_var.set(f"执行出错: {str(e)[:20]}...")
                messagebox.showerror("执行错误", f"路径点 {i+1} 执行失败：{str(e)}")
                break
        
        # 执行完成/停止
        self.is_executing = False
        self.exec_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.canvas.delete("current")
        
        if i == len(self.path_points)-1 and self.is_executing is False:
            self.status_var.set(f"路径执行完成！共执行 {len(self.path_points)} 个路径点")
            messagebox.showinfo("执行完成", f"路径执行完成！共执行 {len(self.path_points)} 个路径点")
        else:
            self.status_var.set("路径执行已停止")

    def stop_execution(self):
        """停止路径执行"""
        self.is_executing = False
        self.status_var.set("正在停止路径执行...")

    def run(self):
        """运行主程序"""
        # 初始化画布滚动区域
        self.update_canvas_scroll_region()
        self.root.mainloop()

# 程序入口
if __name__ == "__main__":
    # 设置高清显示适配
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = PathControllerGUI(root)
    app.run()