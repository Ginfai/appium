from lxml import etree
import sys
import tkinter as tk
from tkinter import filedialog # 导入文件对话框模块

def correct_kml_coordinates(input_kml_path, output_kml_path, delta_lon, delta_lat):
    """
    Reads a KML file, applies a coordinate offset to all <coordinates> and <gx:coord> tags,
    and saves the result to a new KML file.

    Args:
        input_kml_path (str): Path to the input KML file.
        output_kml_path (str): Path to save the corrected output KML file.
        delta_lon (float): The amount to add to the longitude.
        delta_lat (float): The amount to add to the latitude.
    """
    try:
        # Parse the KML file
        # recover=True helps in parsing slightly malformed XML if necessary
        parser = etree.XMLParser(ns_clean=True, recover=True)
        tree = etree.parse(input_kml_path, parser)
        root = tree.getroot()

        # Define KML and Google Extension (gx) namespaces
        # Ensure these match the namespaces used in your KML file if they are different
        ns = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'gx': 'http://www.google.com/kml/ext/2.2' # Google Extension namespace
        }

        # Find all <coordinates> (standard KML) and <gx:coord> (Google Extension) elements
        # The | operator combines the results of two XPath queries
        all_coord_elements = root.xpath('//kml:coordinates | //gx:coord', namespaces=ns)

        print(f"找到 {len(all_coord_elements)} 个坐标元素 (<coordinates> 或 <gx:coord>)。")

        corrected_point_count = 0
        skipped_element_count = 0

        for element in all_coord_elements:
            original_text = element.text
            if original_text is None: # Skip empty elements
                skipped_element_count += 1
                print(f"Warning: Skipping empty coordinate element: {etree.tostring(element, encoding='unicode').strip()}")
                continue

            original_text = original_text.strip()
            corrected_text = ""
            element_corrected_count = 0 # Counter for points corrected within this element

            # --- Handle <coordinates> tags (standard KML) ---
            if element.tag == '{http://www.opengis.net/kml/2.2}coordinates':
                # <coordinates> format: lon,lat[,alt] space-separated
                tuples_str = original_text.split() # Split by space into individual lon,lat[,alt] strings
                corrected_tuples = []
                for coord_tuple_str in tuples_str:
                    try:
                        coords = coord_tuple_str.split(',')
                        if len(coords) >= 2: # Must have at least longitude and latitude
                            lon = float(coords[0])
                            lat = float(coords[1])
                            alt_part = "," + coords[2] if len(coords) > 2 else "" # Keep altitude and leading comma if present

                            # Apply the offset
                            corrected_lon = lon + delta_lon
                            corrected_lat = lat + delta_lat

                            # Reconstruct the corrected tuple string
                            corrected_tuple_str = f"{corrected_lon},{corrected_lat}{alt_part}"
                            corrected_tuples.append(corrected_tuple_str)
                            element_corrected_count += 1
                        else:
                            print(f"Warning: <coordinates> 内的坐标组格式不正确 '{coord_tuple_str}'。跳过此坐标组。")
                            skipped_element_count += 1 # Count this as a skipped point within an element

                    except (ValueError, IndexError) as e:
                        print(f"Warning: 无法解析 <coordinates> 内的坐标组 '{coord_tuple_str}'。跳过此坐标组。错误: {e}")
                        skipped_element_count += 1 # Count this as a skipped point within an element
                        pass # Skip problematic tuples

                # Join corrected tuples back with spaces
                corrected_text = " ".join(corrected_tuples)
                corrected_point_count += element_corrected_count # Add to total count

                # Update element text only if some tuples were corrected
                if corrected_tuples:
                     element.text = corrected_text
                elif element_corrected_count == 0 and tuples_str: # If original text wasn't empty but all points failed
                     print(f"Warning: <coordinates> 元素 '{original_text}' 中所有坐标组均无法解析。保留原始内容。")
                     # Optionally set text to empty or a placeholder, but leaving original is safer
                     # element.text = "" # Or set to original_text if you want to keep it

            # --- Handle <gx:coord> tags (Google Extension) ---
            elif element.tag == '{http://www.google.com/kml/ext/2.2}coord':
                 # <gx:coord> format: lon lat alt space-separated
                 parts = original_text.split() # Split by space

                 try:
                     # gx:coord typically has exactly 3 parts: lon lat alt
                     if len(parts) == 3:
                         lon = float(parts[0])
                         lat = float(parts[1])
                         alt = parts[2] # Keep altitude as string

                         # Apply the offset
                         corrected_lon = lon + delta_lon
                         corrected_lat = lat + delta_lat

                         # Reconstruct the corrected string (space separated lon lat alt)
                         corrected_gx_coord_str = f"{corrected_lon} {corrected_lat} {alt}"

                         # Update the element's text
                         element.text = corrected_gx_coord_str
                         corrected_point_count += 1 # Count this single point
                         element_corrected_count += 1

                     else:
                         print(f"Warning: <gx:coord> 元素格式不正确 '{original_text}'。期望 '经度 纬度 高度'。跳过此元素。")
                         skipped_element_count += 1 # Count this as a skipped element

                 except (ValueError, IndexError) as e:
                     print(f"Warning: 无法解析 <gx:coord> '{original_text}'。跳过此元素。错误: {e}")
                     skipped_element_count += 1 # Count this as a skipped element
                     pass # Skip problematic gx:coord

            else:
                # This case should ideally not be reached with the current XPath,
                # but it's good for robustness if the XPath or KML structure is unexpected.
                print(f"Warning: 发现未知元素标签 {element.tag}。跳过。")
                skipped_element_count += 1


        print(f"修正完成！共处理 {len(all_coord_elements)} 个坐标元素。成功修正 {corrected_point_count} 个坐标点。跳过 {skipped_element_count} 个格式错误或无法解析的坐标元素/点。")


        # Save the modified tree to a new file
        # Use xml_declaration=True to ensure the <?xml version="1.0" encoding="utf-8"?> header is included
        # Use pretty_print=True for readability of the output file
        tree.write(output_kml_path, pretty_print=True, encoding='utf-8', xml_declaration=True)

        print(f"修正后的文件已保存到 '{output_kml_path}'")

    except FileNotFoundError:
        print(f"错误: 输入文件未找到 '{input_kml_path}'")
    except etree.XMLSyntaxError as e:
        print(f"错误: 无法解析 KML 文件 '{input_kml_path}'。请检查文件是否为有效的 XML 格式。错误详情: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")
        # You might want to print the traceback for debugging:
        # import traceback
        # traceback.print_exc()

