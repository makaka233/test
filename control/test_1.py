# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
from threading import Thread
import keyboard

class CoordinateController:
    def __init__(self, root):
        # 主窗口配置
        self.root = root
        self.root.title("高精度坐标控制器")
        self.root.geometry("800x500")
        self.root.minsize(600, 400)
        
        # 核心参数
        self.serial_port = None          # 串口对象
        self.current_x = 0.0             # 当前X坐标
        self.current_y = 0.0             # 当前Y坐标
        self.zero_x = 0.0                # 零点X偏移
        self.zero_y = 0.0                # 零点Y偏移
        self.move_step = 1.0             # 单次移动步长(mm)
        self.is_moving = False           # 运动状态标记
        self.deadzone = (0, 1900)        # 运动范围限制(X/Y: 0-1900mm)
        
        # 初始化界面
        self.setup_ui()
        # 初始化串口
        self.init_serial()
        # 绑定键盘事件
        self.bind_hotkeys()

    def setup_ui(self):
        # ========== 顶部串口状态区 ==========
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.serial_status = tk.StringVar(value="串口状态：未连接")
        ttk.Label(status_frame, textvariable=self.serial_status).pack(side=tk.LEFT, padx=5)
        
        # ========== 零点设置区 ==========
        zero_frame = ttk.LabelFrame(self.root, text="零点控制")
        zero_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            zero_frame, 
            text="设置当前位置为零点", 
            command=self.set_zero,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        ttk.Label(zero_frame, text="当前零点偏移：").pack(side=tk.LEFT, padx=10)
        self.zero_label = tk.StringVar(value=f"X: {self.zero_x:.2f} mm | Y: {self.zero_y:.2f} mm")
        ttk.Label(zero_frame, textvariable=self.zero_label).pack(side=tk.LEFT)

        # ========== 坐标显示区 ==========
        coord_frame = ttk.LabelFrame(self.root, text="当前坐标（相对零点）")
        coord_frame.pack(fill=tk.X, padx=10, pady=5)
        
        coord_display = ttk.Frame(coord_frame)
        coord_display.pack(padx=20, pady=15)
        
        self.x_display = tk.StringVar(value=f"X坐标：{self.current_x:.2f} mm")
        self.y_display = tk.StringVar(value=f"Y坐标：{self.current_y:.2f} mm")
        
        ttk.Label(coord_display, textvariable=self.x_display, font=("Arial", 14)).grid(row=0, column=0, padx=20)
        ttk.Label(coord_display, textvariable=self.y_display, font=("Arial", 14)).grid(row=0, column=1, padx=20)

        # ========== 手动控制区 ==========
        control_frame = ttk.LabelFrame(self.root, text="手动运动控制")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 步长设置
        step_frame = ttk.Frame(control_frame)
        step_frame.pack(pady=5)
        
        ttk.Label(step_frame, text="移动步长(mm)：").grid(row=0, column=0, padx=5)
        self.step_entry = ttk.Entry(step_frame, width=10)
        self.step_entry.insert(0, str(self.move_step))
        self.step_entry.grid(row=0, column=1, padx=5)
        ttk.Button(step_frame, text="确认步长", command=self.update_step).grid(row=0, column=2, padx=5)
        
        # 方向按键区
        direction_frame = ttk.Frame(control_frame)
        direction_frame.pack(pady=10)
        
        # 方向按钮布局
        ttk.Button(direction_frame, text="↑ 上 (Y+)", command=lambda: self.move(0, 1)).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(direction_frame, text="← 左 (X-)", command=lambda: self.move(-1, 0)).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(direction_frame, text="↓ 下 (Y-)", command=lambda: self.move(0, -1)).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(direction_frame, text="→ 右 (X+)", command=lambda: self.move(1, 0)).grid(row=1, column=2, padx=5, pady=5)
        
        # 按键提示
        ttk.Label(direction_frame, text="键盘方向键也可控制", font=("Arial", 8)).grid(row=3, column=0, columnspan=3, pady=5)

        # ========== 坐标输入执行区 ==========
        exec_frame = ttk.LabelFrame(self.root, text="坐标输入执行")
        exec_frame.pack(fill=tk.X, padx=10, pady=5)
        
        input_frame = ttk.Frame(exec_frame)
        input_frame.pack(padx=20, pady=15)
        
        # X坐标输入
        ttk.Label(input_frame, text="目标X坐标：").grid(row=0, column=0, padx=5, pady=5)
        self.target_x = ttk.Entry(input_frame, width=15)
        self.target_x.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="mm").grid(row=0, column=2, padx=5)
        
        # Y坐标输入
        ttk.Label(input_frame, text="目标Y坐标：").grid(row=1, column=0, padx=5, pady=5)
        self.target_y = ttk.Entry(input_frame, width=15)
        self.target_y.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="mm").grid(row=1, column=2, padx=5)
        
        # 执行按钮
        exec_btn_frame = ttk.Frame(exec_frame)
        exec_btn_frame.pack(pady=5)
        
        self.exec_btn = ttk.Button(
            exec_btn_frame, 
            text="执行坐标移动", 
            command=self.execute_target,
            style="Accent.TButton"
        )
        self.exec_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(
            exec_btn_frame, 
            text="停止运动", 
            command=self.stop_movement,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # ========== 状态提示区 ==========
        self.status_text = tk.StringVar(value="就绪 - 请设置零点后开始操作")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_text,
            relief=tk.SUNKEN,
            padding=5
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    def init_serial(self):
        """初始化串口连接"""
        try:
            # 串口参数可根据实际设备调整
            self.serial_port = serial.Serial(
                port="COM4",
                baudrate=115200,
                timeout=0.1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.serial_status.set("串口状态：已连接 (COM4)")
            self.status_text.set("串口连接成功，可开始操作")
        except Exception as e:
            self.serial_status.set(f"串口状态：连接失败 - {str(e)[:20]}...")
            messagebox.showwarning(
                "串口警告",
                f"无法连接串口：{e}\n程序将以模拟模式运行，无法控制实际设备"
            )

    def bind_hotkeys(self):
        """绑定键盘热键"""
        # 方向键控制
        keyboard.add_hotkey('up', lambda: self.move(0, 1))
        keyboard.add_hotkey('down', lambda: self.move(0, -1))
        keyboard.add_hotkey('left', lambda: self.move(-1, 0))
        keyboard.add_hotkey('right', lambda: self.move(1, 0))
        # 零点设置快捷键
        keyboard.add_hotkey('z', self.set_zero)
        # 退出快捷键
        keyboard.add_hotkey('esc', self.root.quit)

    def set_zero(self):
        """设置当前位置为零点"""
        self.zero_x = self.current_x + self.zero_x
        self.zero_y = self.current_y + self.zero_y
        self.current_x = 0.0
        self.current_y = 0.0
        # 更新显示
        self.update_coord_display()
        self.zero_label.set(f"X: {self.zero_x:.2f} mm | Y: {self.zero_y:.2f} mm")
        self.status_text.set("已将当前位置设为新零点")
        messagebox.showinfo("零点设置", "成功将当前位置设为坐标零点！")

    def update_step(self):
        """更新移动步长"""
        try:
            new_step = float(self.step_entry.get())
            if new_step <= 0 or new_step > 50:
                raise ValueError("步长必须在0.1-50mm之间")
            self.move_step = new_step
            self.status_text.set(f"移动步长已更新为：{new_step:.2f} mm")
            messagebox.showinfo("步长更新", f"步长设置成功：{new_step:.2f} mm")
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的步长值：{e}\n请输入0.1-50之间的数字")
            # 恢复原有值
            self.step_entry.delete(0, tk.END)
            self.step_entry.insert(0, str(self.move_step))

    def move(self, dx, dy):
        """执行单次移动（dx: X方向 -1/0/1, dy: Y方向 -1/0/1）"""
        if self.is_moving:
            return
            
        # 计算目标坐标
        target_x = self.current_x + dx * self.move_step
        target_y = self.current_y + dy * self.move_step
        
        # 范围检查
        if not (self.deadzone[0] <= target_x <= self.deadzone[1] and
                self.deadzone[0] <= target_y <= self.deadzone[1]):
            messagebox.showwarning(
                "超出范围",
                f"目标位置({target_x:.2f}, {target_y:.2f})超出运动范围{self.deadzone}"
            )
            return
        
        # 执行移动
        self.is_moving = True
        try:
            # 计算绝对坐标（含零点偏移）
            abs_x = target_x + self.zero_x
            abs_y = target_y + self.zero_y
            
            # 发送串口指令
            if self.serial_port and self.serial_port.is_open:
                cmd = f"X{abs_x:.2f} Y{abs_y:.2f}\n"
                self.serial_port.write(cmd.encode("utf-8"))
                time.sleep(0.05)  # 设备响应时间
            
            # 更新当前坐标
            self.current_x = target_x
            self.current_y = target_y
            self.update_coord_display()
            self.status_text.set(f"已移动：X{dx*self.move_step:+.2f} Y{dy*self.move_step:+.2f} mm")
            
        except Exception as e:
            messagebox.showerror("移动失败", f"移动指令执行失败：{e}")
        finally:
            self.is_moving = False

    def execute_target(self):
        """执行目标坐标移动"""
        try:
            # 获取输入坐标
            target_x = float(self.target_x.get())
            target_y = float(self.target_y.get())
            
            # 范围检查
            if not (self.deadzone[0] <= target_x <= self.deadzone[1] and
                    self.deadzone[0] <= target_y <= self.deadzone[1]):
                raise ValueError(f"坐标超出运动范围{self.deadzone}")
            
            self.is_moving = True
            self.exec_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_text.set(f"正在移动到目标坐标：({target_x:.2f}, {target_y:.2f})")
            
            # 启动线程执行移动（避免界面卡死）
            Thread(target=self._move_to_target, args=(target_x, target_y), daemon=True).start()
            
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的坐标值：{e}\n请输入0-1900之间的数字")

    def _move_to_target(self, target_x, target_y):
        """后台执行目标坐标移动"""
        try:
            # 计算总移动距离
            dx_total = target_x - self.current_x
            dy_total = target_y - self.current_y
            total_steps = max(abs(int(dx_total / self.move_step)), abs(int(dy_total / self.move_step)), 1)
            
            # 分步移动
            for step in range(total_steps):
                if not self.is_moving:  # 检查是否停止
                    break
                    
                # 计算单步步长
                step_x = dx_total / total_steps
                step_y = dy_total / total_steps
                
                # 更新当前坐标
                self.current_x += step_x
                self.current_y += step_y
                
                # 发送串口指令
                abs_x = self.current_x + self.zero_x
                abs_y = self.current_y + self.zero_y
                if self.serial_port and self.serial_port.is_open:
                    cmd = f"X{abs_x:.2f} Y{abs_y:.2f}\n"
                    self.serial_port.write(cmd.encode("utf-8"))
                
                # 更新显示
                self.root.after(0, self.update_coord_display)
                self.root.after(0, lambda: self.status_text.set(
                    f"移动中：{step+1}/{total_steps} 步 | 当前坐标：({self.current_x:.2f}, {self.current_y:.2f})"
                ))
                
                time.sleep(0.05)  # 移动间隔
            
            # 最终校准
            self.current_x = target_x
            self.current_y = target_y
            self.root.after(0, self.update_coord_display)
            
            if self.is_moving:
                self.root.after(0, lambda: self.status_text.set(
                    f"已到达目标坐标：({target_x:.2f}, {target_y:.2f})"
                ))
            else:
                self.root.after(0, lambda: self.status_text.set("移动已被手动停止"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("执行失败", f"移动到目标坐标失败：{e}"))
            self.root.after(0, lambda: self.status_text.set(f"移动失败：{str(e)[:20]}..."))
        finally:
            self.is_moving = False
            self.root.after(0, lambda: self.exec_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def stop_movement(self):
        """停止当前运动"""
        self.is_moving = False
        self.status_text.set("运动已停止")
        messagebox.showinfo("停止", "已停止当前运动")

    def update_coord_display(self):
        """更新坐标显示"""
        self.x_display.set(f"X坐标：{self.current_x:.2f} mm")
        self.y_display.set(f"Y坐标：{self.current_y:.2f} mm")

    def __del__(self):
        """析构函数：关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

# 程序入口
if __name__ == "__main__":
    # 高DPI适配
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    # 设置按钮样式
    style = ttk.Style()
    style.configure("Accent.TButton", font=("Arial", 10, "bold"))
    
    app = CoordinateController(root)
    root.mainloop()