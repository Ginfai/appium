# -*- coding: utf-8 -*- # Added encoding declaration for non-ASCII characters

import tkinter as tk
from tkinter import filedialog, messagebox
from lxml import etree
import sys
import numpy as np
from skimage import transform
import traceback # 导入 traceback 用于打印详细错误信息 (调试用)

# --- 核心修正函数 ---
# 这个函数只负责读取文件，应用变换，并保存文件
# 它不处理文件对话框，也不应该调用 sys.exit()
def correct_kml_coordinates(input_kml_path, output_kml_path, transform_matrix, status_callback=None):
    """
    Reads a KML file from input_kml_path, applies an affine transformation
    to all <coordinates> and <gx:coord> tags using transform_matrix,
    and saves the result to output_kml_path.

    Args:
        input_kml_path (str): Path to the input KML file.
        output_kml_path (str): Path to save the corrected output KML file.
        transform_matrix (skimage.transform.AffineTransform): The calculated affine transform.
        status_callback (function, optional): A function to call with status messages.
                                              Defaults to None (messages will be printed).
    Raises:
        FileNotFoundError: If the input file is not found.
        etree.XMLSyntaxError: If the input file is not valid XML/KML.
        ValueError: If coordinate values cannot be parsed as floats.
        IndexError: If coordinate strings have unexpected structure.
        Exception: For other unexpected errors during processing.
    """
    def update_status(message):
        if status_callback:
            status_callback(message)
        else:
            print(message)

    update_status(f"正在读取文件: {input_kml_path}")

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

        update_status(f"找到 {len(all_coord_elements)} 个坐标元素 (<coordinates> 或 <gx:coord>)。")

        corrected_point_count = 0
        skipped_element_count = 0

        for i, element in enumerate(all_coord_elements):
            original_text = element.text
            if original_text is None or not original_text.strip(): # Skip empty or whitespace-only elements
                skipped_element_count += 1
                # update_status(f"Warning: Skipping empty coordinate element {i+1}.") # Optional detailed warning
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

                            # --- 应用仿射变换 ---
                            original_point = np.array([[lon, lat]]) # 将点转换为 numpy 数组 (需要是二维的 [[lon, lat]])
                            corrected_point = transform_matrix(original_point) # 应用变换
                            corrected_lon = corrected_point[0, 0] # 获取修正后的经度
                            corrected_lat = corrected_point[0, 1] # 获取修正后的纬度
                            # --- 变换结束 ---

                            # Reconstruct the corrected tuple string
                            corrected_tuple_str = f"{corrected_lon},{corrected_lat}{alt_part}"
                            corrected_tuples.append(corrected_tuple_str)
                            element_corrected_count += 1
                        else:
                            # update_status(f"Warning: Element {i+1}: <coordinates> 内的坐标组格式不正确 '{coord_tuple_str}'。跳过此坐标组。") # Optional detailed warning
                            skipped_element_count += 1 # Count this as a skipped point within an element

                    except (ValueError, IndexError) as e:
                        # update_status(f"Warning: Element {i+1}: 无法解析 <coordinates> 内的坐标组 '{coord_tuple_str}'。跳过此坐标组。错误: {e}") # Optional detailed warning
                        skipped_element_count += 1 # Count this as a skipped point within an element
                        pass # Skip problematic tuples

                # Join corrected tuples back with spaces
                corrected_text = " ".join(corrected_tuples)
                corrected_point_count += element_corrected_count # Add to total count

                # Update element text only if some tuples were corrected
                if corrected_tuples:
                     element.text = corrected_text
                # else: # If original text wasn't empty but all points failed
                #      update_status(f"Warning: Element {i+1}: <coordinates> 元素 '{original_text}' 中所有坐标组均无法解析。保留原始内容。") # Optional detailed warning
                     # Optionally set text to empty or a placeholder, but leaving original is safer


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

                         # --- 应用仿射变换 ---
                         original_point = np.array([[lon, lat]]) # 将点转换为 numpy 数组 (需要是二维的 [[lon, lat]])
                         corrected_point = transform_matrix(original_point) # 应用变换
                         corrected_lon = corrected_point[0, 0] # 获取修正后的经度
                         corrected_lat = corrected_point[0, 1] # 获取修正后的纬度
                         # --- 变换结束 ---

                         # Reconstruct the corrected string (space separated lon lat alt)
                         corrected_gx_coord_str = f"{corrected_lon} {corrected_lat} {alt}"

                         # Update the element's text
                         element.text = corrected_gx_coord_str
                         corrected_point_count += 1 # Count this single point
                         element_corrected_count += 1

                     else:
                         # update_status(f"Warning: Element {i+1}: <gx:coord> 元素格式不正确 '{original_text}'。期望 '经度 纬度 高度'。跳过此元素。") # Optional detailed warning
                         skipped_element_count += 1 # Count this as a skipped element

                 except (ValueError, IndexError) as e:
                     # update_status(f"Warning: Element {i+1}: 无法解析 <gx:coord> '{original_text}'。跳过此元素。错误: {e}") # Optional detailed warning
                     skipped_element_count += 1 # Count this as a skipped element
                     pass # Skip problematic gx:coord

            # else: # This case should not be reached with the current XPath
            #      update_status(f"Warning: Element {i+1}: 发现未知元素标签 {element.tag}。跳过。") # Optional detailed warning
            #      skipped_element_count += 1


        update_status(f"修正处理完成。成功修正 {corrected_point_count} 个坐标点。跳过 {skipped_element_count} 个格式错误或无法解析的坐标元素/点。")


        update_status(f"正在保存文件到 '{output_kml_path}'")
        # Save the modified tree to a new file
        # Use xml_declaration=True to ensure the <?xml version="1.0" encoding="utf-8"?> header is included
        # Use pretty_print=True for readability of the output file
        tree.write(output_kml_path, pretty_print=True, encoding='utf-8', xml_declaration=True)
        update_status("文件保存成功。")


    except FileNotFoundError:
        raise FileNotFoundError(f"错误: 输入文件未找到 '{input_kml_path}'")
    except etree.XMLSyntaxError as e:
        raise etree.XMLSyntaxError(f"错误: 无法解析 KML 文件 '{input_kml_path}'。请检查文件是否为有效的 XML 格式。\n错误详情: {e}")
    except Exception as e:
        # Catch any other unexpected errors and raise them
        raise Exception(f"修正过程中发生未知错误: {e}")