# --- 脚本执行部分 (使用文件对话框) ---
# 请确保此部分代码紧跟在上面的函数定义之后
if __name__ == "__main__":
    # 定义偏差量 (基于你已知的一个点的偏差计算得出)
    longitude_offset = +0.000007
    latitude_offset = -0.000116

    # 初始化 Tkinter 根窗口 (并隐藏它)
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口，只显示对话框

    # 弹出文件选择对话框，让用户选择输入 KML 文件
    input_file = filedialog.askopenfilename(
        title="选择需要修正的 KML 文件",
        filetypes=(("KML 文件", "*.kml"), ("所有文件", "*.*")) # 过滤文件类型
    )

    # 检查用户是否选择了文件 (如果取消对话框，input_file 会是空字符串)
    if not input_file:
        print("未选择输入文件，脚本退出。")
        sys.exit() # 退出脚本

    # 弹出保存文件对话框，让用户选择保存修正后文件的位置和名称
    # 尝试提供一个默认文件名，例如在原文件名前加上 "corrected_"
    # 这里的分割是为了处理不同操作系统的路径分隔符 / 和 \
    original_filename = input_file.split('/')[-1].split('\\')[-1]
    # 去掉可能的 .kml 扩展名再加前缀，然后defaultextension会确保有.kml
    if original_filename.lower().endswith('.kml'):
        original_filename = original_filename[:-4]
    suggested_output_name = "corrected_" + original_filename


    output_file = filedialog.asksaveasfilename(
        title="保存修正后的 KML 文件为...",
        defaultextension=".kml", # 如果用户没输入扩展名，自动加上 .kml
        filetypes=(("KML 文件", "*.kml"), ("所有文件", "*.*")),
        initialfile=suggested_output_name # 建议的默认文件名
    )

    # 检查用户是否选择了保存位置
    if not output_file:
        print("未选择输出文件路径，脚本退出。")
        sys.exit() # 退出脚本

    # --- 调用修正函数，使用用户选择的文件路径 ---
    print(f"正在读取文件: {input_file}")
    print(f"将保存到文件: {output_file}")
    correct_kml_coordinates(input_file, output_file, longitude_offset, latitude_offset)

    print("修正完成！")