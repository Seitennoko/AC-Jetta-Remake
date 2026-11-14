import asyncio
import websockets
import vgamepad as vg
import socket
import ctypes
from ctypes import mmap, Structure, c_int32, c_float, c_wchar

gamepad = vg.VX360Gamepad()

# ================= 神力科莎 (Assetto Corsa) 共享内存映射定义 =================
class SPageFilePhysics(Structure):
    _fields_ = [
        ("packetId", c_int32),
        ("gas", c_float),
        ("brake", c_float),
        ("fuel", c_float),
        ("gear", c_int32),         # 0: R, 1: N, 2: 1挡, 3: 2挡...
        ("rpms", c_int32),         # 当前转速
        ("steerAngle", c_float),
        ("speedKmh", c_float),     # 实时时速 (km/h)
        # 后面字段省略，仅提取仪表盘核心数据
    ]

class SPageFileStatic(Structure):
    _fields_ = [
        ("smVersion", c_wchar * 15),
        ("acVersion", c_wchar * 15),
        ("numberOfSessions", c_int32),
        ("numCars", c_int32),
        ("carModel", c_wchar * 33),
        ("track", c_wchar * 33),
        ("playerName", c_wchar * 33),
        ("playerSurname", c_wchar * 33),
        ("playerNick", c_wchar * 33),
        ("sectorCount", c_int32),
        ("maxTorque", c_float),
        ("maxPower", c_float),
        ("maxRpm", c_int32),        # 该车最大极限转速
    ]

# 安全获取神力科莎共享内存数据的函数
def get_ac_telemetry():
    rpm, max_rpm, speed, gear = 0, 8000, 0, 1
    try:
        # 读取 Physics (转速、时速、档位)
        shm_physics = mmap.mmap(0, ctypes.sizeof(SPageFilePhysics), "Local\\acpm_physics")
        physics = SPageFilePhysics.from_buffer_copy(shm_physics)
        rpm = int(physics.rpms)
        speed = float(physics.speedKmh)
        gear = int(physics.gear)
        shm_physics.close()

        # 读取 Static (红线转速)
        shm_static = mmap.mmap(0, ctypes.sizeof(SPageFileStatic), "Local\\acpm_static")
        static = SPageFileStatic.from_buffer_copy(shm_static)
        if static.maxRpm > 0:
            max_rpm = int(static.maxRpm)
        shm_static.close()

    except Exception:
        # 如果 AC 未运行或尚未进入赛道，回传默认零值
        pass

    return rpm, max_rpm, speed, gear

# 自动获取本机的真实局域网 IP[span_3](start_span)[span_3](end_span)
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# 定时高频向手机端广播赛车物理数据的协程任务
async def telemetry_broadcast_loop(websocket):
    while True:
        try:
            rpm, max_rpm, speed, gear = get_ac_telemetry()
            # 打包 JSON 格式数据发给手机 HTML 仪表盘[span_4](start_span)[span_4](end_span)
            telemetry_data = (
                f'{{"rpm":{rpm},"maxRpm":{max_rpm},"speed":{round(speed,1)},"gear":{gear}}}'
            )
            await websocket.send(telemetry_data)
            await asyncio.sleep(0.03)  # 约 33Hz 的刷新率，兼顾流畅度与性能
        except websockets.exceptions.ConnectionClosed:
            break
        except Exception:
            await asyncio.sleep(0.1)

# 完美兼容新旧版本 websockets 库[span_5](start_span)[span_5](end_span)
async def handle_client(websocket, *args):
    print("\n[状态] 控制端已顺利建立连线，性能全开注入中...")
    
    # 建立连接后，开启后台线程持续向手机发送 telemetry 数据
    telemetry_task = asyncio.create_task(telemetry_broadcast_loop(websocket))

    try:
        async for message in websocket:
            try:
                # 忽略服务端发给客户端的 JSON 反弹
                if message.startswith("{"):
                    continue

                # 解析前端发过来的字符串: X:123,T:0,B:0...[span_6](start_span)[span_6](end_span)
                data = dict(item.split(":") for item in message.split(","))
                
                stick_x = int(data.get("X", 0))
                throttle = int(data.get("T", 0))
                brake    = int(data.get("B", 0))
                
                btn_back  = int(data.get("BK", 0))
                btn_start = int(data.get("ST", 0))
                btn_rb    = int(data.get("RB", 0))
                btn_lb    = int(data.get("LB", 0))
                btn_a     = int(data.get("A", 0))
                btn_y     = int(data.get("Y", 0))

                # 虚拟手柄核心注入[span_7](start_span)[span_7](end_span)
                gamepad.left_joystick(x_value=stick_x, y_value=0)
                gamepad.right_trigger(value=throttle)
                gamepad.left_trigger(value=brake)

                if btn_back:  gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
                else:         gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
                
                if btn_start: gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
                else:         gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
                
                if btn_rb:    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
                else:         gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
                
                if btn_lb:    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
                else:         gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
                
                if btn_a:     gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                else:         gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                
                if btn_y:     gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
                else:         gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

                gamepad.update()

            except Exception:
                continue

    except websockets.exceptions.ConnectionClosed:
        print("\n[状态] 控制端已离线。")
    finally:
        telemetry_task.cancel()  # 连接断开时取消数据推送任务
        # 重置虚拟手柄[span_8](start_span)[span_8](end_span)
        gamepad.left_joystick(x_value=0, y_value=0)
        gamepad.right_trigger(value=0)
        gamepad.left_trigger(value=0)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        gamepad.update()
        print("[状态] 安全锁定已触发，虚拟手柄数值已重置。")

async def main():
    local_ip = get_local_ip()
    async with websockets.serve(handle_client, "0.0.0.0", 9999, ping_interval=2, ping_timeout=2):
        print("======================================================")
        print("   AC Telemetry + Controller Server V25.0 双向传输版")
        print(f"     👉 请在手机端连接 IP：{local_ip}")
        print("     👉 端口：9999  |  神力科莎 (AC) 物理内存实时读取中")
        print("======================================================")
        print("正在等待手机端连线...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
