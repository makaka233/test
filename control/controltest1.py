# -*- coding: utf-8 -*-
import sys
import io
import codecs
import serial  # type: ignore
import keyboard  # type: ignore
import time

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

class PositionController:
    def __init__(self):
        self.move_distance = 0
        self.current_position = [0, 0]  # 当前坐标初始为(0, 0)
        self.serial_port = None
        self.setup_serial_port()  # 设置串口
        self.setup_move_distance()  # 设置移动距离
        self.setup_movement_controls()  # 设置移动控制

    def setup_serial_port(self):
        try:
            self.serial_port = serial.Serial(
                port='COM3',     
                baudrate=115200,   
                timeout=1        
            )
            print("串口已成功打开")
        except serial.SerialException as e:
            print(f"打开串口失败: {e}")
            exit(1)

    def setup_move_distance(self):
        while True:
            try:
                distance = input("请输入每次移动的距离(单位: mm，必须为毫米): ")
                self.move_distance = float(distance)
                print(f"已设置移动距离为 {self.move_distance} mm")
                break
            except ValueError:
                print("请输入有效的数字")
            except Exception as e:
                print(f"发生错误: {e}")

    def setup_movement_controls(self):
        keyboard.add_hotkey('up', self.move_positive_y)     # 上键正Y方向self.move_positive_y
        keyboard.add_hotkey('down', self.move_negative_y)   # 下键负Y方向self.move_negative_y
        keyboard.add_hotkey('left', self.move_negative_x)   # 左键负X方向
        keyboard.add_hotkey('right', self.move_positive_x)  # 右键正X方向
        keyboard.add_hotkey('r', self.reset_move_distance)   # 按 'r' 键重新设置移动距离

        print("移动控制已就绪:")
        print("↑ Y轴正方向移动")
        print("↓ Y轴负方向移动")
        print("← X轴负方向移动")
        print("→ X轴正方向移动")
        print("按 'r' 重新设置移动距离")
        print("按 ESC 退出")

    def reset_move_distance(self):
        print("请按回车键输入新的移动距离")
        while True:
            try:
                distance = input("请输入每次移动的距离(单位: mm，必须为毫米): ")
                self.move_distance = float(distance)
                print(f"已设置移动距离为 {self.move_distance} mm")
                break
            except ValueError:
                print("请输入有效的数字")
            except Exception as e:
                print(f"发生错误: {e}")

    def move_positive_y(self):
        print(f"Y轴正方向移动 {self.move_distance} mm")
        self.execute_move(0, self.move_distance)  # 向上移动，Y坐标增加

    def move_negative_y(self):
        print(f"Y轴负方向移动 {self.move_distance} mm")
        self.execute_move(0, -self.move_distance)  # 向下移动，Y坐标减少

    def move_positive_x(self):
        print(f"X轴正方向移动 {self.move_distance} mm")
        self.execute_move(self.move_distance, 0)

    def move_negative_x(self):
        print(f"X轴负方向移动 {self.move_distance} mm")
        self.execute_move(-self.move_distance, 0)

    def execute_move(self, x, y):
        try:
            self.current_position[0] += x  
            self.current_position[1] += y  
            
            move_command = f"X{self.current_position[0]} Y{self.current_position[1]}\n"  # 使用当前坐标
            self.serial_port.write(move_command.encode('utf-8'))  # 发送命令
            
            print(f"发送命令: {move_command.strip()}")
            print(f"当前坐标: X{self.current_position[0]} Y{self.current_position[1]}")  # 输出当前坐标
            
            # 确保立即刷新输出
            sys.stdout.flush()  # 刷新输出缓冲区
            
            time.sleep(0.5)  # 等待设备处理

        except Exception as e:
            print(f"移动出错: {e}")

    def close_serial_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("串口已关闭")

    def start(self):
        print("按 ESC 退出程序")
        keyboard.wait('esc')
        self.close_serial_port()  # 退出时关闭串口

def main():
    controller = PositionController()
    controller.start()

if __name__ == "__main__":
    main()
