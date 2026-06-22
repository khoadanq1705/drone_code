import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed

async def run():
    # 1. Khởi tạo đối tượng drone
    drone = System()

    # 2. Kết nối tới drone giả lập SITL
    print("Đang kết nối tới drone ảo...")
    await drone.connect(system_address="udp://:14540")

    # Vòng lặp chờ drone kết nối thành công
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Đã kết nối thành công với Drone!")
            break

    # 3. Chờ định vị GPS ổn định
    print("Đang chờ drone định vị GPS ổn định...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("Hệ thống và GPS đã sẵn sàng!")
            break

    # 4. Khởi động động cơ (Arming)
    print("Khởi động động cơ (Arming)...")
    await drone.action.arm()

    # 5. Thiết lập độ cao và Cất cánh
    print("CẤT CÁNH! Drone đang bay lên cao 5 mét...")
    await drone.action.set_takeoff_altitude(8.0)
    await drone.action.takeoff()
    
    # Chờ 8 giây để drone hoàn thành quá trình cất cánh và đứng ổn định ở độ cao 5m
    await asyncio.sleep(8)

    # 6. BẮT ĐẦU BAY THẲNG TIẾN VỀ PHÍA TRƯỚC (Sử dụng chế độ Offboard)
    print("BẮT ĐẦU BAY THẲNG! Tiến về phía trước với vận tốc 2m/s...")
    
    # Thiết lập giá trị vận tốc ban đầu (đứng yên) trước khi bật Offboard
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))

    try:
        # Bật chế độ điều khiển Offboard
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Bật Offboard thất bại do: {error._result.result}. Đang hạ cánh an toàn...")
        await drone.action.land()
        return

    # Ra lệnh cho drone bay thẳng về phía trước với vận tốc 2 m/s (trục X dương)
    # Các tham số: (Vận tốc tiến/lùi, Vận tốc trái/phải, Vận tốc lên/xuống, Tốc độ quay cổ xe)
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(2.0, 0.0, 0.0, 0.0))
    
    # Cho drone duy trì vận tốc này trong 5 giây (2m/s * 5s = bay được đúng 10 mét)
    await asyncio.sleep(5)

    # 7. DỪNG LẠI VÀ TREO MÌNH TRÊN KHÔNG
    print("Đã bay xong 10 mét. Đang giảm tốc độ và đứng yên thả trôi 3 giây...")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    # Tắt chế độ Offboard để trả lại quyền điều khiển tự động cho lệnh Hạ cánh
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Tắt Offboard thất bại: {error._result.result}")

    # 8. Ra lệnh HẠ CÁNH (LAND) tại vị trí hiện tại
    print("Đang thực hiện hạ cánh (LAND)...")
    await drone.action.land()

if __name__ == "__main__":
    # Kích hoạt vòng lặp bất đồng bộ để chạy hàm run()
    asyncio.run(run())


    