# --- GUI Code ---
class KmlCorrectorGUI:
    def __init__(self, master):
        self.master = master
        master.title("KML 坐标修正工具 (基于仿射变换)")

        # Configure the main window grid to be slightly responsive
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_columnconfigure(2, weight=1)
        master.grid_columnconfigure(3, weight=1)
        master.grid_rowconfigure(3, weight=1) # Status area expands

        self.incorrect_entries = []
        self.correct_entries = []
        self.num_points = 5 # Allow input for up to 5 points by default (can be more than 3)

        self.input_file_path = ""
        self.output_file_path = ""

        # --- Coordinate Input Frame ---
        self.coord_frame = tk.LabelFrame(master, text="输入参考点 (至少 3 对)")
        self.coord_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

        # Configure coord_frame columns to expand
        self.coord_frame.grid_columnconfigure(1, weight=1)
        self.coord_frame.grid_columnconfigure(2, weight=1)
        self.coord_frame.grid_columnconfigure(3, weight=1)
        self.coord_frame.grid_columnconfigure(4, weight=1)


        tk.Label(self.coord_frame, text="").grid(row=0, column=0) # Spacer for alignment
        tk.Label(self.coord_frame, text="文件中的错误点", font='TkDefaultFont 9 bold').grid(row=0, column=1, columnspan=2)
        tk.Label(self.coord_frame, text="实际正确点", font='TkDefaultFont 9 bold').grid(row=0, column=3, columnspan=2)

        tk.Label(self.coord_frame, text="经度").grid(row=1, column=1)
        tk.Label(self.coord_frame, text="纬度").grid(row=1, column=2)
        tk.Label(self.coord_frame, text="经度").grid(row=1, column=3)
        tk.Label(self.coord_frame, text="纬度").grid(row=1, column=4)

        for i in range(self.num_points):
            tk.Label(self.coord_frame, text=f"点 {chr(65+i)}:").grid(row=i+2, column=0, sticky="w", padx=5)

            # Incorrect point entries
            incorrect_lon = tk.StringVar()
            incorrect_lat = tk.StringVar()
            entry_inc_lon = tk.Entry(self.coord_frame, textvariable=incorrect_lon, width=20)
            entry_inc_lat = tk.Entry(self.coord_frame, textvariable=incorrect_lat, width=20)
            entry_inc_lon.grid(row=i+2, column=1, padx=2, pady=2, sticky="ew")
            entry_inc_lat.grid(row=i+2, column=2, padx=2, pady=2, sticky="ew")
            self.incorrect_entries.append((incorrect_lon, incorrect_lat))

            # Correct point entries
            correct_lon = tk.StringVar()
            correct_lat = tk.StringVar()
            entry_corr_lon = tk.Entry(self.coord_frame, textvariable=correct_lon, width=20)
            entry_corr_lat = tk.Entry(self.coord_frame, textvariable=correct_lat, width=20)
            entry_corr_lon.grid(row=i+2, column=3, padx=2, pady=2, sticky="ew")
            entry_corr_lat.grid(row=i+2, column=4, padx=2, pady=2, sticky="ew")
            self.correct_entries.append((correct_lon, correct_lat))

        # --- File Selection Frame ---
        self.file_frame = tk.LabelFrame(master, text="文件选择")
        self.file_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

        # Configure file_frame columns to expand
        self.file_frame.grid_columnconfigure(1, weight=1)


        tk.Label(self.file_frame, text="输入 KML 文件:").grid(row=0, column=0, sticky="w", padx=5)
        self.input_file_label = tk.Label(self.file_frame, text="未选择", fg="blue", anchor="w")
        self.input_file_label.grid(row=0, column=1, sticky="ew", padx=5)
        self.input_button = tk.Button(self.file_frame, text="浏览...", command=self.select_input_file)
        self.input_button.grid(row=0, column=2, padx=5, pady=5) # Place button next to label, spanning 2 columns

        tk.Label(self.file_frame, text="输出 KML 文件:").grid(row=1, column=0, sticky="w", padx=5)
        self.output_file_label = tk.Label(self.file_frame, text="未选择", fg="blue", anchor="w")
        self.output_file_label.grid(row=1, column=1, sticky="ew", padx=5)
        self.output_button = tk.Button(self.file_frame, text="保存为...", command=self.select_output_file)
        self.output_button.grid(row=1, column=2, padx=5, pady=5) # Place button next to label


        # --- Control Button ---
        self.correct_button = tk.Button(master, text="开始修正", command=self.start_correction, font='TkDefaultFont 10 bold', bg="green", fg="white")
        self.correct_button.grid(row=2, column=0, columnspan=4, pady=10)

        # --- Status Area ---
        self.status_frame = tk.LabelFrame(master, text="状态信息")
        self.status_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky="nsew") # sticky="nsew" makes it expand

        # Configure status_frame grid
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(0, weight=1)

        self.status_text = tk.Text(self.status_frame, height=8, width=60, state='disabled', wrap='word') # wrap='word' helps with long lines
        self.status_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add a scrollbar to the status text area
        self.status_scrollbar = tk.Scrollbar(self.status_frame, command=self.status_text.yview)
        self.status_scrollbar.grid(row=0, column=1, sticky='ns')
        self.status_text['yscrollcommand'] = self.status_scrollbar.set


        # --- Populate with user's last provided points as default ---
        # Point A: (118.078466,24.481030) -> (118.078465,24.480972)
        # Point B: (118.078727,24.480946) -> (118.078736,24.480891)
        # Point C: (118.078249,24.481114) -> (118.078279,24.481047)
        # Add placeholders for 2 more points if needed

        # default_incorrect = [
        #     ("118.078466", "24.481030"),
        #     ("118.078727", "24.480946"),
        #     ("118.078249", "24.481114"),
        #     ("", ""), # Placeholder for Point D
        #     ("", "")  # Placeholder for Point E
        # ]
        # default_correct = [
        #     ("118.078465", "24.480972"),
        #     ("118.078736", "24.480891"),
        #     ("118.078279,24.481047"), # This one was copied wrong before - should be two parts
        #     ("118.078279", "24.481047"),
        #     ("", ""), # Placeholder for Point D
        #     ("", "")  # Placeholder for Point E
        # ]
        #  # Correcting the default_correct list based on the user's input format
        # default_correct = [
        #     ("118.078465", "24.480972"),
        #     ("118.078736", "24.480891"),
        #     ("118.078279", "24.481047"),
        #     ("", ""), # Placeholder for Point D
        #     ("", "")  # Placeholder for Point E
        # ]


        # for i in range(self.num_points):
        #      if i < len(default_incorrect):
        #         self.incorrect_entries[i][0].set(default_incorrect[i][0])
        #         self.incorrect_entries[i][1].set(default_incorrect[i][1])
        #      if i < len(default_correct):
        #         self.correct_entries[i][0].set(default_correct[i][0])
        #         self.correct_entries[i][1].set(default_correct[i][1])


    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="选择需要修正的 KML 文件",
            filetypes=(("KML 文件", "*.kml"), ("所有文件", "*.*"))
        )
        if file_path:
            self.input_file_path = file_path
            # Display just the filename and indicate selection
            display_name = file_path.split('/')[-1].split('\\')[-1]
            self.input_file_label.config(text=display_name, fg="black")
            self.update_status(f"已选择输入文件: {display_name}")


    def select_output_file(self):
        # Suggest a default name based on input file if selected
        initial_file = ""
        if self.input_file_path:
             original_filename = self.input_file_path.split('/')[-1].split('\\')[-1]
             if original_filename.lower().endswith('.kml'):
                 original_filename = original_filename[:-4]
             initial_file = "corrected_affine_" + original_filename

        file_path = filedialog.asksaveasfilename(
            title="保存修正后的 KML 文件为...",
            defaultextension=".kml",
            filetypes=(("KML 文件", "*.kml"), ("所有文件", "*.*")),
            initialfile=initial_file
        )
        if file_path:
            self.output_file_path = file_path
            # Display just the filename and indicate selection
            display_name = file_path.split('/')[-1].split('\\')[-1]
            self.output_file_label.config(text=display_name, fg="black")
            self.update_status(f"已选择输出文件路径: {display_name}")


    def update_status(self, message):
        """Appends a message to the status text area."""
        self.status_text.config(state='normal') # Enable editing
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END) # Scroll to the bottom
        self.status_text.config(state='disabled') # Disable editing
        self.master.update_idletasks() # Update the GUI display immediately

    def start_correction(self):
        self.update_status("--- 开始修正 ---")
        self.correct_button.config(state='disabled') # Disable button during processing

        # --- 1. Validate and Collect Input Coordinates ---
        incorrect_points_list = []
        correct_points_list = []

        try:
            for i in range(self.num_points):
                inc_lon_str = self.incorrect_entries[i][0].get().strip()
                inc_lat_str = self.incorrect_entries[i][1].get().strip()
                corr_lon_str = self.correct_entries[i][0].get().strip()
                corr_lat_str = self.correct_entries[i][1].get().strip()

                # Skip entirely empty rows
                if not inc_lon_str and not inc_lat_str and not corr_lon_str and not corr_lat_str:
                     continue

                # Check for incomplete rows
                if not inc_lon_str or not inc_lat_str or not corr_lon_str or not corr_lat_str:
                     messagebox.showwarning("警告", f"点 {chr(65+i)} 坐标不完整。请填写完整的点对或留空该行。")
                     self.update_status("输入坐标不完整。")
                     self.correct_button.config(state='normal')
                     return

                # Convert to float and add to lists
                inc_lon = float(inc_lon_str)
                inc_lat = float(inc_lat_str)
                corr_lon = float(corr_lon_str)
                corr_lat = float(corr_lat_str)

                incorrect_points_list.append([inc_lon, inc_lat])
                correct_points_list.append([corr_lon, corr_lat])

            # Check if enough points were provided
            if len(incorrect_points_list) < 3:
                messagebox.showwarning("警告", "请至少填写 3 对完整的参考点坐标来计算仿射变换！")
                self.update_status("参考点数量不足。")
                self.correct_button.config(state='normal')
                return

            incorrect_points = np.array(incorrect_points_list)
            correct_points = np.array(correct_points_list)


        except ValueError:
            messagebox.showwarning("警告", "坐标输入无效。请确保经纬度是数字！")
            self.update_status("坐标输入格式错误。")
            self.correct_button.config(state='normal')
            return
        except Exception as e:
            messagebox.showerror("错误", f"读取坐标时发生未知错误: {e}")
            self.update_status("读取坐标时发生错误。")
            self.correct_button.config(state='normal')
            return


        # --- 2. Validate File Selection ---
        if not self.input_file_path:
            messagebox.showwarning("警告", "请先选择输入 KML 文件！")
            self.update_status("未选择输入文件。")
            self.correct_button.config(state='normal')
            return
        if not self.output_file_path:
            messagebox.showwarning("警告", "请先选择输出文件路径！")
            self.update_status("未选择输出文件路径。")
            self.correct_button.config(state='normal')
            return


        # --- 3. Calculate Affine Transformation ---
        self.update_status("正在计算仿射变换...")

        try:
            affine_transform = transform.estimate_transform('affine', incorrect_points, correct_points)

            if affine_transform is None:
                 messagebox.showerror("错误", "无法计算仿射变换。请检查输入的参考点是否共线或数据是否存在其他问题。")
                 self.update_status("计算仿射变换失败：点可能共线或数据有问题。")
                 self.correct_button.config(state='normal')
                 return

            self.update_status("成功计算仿射变换。")
            # Optional: Display the transform matrix
            # self.update_status(f"变换矩阵:\n{affine_transform.params}")


        except Exception as e:
            messagebox.showerror("错误", f"计算仿射变换时发生未知错误。\n错误详情: {e}")
            # traceback.print_exc() # Print traceback to console for debugging
            self.update_status("计算仿射变换时发生错误。")
            self.correct_button.config(state='normal')
            return


        # --- 4. Perform Correction ---
        self.update_status(f"正在修正文件: {self.input_file_path}")
        self.update_status(f"将保存到文件: {self.output_file_path}")

        try:
            # Call the core correction function
            # Pass the status_callback so the function can update the GUI status area
            correct_kml_coordinates(self.input_file_path, self.output_file_path, affine_transform, self.update_status)

            self.update_status("文件修正完成！")
            messagebox.showinfo("完成", "KML 文件修正成功！")

        except FileNotFoundError:
             messagebox.showerror("错误", f"输入文件未找到 '{self.input_file_path}'")
             self.update_status("修正失败：输入文件未找到。")
        except etree.XMLSyntaxError as e:
             messagebox.showerror("错误", f"无法解析 KML 文件 '{self.input_file_path}'。\n请检查文件是否为有效的 XML/KML 格式。\n错误详情: {e}")
             self.update_status("修正失败：XML 解析错误。")
        except Exception as e:
             messagebox.showerror("错误", f"修正过程中发生未知错误。\n错误详情: {e}")
             # traceback.print_exc() # Print traceback to console for debugging
             self.update_status("修正失败：未知错误。")

        finally:
            self.correct_button.config(state='normal') # Re-enable button


# --- Main application execution ---
if __name__ == "__main__":
    # Create the main application window
    root = tk.Tk()
    gui = KmlCorrectorGUI(root)
    root.mainloop() # Start the Tkinter event loop