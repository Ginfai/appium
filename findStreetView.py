from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import csv
import datetime
import os

# 设置 Chrome 选项
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# 设置 ChromeDriver 路径
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 打开目标网站
driver.get("https://www.streetviewfun.com/top-100/")

# 等待页面加载完成
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "gdrts-grid-item"))
)

# 提取所有 <td class="gdrts-grid-item"> 中的链接
links = []
td_elements = driver.find_elements(By.CLASS_NAME, "gdrts-grid-item")
for td in td_elements:
    try:
        # 等待 <a> 标签加载完成
        a_tag = WebDriverWait(td, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
        link = a_tag.get_attribute("href")
        links.append(link)
    except TimeoutException:
        print(f"未找到 <a> 标签：{td.text}")

# 遍历每个链接，进入详情页并提取街景链接
street_view_links = []
for link in links:
    driver.get(link)
    try:
        # 使用显式等待替代 sleep
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "goo.gl/maps")]'))
        )
        a_tag = driver.find_element(By.XPATH, '//a[contains(@href, "goo.gl/maps")]')
        street_view_link = a_tag.get_attribute("href")
        # 获取标题作为描述
        title = driver.title
        street_view_links.append({"link": street_view_link, "description": title})
        print(f"成功获取街景链接：{street_view_link}")
    except TimeoutException:
        print(f"页面加载超时：{link}")
    except NoSuchElementException:
        print(f"页面中未找到街景链接：{link}")
    except Exception as e:
        print(f"发生未知错误：{link}，错误类型：{type(e).__name__}，错误信息：{str(e)}")

# 关闭浏览器
driver.quit()

# 创建输出目录
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(output_dir, exist_ok=True)

# 生成带时间戳的文件名
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"street_view_links_{timestamp}.csv"
filepath = os.path.join(output_dir, filename)

# 写入CSV文件
with open(filepath, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['link', 'description'])
    writer.writeheader()
    writer.writerows(street_view_links)

# 输出结果
print(f"\n共找到 {len(street_view_links)} 个街景链接")
print(f"结果已保存到文件：{filepath}")