from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

APPIUM_SERVER = 'http://localhost:4723'

options = UiAutomator2Options()
options.platform_name = "Android"
options.platform_version = "11"
options.device_name = "2a36f8ac"
options.app_package = "com.earth.bdspace"
options.app_activity = "com.earth.bdspace.ui.activity.HomeActivity"
options.automation_name = "UiAutomator2"
options.set_capability("ignoreHiddenApiPolicyError", True)
options.set_capability("noReset", True)
#当设备上已安装uiautomator2包，可以设置
#options.set_capability("skipServerInstallation",True)

def get_central_area(driver):
    """计算屏幕中央区域"""
    window_size = driver.get_window_size()
    area_width = int(window_size['width'] * 0.3)  # 减小区域宽度
    area_height = int(window_size['height'] * 0.3)  # 减小区域高度
    left = (window_size['width'] - area_width) // 2
    top = (window_size['height'] - area_height) // 2
    return {
        'width': area_width,
        'height': area_height,
        'left': max(0, left),
        'top': max(0, top)
    }
#vivo x7 percent 0.7  
def perform_pinch_close(driver):
    """执行缩小操作"""
    area = get_central_area(driver)
    driver.execute_script('mobile: pinchCloseGesture', {
        'percent': 0.3,  # 从0.6调整为0.3，缩小幅度增大
        'angle': 45,      # 新增斜角参数（30-60度范围）
        'top': area['top'],
        'width': area['width'],
        'height': area['height'],
        'speed': 1500
    })
    print("缩小操作完成")
    time.sleep(2)

def perform_pinch_open(driver):
    """执行放大操作"""
    area = get_central_area(driver)
    driver.execute_script('mobile: pinchOpenGesture', {
        'percent': 0.7,  # 从0.6调整为0.7，放大倍数增大
        'angle': 135,     # 反向斜角（120-150度）
        'left': area['left'],
        'top': area['top'],
        'width': area['width'],
        'height': area['height'],
        'speed': 1500
    })
    print("放大操作完成")
    time.sleep(2)

def main():
    try:
        driver = webdriver.Remote(APPIUM_SERVER, options=options)
        print("连接成功")  
        start_time = time.time()
        timeout = 600  # 10分钟
        time.sleep(5)

        while time.time() - start_time < timeout:
            # 执行10次缩小
            for i in range(10):
                perform_pinch_close(driver)
                print(f"已完成缩小操作 {i+1}/10 次")

            # 执行10次放大
            for i in range(10):
                perform_pinch_open(driver)
                print(f"已完成放大操作 {i+1}/10 次")
        
            print(f"持续运行时间: {int(time.time() - start_time)}秒")
            time.sleep(10)
    except KeyboardInterrupt:
        print("手动停止")
    finally:
        if 'driver' in locals():
            driver.quit()
            print("驱动关闭")

if __name__ == '__main__':
    main()