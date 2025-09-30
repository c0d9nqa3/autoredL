# -*- coding: utf-8 -*-
import time
import subprocess
import os


def set_gpio_cmd(pin, value):
    """使用系统命令设置GPIO"""
    try:
        # 使用echo和tee命令
        cmd = f"echo {value} | sudo tee /sys/class/gpio/gpio{pin}/value"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"设置GPIO {pin} 值失败: {e}")
        return False


def pwm_servo_cmd(pin, angle):
    """PWM控制舵机"""
    duty_cycle = 2.5 + (angle / 180.0) * 10.0

    for _ in range(50):
        set_gpio_cmd(pin, 1)
        time.sleep(duty_cycle / 1000.0)
        set_gpio_cmd(pin, 0)
        time.sleep((20 - duty_cycle) / 1000.0)


def test_servo_cmd(pin, name):
    """测试舵机"""
    print(f"测试 {name} (GPIO {pin})")

    try:
        angles = [0, 90, 180]
        for angle in angles:
            print(f"{name}: {angle}度")
            pwm_servo_cmd(pin, angle)
            time.sleep(2)
        return True
    except Exception as e:
        print(f"测试 {name} 失败: {e}")
        return False


# 测试舵机
print("舵机测试开始...")

# 测试舵机1（水平控制，GPIO6）
if test_servo_cmd(6, "舵机1（水平）"):
    print("舵机1测试成功")
else:
    print("舵机1测试失败")

# 测试舵机2（垂直控制，GPIO5）
if test_servo_cmd(5, "舵机2（垂直）"):
    print("舵机2测试成功")
else:
    print("舵机2测试失败")

print("测试完成")