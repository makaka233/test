# -*- coding: utf-8 -*-
import sys
import io
import codecs
import serial  # type: ignore
import keyboard  # type: ignore
import time
a=10
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

class PositionController:
    def __init__(self):
        self.move_distance = 0
        self.current_position = [0, 0]  # 当前坐标初始为(0, 0)
        self.serial_port = None
        # self.zero_offset = [-900.0, 2100.0]  # 移除手动设置零点
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
        keyboard.add_hotkey('up', self.move_positive_y)     # 上键正Y方向
        keyboard.add_hotkey('down', self.move_negative_y)   # 下键负Y方向
        keyboard.add_hotkey('left', self.move_negative_x)   # 左键负X方向
        keyboard.add_hotkey('right', self.move_positive_x)  # 右键正X方向
        keyboard.add_hotkey('r', self.reset_move_distance)   # 按 'r' 键重新设置移动距离
        # keyboard.add_hotkey('z', self.set_current_position_as_zero)  # 按 'z' 键删除设置零点功能

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

            # 计算实际绝对坐标
            absolute_x = self.current_position[0]  # 不再加上零点偏移
            absolute_y = self.current_position[1]  # 不再加上零点偏移
            
            move_command = f"X{absolute_x} Y{absolute_y}\n"  
            self.serial_port.write(move_command.encode('utf-8'))  
            
            print(f"发送命令: {move_command.strip()}")
            print(f"当前相对坐标: X{self.current_position[0]} Y{self.current_position[1]}")
            print(f"实际绝对坐标: X{absolute_x} Y{absolute_y}")
            
            sys.stdout.flush()  
            
            time.sleep(0.5)  

        except Exception as e:
            print(f"移动出错: {e}")

    def close_serial_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("串口已关闭")

    def start(self):
        print("按 ESC 退出程序")
        keyboard.wait('esc')
        self.close_serial_port()  

def main():
    controller = PositionController()
    controller.start()

if __name__ == "__main__":
    main()
