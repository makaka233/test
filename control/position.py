# -*- coding: utf-8 -*-
import sys
import io
import codecs
import serial  # type: ignore
import keyboard  # type: ignore
import time
from threading import Thread

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

class PositionController:
    def __init__(self):
        self.move_distance = 0
        self.current_position = [0, 0]  # 当前坐标初始为(0, 0)
        self.serial_port = None
        self.is_listening = True  # 用于控制位置监听线程
        self.setup_serial_port()  # 设置串口
        self.setup_move_distance()  # 设置移动距离
        self.setup_movement_controls()  # 设置移动控制
        # 启动位置监听线程
        self.start_position_listener()

    def setup_serial_port(self):
        try:
            self.serial_port = serial.Serial(
                port='COM4',     
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
        keyboard.add_hotkey('r', self.reset_move_distance)   # 按 'r' 重新设置移动距离
        keyboard.add_hotkey('p', self.request_current_position)  # 按 'p' 键主动请求当前位置

        print("移动控制已就绪:")
        print("↑ Y轴正方向移动")
        print("↓ Y轴负方向移动")
        print("← X轴负方向移动")
        print("→ X轴正方向移动")
        print("按 'r' 重新设置移动距离")
        print("按 'p' 查看当前位置")
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
        self.execute_move(0, self.move_distance)

    def move_negative_y(self):
        print(f"Y轴负方向移动 {self.move_distance} mm")
        self.execute_move(0, -self.move_distance)

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

            absolute_x = self.current_position[0]
            absolute_y = self.current_position[1]
            
            move_command = f"X{absolute_x} Y{absolute_y}\n"  
            self.serial_port.write(move_command.encode('utf-8'))  
            
            print(f"发送命令: {move_command.strip()}")
            print(f"当前相对坐标: X{self.current_position[0]} Y{self.current_position[1]}")
            print(f"实际绝对坐标: X{absolute_x} Y{absolute_y}")
            
            sys.stdout.flush()  
            time.sleep(0.5)  

        except Exception as e:
            print(f"移动出错: {e}")

    def request_current_position(self):
        """主动请求设备当前位置"""
        try:
            # 发送位置查询命令（需根据设备协议修改，此处为示例）
            query_command = "GET_POS\n"
            self.serial_port.write(query_command.encode('utf-8'))
            print("已发送位置查询请求，等待设备响应...")
        except Exception as e:
            print(f"请求位置出错: {e}")

    def start_position_listener(self):
        """启动线程监听设备回传的位置信息"""
        def listen():
            while self.is_listening and self.serial_port.is_open:
                try:
                    # 读取设备返回的数据（假设设备会主动回传或响应查询）
                    response = self.serial_port.readline().decode('utf-8').strip()
                    if response:
                        self.parse_position_response(response)
                except Exception as e:
                    # 忽略读取超时等正常错误
                    if "timed out" not in str(e).lower():
                        print(f"监听位置出错: {e}")
                time.sleep(0.1)  # 降低CPU占用

        # 启动监听线程
        self.listener_thread = Thread(target=listen, daemon=True)
        self.listener_thread.start()

    def parse_position_response(self, response):
        """解析设备返回的位置信息（需根据设备实际协议修改）"""
        # 假设设备返回格式为 "POS:X123.45 Y678.90"
        if response.startswith("POS:"):
            try:
                pos_data = response[4:].strip()
                x_str, y_str = pos_data.split()
                x = float(x_str[1:])  # 去除"X"前缀
                y = float(y_str[1:])  # 去除"Y"前缀
                
                # 更新当前位置
                self.current_position = [x, y]
                print(f"\n收到设备位置: X{x} Y{y}")
                print(f"已更新当前坐标为: X{x} Y{y}")
            except Exception as e:
                print(f"解析位置数据失败: {e}，原始数据: {response}")

    def close_serial_port(self):
        self.is_listening = False  # 停止监听线程
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