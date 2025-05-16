def calculate_central_meridian():
    try:
        # 获取用户输入的经度
        longitude = float(input("请输入经度值(输入-1退出): "))
        
        if longitude == -1:
            print("程序已退出")
            return -1, -1
            
        if longitude < 0 or longitude > 180:
            print("经度值必须在0到180之间！")
            return None
            
        # 计算6度带带号
        zone_number_6 = int((longitude + 6) / 6)
        
        # 计算中央经线
        central_meridian_6 = (zone_number_6 * 6) - 3

        # 计算3度带对应的中央经线
        central_meridian_3 = (longitude + 1.5) // 3 * 3
        
        print(f"6度带对应的中央经线: {central_meridian_6}°")
        print(f"3度带对应的中央经线: {central_meridian_3}°")
        
        return central_meridian_6, central_meridian_3
        
    except ValueError:
        print("输入错误!请输入有效的经度数值。")
        return None

if __name__ == "__main__":
    while True:
        result = calculate_central_meridian()
        if result is None:
            continue
        if result[0] == -1:
            break