import re
import csv
from datetime import datetime

def extract_street_view_info(url):
    # Extract Street View ID
    street_view_id_match = re.search(r'1s([A-Za-z0-9_-]+)', url)
    street_view_id = street_view_id_match.group(1) if street_view_id_match else None

    # Extract yaw and pitch using 'h' for yaw and 't' for pitch
    yaw_match = re.search(r'([0-9.-]+)h,', url)  # Match the value before 'h,'
    yaw = yaw_match.group(1) if yaw_match else None

    pitch_match = re.search(r'([0-9.-]+)t', url)  # Match the value before 't'
    pitch = pitch_match.group(1) if pitch_match else None

    return street_view_id, yaw, pitch

def extract_key_info(url):
    street_view_id, yaw, pitch = extract_street_view_info(url)
    key_info = {
        'street_view_id': street_view_id,
        'yaw': yaw,
        'pitch': pitch
    }
    return key_info

def process_batch_urls():
    print("请输入多个URL（每行一个），输入空行结束：")
    urls = []
    while True:
        line = input().strip()
        if not line:
            break
        urls.append(line)
    
    # 创建CSV文件名（使用时间戳避免重名）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'street_view_data_{timestamp}.csv'
    
    # 写入CSV文件
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['url', '街景ID', '旋转角', '俯仰角']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        print("\n处理结果：")
        print("-" * 50)
        for i, url in enumerate(urls, 1):
            try:
                key_info = extract_key_info(url)
                # 写入CSV
                writer.writerow({
                    'url': url,
                    '街景ID': key_info['street_view_id'],
                    '旋转角': key_info['yaw'],
                    '俯仰角': key_info['pitch']
                })
                
                # 控制台输出
                print(f"\n链接 {i}:")
                print(f'街景ID--panoId: {key_info["street_view_id"]}')
                print(f'旋转角--yaw: {key_info["yaw"]}')
                print(f'俯仰角--pitch: {key_info["pitch"]}')
            except Exception as e:
                print(f'\n链接 {i} 处理出错: {e}')
                # 写入错误信息到CSV
                writer.writerow({
                    'url': url,
                    '街景ID': '处理出错',
                    '旋转角': '处理出错',
                    '俯仰角': '处理出错'
                })
            print("-" * 50)
    
    print(f"\n数据已保存到文件: {csv_filename}")

if __name__ == "__main__":
    while True:
        print("\n1. 批量处理URLs并保存到CSV")
        print("2. 退出程序")
        choice = input("请选择操作 (1/2): ")
        
        if choice == "2":
            print("程序已退出。")
            break
        elif choice == "1":
            process_batch_urls()
        else:
            print("无效的选择，请重试。")
