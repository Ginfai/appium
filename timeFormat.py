import pandas as pd
from datetime import datetime, timedelta

# 读取CSV文件
df = pd.read_excel(r'C:\Users\thread0\Downloads\LTS-cn-north-4-2025-1-15.xlsx')

# 打印原始列名
print("原始列名：", df.columns)

# 去除列名前后的多余引号
df.columns = [col.strip("'") for col in df.columns]

# 打印处理后的列名
print("处理后的列名：", df.columns)

# 去掉__client_time__列中的多余引号
#df['__client_time__'] = df['__client_time__'].str.replace("'", "")

# 将时间戳转换为datetime对象（UTC时间）
df['__client_time__'] = pd.to_datetime(df['__client_time__'], unit='ms')

# 将UTC时间转换为东八区时间（UTC+8）
df['__client_time__'] = df['__client_time__'] + timedelta(hours=8)

# 将datetime对象格式化为yyyy-mm-dd hh:mm:ss
df['__client_time__'] = df['__client_time__'].dt.strftime('%Y-%m-%d %H:%M:%S')

# 保存转换后的数据到新的CSV文件（可选）
df.to_excel('LTS-cn-north-4-2025-1-15_converted.xlsx', index=False)

# 打印转换后的数据
print(df)