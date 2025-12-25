# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import time
from threading import Thread
import keyboard
import csv
import json
import os

class AdvancedCoordinateController:
    def __init__(self, root):
        # 主窗口配置
        self.root = root
        self.root.title("高精度坐标路径控制器")
        self.root.geometry("950x700")
        self.root.minsize(800, 600)
        
        # 核心参数
        self.serial_port = None          # 串口对象
        self.current_x = 0.0             # 当前X坐标
        self.current_y = 0.0             # 当前Y坐标
        self.zero_x = 0.0                # 零点X偏移
        self.zero_y = 0.0                # 零点Y偏移
        self.move_step = 1.0             # 单次移动步长(mm)
        self.is_moving = False           # 运动状态标记
        self.deadzone = (0, 1900)        # 运动范围限制(X/Y: 0-1900mm)
        self.path_points = []            # 路径点列表 [(x1,y1),(x2,y2),...]
        self.execution_delay = 0.1       # 路径点执行间隔(秒)
        
        # 初始化界面
        self.setup_ui()
        # 初始化串口
        self.init_serial()
        # 绑定键盘事件
        self.bind_hotkeys()

    def setup_ui(self):
        # ========== 整体布局：左右分栏 ==========
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：控制区（占比60%）
        left_frame = ttk.Frame(main_paned, width=570)
        main_paned.add(left_frame, weight=6)
        
        # 右侧：路径点管理区（占比40%）
        right_frame = ttk.Frame(main_paned, width=380)
        main_paned.add(right_frame, weight=4)

        # ==================== 左侧控制区 ====================
        # 串口状态区
        status_frame = ttk.Frame(left_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.serial_status = tk.StringVar(value="串口状态：未连接")
        ttk.Label(status_frame, textvariable=self.serial_status).pack(side=tk.LEFT, padx=5)

        # 零点设置区
        zero_frame = ttk.LabelFrame(left_frame, text="零点控制")
        zero_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            zero_frame, 
            text="设置当前位置为零点 (Z)", 
            command=self.set_zero,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        ttk.Label(zero_frame, text="零点偏移：").pack(side=tk.LEFT, padx=10)
        self.zero_label = tk.StringVar(value=f"X: {self.zero_x:.2f} | Y: {self.zero_y:.2f} mm")
        ttk.Label(zero_frame, textvariable=self.zero_label).pack(side=tk.LEFT)

        # 坐标显示区
        coord_frame = ttk.LabelFrame(left_frame, text="当前坐标（相对零点）")
        coord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        coord_display = ttk.Frame(coord_frame)
        coord_display.pack(padx=20, pady=15)
        
        self.x_display = tk.StringVar(value=f"X坐标：{self.current_x:.2f} mm")
        self.y_display = tk.StringVar(value=f"Y坐标：{self.current_y:.2f} mm")
        
        ttk.Label(coord_display, textvariable=self.x_display, font=("Arial", 14)).grid(row=0, column=0, padx=20)
        ttk.Label(coord_display, textvariable=self.y_display, font=("Arial", 14)).grid(row=0, column=1, padx=20)

        # 手动控制区
        control_frame = ttk.LabelFrame(left_frame, text="手动运动控制")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
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
        
        ttk.Button(direction_frame, text="↑ 上 (Y+)", command=lambda: self.move(0, 1)).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(direction_frame, text="← 左 (X-)", command=lambda: self.move(-1, 0)).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(direction_frame, text="↓ 下 (Y-)", command=lambda: self.move(0, -1)).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(direction_frame, text="→ 右 (X+)", command=lambda: self.move(1, 0)).grid(row=1, column=2, padx=5, pady=5)
        
        # 单坐标执行区
        exec_single_frame = ttk.LabelFrame(left_frame, text="单坐标执行")
        exec_single_frame.pack(fill=tk.X, padx=5, pady=5)
        
        single_input_frame = ttk.Frame(exec_single_frame)
        single_input_frame.pack(padx=20, pady=10)
        
        ttk.Label(single_input_frame, text="目标X：").grid(row=0, column=0, padx=5)
        self.target_x_single = ttk.Entry(single_input_frame, width=12)
        self.target_x_single.grid(row=0, column=1, padx=5)
        
        ttk.Label(single_input_frame, text="目标Y：").grid(row=0, column=2, padx=5)
        self.target_y_single = ttk.Entry(single_input_frame, width=12)
        self.target_y_single.grid(row=0, column=3, padx=5)
        
        ttk.Button(single_input_frame, text="执行单坐标", command=self.execute_single_target).grid(row=0, column=4, padx=10)
        self.stop_btn = ttk.Button(single_input_frame, text="停止运动", command=self.stop_movement, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=5, padx=5)

        # 路径执行设置
        path_exec_frame = ttk.LabelFrame(left_frame, text="路径执行设置")
        path_exec_frame.pack(fill=tk.X, padx=5, pady=5)
        
        exec_set_frame = ttk.Frame(path_exec_frame)
        exec_set_frame.pack(padx=20, pady=10)
        
        ttk.Label(exec_set_frame, text="点间隔(秒)：").grid(row=0, column=0, padx=5)
        self.delay_entry = ttk.Entry(exec_set_frame, width=8)
        self.delay_entry.insert(0, str(self.execution_delay))
        self.delay_entry.grid(row=0, column=1, padx=5)
        ttk.Button(exec_set_frame, text="设置间隔", command=self.update_delay).grid(row=0, column=2, padx=5)
        
        self.exec_path_btn = ttk.Button(exec_set_frame, text="执行路径点", command=self.execute_path_points, state=tk.DISABLED)
        self.exec_path_btn.grid(row=0, column=3, padx=10)
        
        # 状态提示区
        self.status_text = tk.StringVar(value="就绪 - 请设置零点后开始操作")
        status_bar = ttk.Label(
            left_frame, 
            textvariable=self.status_text,
            relief=tk.SUNKEN,
            padding=5
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # ==================== 右侧路径点管理区 ====================
        # 路径点操作区
        path_oper_frame = ttk.LabelFrame(right_frame, text="路径点操作")
        path_oper_frame.pack(fill=tk.X, padx=5, pady=5)
        
        oper_btn_frame = ttk.Frame(path_oper_frame)
        oper_btn_frame.pack(padx=10, pady=8)
        
        # 添加当前位置为路径点
        ttk.Button(oper_btn_frame, text="添加当前位置", command=self.add_current_to_path).grid(row=0, column=0, padx=5, pady=5)
        # 手动添加路径点
        ttk.Button(oper_btn_frame, text="手动添加点", command=self.add_manual_point).grid(row=0, column=1, padx=5, pady=5)
        # 删除选中点
        ttk.Button(oper_btn_frame, text="删除选中点", command=self.delete_selected_point).grid(row=0, column=2, padx=5, pady=5)
        # 清空路径点
        ttk.Button(oper_btn_frame, text="清空路径", command=self.clear_path_points).grid(row=0, column=3, padx=5, pady=5)
        
        # 路径点保存/加载
        file_oper_frame = ttk.Frame(path_oper_frame)
        file_oper_frame.pack(padx=10, pady=8)
        
        ttk.Button(file_oper_frame, text="保存为CSV", command=self.save_path_to_csv).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(file_oper_frame, text="保存为JSON", command=self.save_path_to_json).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_oper_frame, text="加载CSV", command=self.load_path_from_csv).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(file_oper_frame, text="加载JSON", command=self.load_path_from_json).grid(row=0, column=3, padx=5, pady=5)
        
        # 路径点列表显示
        path_list_frame = ttk.LabelFrame(right_frame, text="路径点列表")
        path_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 列表表头
        columns = ("序号", "X坐标(mm)", "Y坐标(mm)")
        self.path_tree = ttk.Treeview(path_list_frame, columns=columns, show="headings", height=15)
        self.path_tree.heading("序号", text="序号")
        self.path_tree.heading("X坐标(mm)", text="X坐标(mm)")
        self.path_tree.heading("Y坐标(mm)", text="Y坐标(mm)")
        
        # 设置列宽
        self.path_tree.column("序号", width=60, anchor=tk.CENTER)
        self.path_tree.column("X坐标(mm)", width=120, anchor=tk.CENTER)
        self.path_tree.column("Y坐标(mm)", width=120, anchor=tk.CENTER)
        
        # 滚动条
        tree_scroll = ttk.Scrollbar(path_list_frame, orient=tk.VERTICAL, command=self.path_tree.yview)
        self.path_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.path_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    def init_serial(self):
        """初始化串口连接"""
        try:
            self.serial_port = serial.Serial(
                port="COM4",
                baudrate=115200,
                timeout=0.1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,  # 修正属性名
                bytesize=serial.EIGHTBITS
            )
            self.serial_status.set("串口状态：已连接 (COM3)")
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
        # 添加当前点快捷键
        keyboard.add_hotkey('a', self.add_current_to_path)
        # 退出快捷键
        keyboard.add_hotkey('esc', self.root.quit)

    def set_zero(self):
        """设置当前位置为零点"""
        self.zero_x = self.current_x + self.zero_x
        self.zero_y = self.current_y + self.zero_y
        self.current_x = 0.0
        self.current_y = 0.0
        self.update_coord_display()
        self.zero_label.set(f"X: {self.zero_x:.2f} | Y: {self.zero_y:.2f} mm")
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
            self.step_entry.delete(0, tk.END)
            self.step_entry.insert(0, str(self.move_step))

    def update_delay(self):
        """更新路径点执行间隔"""
        try:
            new_delay = float(self.delay_entry.get())
            if new_delay < 0.05 or new_delay > 10:
                raise ValueError("间隔必须在0.05-10秒之间")
            self.execution_delay = new_delay
            self.status_text.set(f"路径点执行间隔已更新为：{new_delay:.2f} 秒")
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的间隔值：{e}\n请输入0.05-10之间的数字")
            self.delay_entry.delete(0, tk.END)
            self.delay_entry.insert(0, str(self.execution_delay))

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

    def execute_single_target(self):
        """执行单个目标坐标移动"""
        try:
            # 获取输入坐标
            target_x = float(self.target_x_single.get())
            target_y = float(self.target_y_single.get())
            
            # 范围检查
            if not (self.deadzone[0] <= target_x <= self.deadzone[1] and
                    self.deadzone[0] <= target_y <= self.deadzone[1]):
                raise ValueError(f"坐标超出运动范围{self.deadzone}")
            
            self.is_moving = True
            self.stop_btn.config(state=tk.NORMAL)
            self.status_text.set(f"正在移动到目标坐标：({target_x:.2f}, {target_y:.2f})")
            
            # 启动线程执行移动
            Thread(target=self._move_to_target, args=(target_x, target_y), daemon=True).start()
            
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的坐标值：{e}\n请输入0-1900之间的数字")

    def _move_to_target(self, target_x, target_y):
        """后台执行目标坐标移动"""
        try:
            # 计算总移动距离
            dx_total = target_x - self.current_x
            dy_total = target_y - self.current_y
            # 计算需要的步数（至少1步）
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
                self.root.after(0, lambda s=step+1, t=total_steps: self.status_text.set(
                    f"移动中：{s}/{t} 步 | 当前坐标：({self.current_x:.2f}, {self.current_y:.2f})"
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
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def stop_movement(self):
        """停止当前运动"""
        self.is_moving = False
        self.status_text.set("运动已停止")
        self.stop_btn.config(state=tk.DISABLED)
        self.exec_path_btn.config(state=tk.NORMAL if self.path_points else tk.DISABLED)
        messagebox.showinfo("停止", "已停止当前运动")

    def update_coord_display(self):
        """更新坐标显示"""
        self.x_display.set(f"X坐标：{self.current_x:.2f} mm")
        self.y_display.set(f"Y坐标：{self.current_y:.2f} mm")

    # ==================== 路径点管理核心功能 ====================
    def add_current_to_path(self):
        """添加当前位置到路径点"""
        point = (self.current_x, self.current_y)
        self.path_points.append(point)
        self.update_path_tree()
        self.status_text.set(f"已添加当前位置到路径点：({self.current_x:.2f}, {self.current_y:.2f})")
        self.exec_path_btn.config(state=tk.NORMAL)

    def add_manual_point(self):
        """手动输入添加路径点"""
        try:
            x = float(tk.simpledialog.askstring("手动添加点", "请输入X坐标(mm)："))
            y = float(tk.simpledialog.askstring("手动添加点", "请输入Y坐标(mm)："))
            
            # 范围检查
            if not (self.deadzone[0] <= x <= self.deadzone[1] and
                    self.deadzone[0] <= y <= self.deadzone[1]):
                raise ValueError(f"坐标超出运动范围{self.deadzone}")
            
            self.path_points.append((x, y))
            self.update_path_tree()
            self.status_text.set(f"已手动添加路径点：({x:.2f}, {y:.2f})")
            self.exec_path_btn.config(state=tk.NORMAL)
        except ValueError as e:
            messagebox.showerror("输入错误", f"无效的坐标值：{e}\n请输入0-1900之间的数字")
        except TypeError:
            # 用户取消输入
            pass

    def delete_selected_point(self):
        """删除选中的路径点"""
        try:
            selected = self.path_tree.selection()[0]
            index = int(self.path_tree.item(selected, "values")[0]) - 1
            del self.path_points[index]
            self.update_path_tree()
            self.status_text.set(f"已删除路径点 #{index+1}")
            if not self.path_points:
                self.exec_path_btn.config(state=tk.DISABLED)
        except IndexError:
            messagebox.showwarning("选择错误", "请先选中要删除的路径点")

    def clear_path_points(self):
        """清空所有路径点"""
        if messagebox.askyesno("确认清空", "是否确定清空所有路径点？"):
            self.path_points.clear()
            self.update_path_tree()
            self.status_text.set("已清空所有路径点")
            self.exec_path_btn.config(state=tk.DISABLED)

    def update_path_tree(self):
        """更新路径点列表显示"""
        # 清空现有内容
        for item in self.path_tree.get_children():
            self.path_tree.delete(item)
        # 添加新内容
        for i, (x, y) in enumerate(self.path_points, 1):
            self.path_tree.insert("", tk.END, values=(i, f"{x:.2f}", f"{y:.2f}"))

    def execute_path_points(self):
        """执行所有路径点"""
        if not self.path_points:
            messagebox.showwarning("空路径", "路径点列表为空，请先添加路径点")
            return
            
        if self.is_moving:
            messagebox.showwarning("运动中", "当前正在执行移动，请先停止")
            return
            
        self.is_moving = True
        self.exec_path_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_text.set(f"开始执行路径点，共{len(self.path_points)}个点，间隔{self.execution_delay:.2f}秒")
        
        # 启动线程执行路径
        Thread(target=self._execute_path_worker, daemon=True).start()

    def _execute_path_worker(self):
        """路径执行工作线程"""
        try:
            for i, (target_x, target_y) in enumerate(self.path_points, 1):
                if not self.is_moving:
                    break
                    
                # 更新状态
                self.root.after(0, lambda idx=i, cnt=len(self.path_points), x=target_x, y=target_y: self.status_text.set(
                    f"执行路径点 {idx}/{cnt}：({x:.2f}, {y:.2f})"
                ))
                
                # 移动到当前路径点
                self._move_to_single_point(target_x, target_y)
                
                # 路径点间隔
                if i < len(self.path_points) and self.is_moving:
                    time.sleep(self.execution_delay)
            
            if self.is_moving:
                self.root.after(0, lambda: self.status_text.set(
                    f"路径执行完成！共执行 {len(self.path_points)} 个路径点"
                ))
                self.root.after(0, lambda: messagebox.showinfo("执行完成", f"已完成所有{len(self.path_points)}个路径点的移动"))
            else:
                self.root.after(0, lambda: self.status_text.set("路径执行已被手动停止"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("执行失败", f"路径执行失败：{e}"))
            self.root.after(0, lambda: self.status_text.set(f"路径执行失败：{str(e)[:20]}..."))
        finally:
            self.is_moving = False
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.exec_path_btn.config(state=tk.NORMAL))

    def _move_to_single_point(self, target_x, target_y):
        """移动到单个路径点（内部调用）"""
        # 计算总移动距离
        dx_total = target_x - self.current_x
        dy_total = target_y - self.current_y
        total_steps = max(abs(int(dx_total / self.move_step)), abs(int(dy_total / self.move_step)), 1)
        
        # 分步移动
        for step in range(total_steps):
            if not self.is_moving:
                break
                
            step_x = dx_total / total_steps
            step_y = dy_total / total_steps
            
            self.current_x += step_x
            self.current_y += step_y
            
            # 发送串口指令
            abs_x = self.current_x + self.zero_x
            abs_y = self.current_y + self.zero_y
            if self.serial_port and self.serial_port.is_open:
                cmd = f"X{abs_x:.2f} Y{abs_y:.2f}\n"
                self.serial_port.write(cmd.encode("utf-8"))
            
            self.root.after(0, self.update_coord_display)
            time.sleep(0.05)
        
        # 最终校准
        self.current_x = target_x
        self.current_y = target_y
        self.root.after(0, self.update_coord_display)

    # ==================== 数据保存/加载功能 ====================
    def save_path_to_csv(self):
        """保存路径点为CSV格式（便于Excel/数据分析工具处理）"""
        if not self.path_points:
            messagebox.showwarning("空路径", "路径点列表为空，无需保存")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存路径点为CSV"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(["序号", "X坐标(mm)", "Y坐标(mm)", "零点偏移X", "零点偏移Y", "保存时间"])
                # 写入数据
                import datetime
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for i, (x, y) in enumerate(self.path_points, 1):
                    writer.writerow([i, f"{x:.2f}", f"{y:.2f}", f"{self.zero_x:.2f}", f"{self.zero_y:.2f}", now])
            
            self.status_text.set(f"路径点已保存为CSV：{os.path.basename(file_path)}")
            messagebox.showinfo("保存成功", f"已将{len(self.path_points)}个路径点保存为CSV文件")
        except Exception as e:
            messagebox.showerror("保存失败", f"CSV文件保存失败：{e}")

    def save_path_to_json(self):
        """保存路径点为JSON格式（便于编程处理）"""
        if not self.path_points:
            messagebox.showwarning("空路径", "路径点列表为空，无需保存")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="保存路径点为JSON"
        )
        if not file_path:
            return
            
        try:
            # 构造JSON数据结构
            data = {
                "metadata": {
                    "zero_offset_x": self.zero_x,
                    "zero_offset_y": self.zero_y,
                    "save_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "deadzone": self.deadzone,
                    "total_points": len(self.path_points)
                },
                "path_points": [{"index": i+1, "x": round(x, 2), "y": round(y, 2)} for i, (x, y) in enumerate(self.path_points)]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            self.status_text.set(f"路径点已保存为JSON：{os.path.basename(file_path)}")
            messagebox.showinfo("保存成功", f"已将{len(self.path_points)}个路径点保存为JSON文件")
        except Exception as e:
            messagebox.showerror("保存失败", f"JSON文件保存失败：{e}")

    def load_path_from_csv(self):
        """从CSV加载路径点"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="加载CSV格式路径点"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # 跳过表头
                next(reader)
                new_points = []
                for row in reader:
                    if len(row) >= 3:
                        x = float(row[1])
                        y = float(row[2])
                        # 范围检查
                        if self.deadzone[0] <= x <= self.deadzone[1] and self.deadzone[0] <= y <= self.deadzone[1]:
                            new_points.append((x, y))
            
            if new_points:
                self.path_points = new_points
                self.update_path_tree()
                self.exec_path_btn.config(state=tk.NORMAL)
                self.status_text.set(f"已从CSV加载{len(new_points)}个路径点")
                messagebox.showinfo("加载成功", f"从CSV文件加载了{len(new_points)}个路径点")
            else:
                messagebox.showwarning("加载失败", "CSV文件中未找到有效路径点")
        except Exception as e:
            messagebox.showerror("加载失败", f"CSV文件加载失败：{e}")

    def load_path_from_json(self):
        """从JSON加载路径点"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="加载JSON格式路径点"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            new_points = []
            for point in data.get("path_points", []):
                x = point.get("x", 0.0)
                y = point.get("y", 0.0)
                if self.deadzone[0] <= x <= self.deadzone[1] and self.deadzone[0] <= y <= self.deadzone[1]:
                    new_points.append((x, y))
            
            if new_points:
                self.path_points = new_points
                self.update_path_tree()
                self.exec_path_btn.config(state=tk.NORMAL)
                # 可选：加载零点偏移
                if "metadata" in data:
                    self.zero_x = data["metadata"].get("zero_offset_x", 0.0)
                    self.zero_y = data["metadata"].get("zero_offset_y", 0.0)
                    self.zero_label.set(f"X: {self.zero_x:.2f} | Y: {self.zero_y:.2f} mm")
                
                self.status_text.set(f"已从JSON加载{len(new_points)}个路径点")
                messagebox.showinfo("加载成功", f"从JSON文件加载了{len(new_points)}个路径点")
            else:
                messagebox.showwarning("加载失败", "JSON文件中未找到有效路径点")
        except Exception as e:
            messagebox.showerror("加载失败", f"JSON文件加载失败：{e}")

    def __del__(self):
        """析构函数：关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

# 补充datetime导入（避免JSON保存时出错）
import datetime

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
    
    app = AdvancedCoordinateController(root)
    root.mainloop()