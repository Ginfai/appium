import pytesseract
from PIL import Image
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Path to the Tesseract executable (update this path if necessary)
pytesseract.pytesseract.tesseract_cmd = r'D:\software\Tesseract\Tesseract-OCR\tesseract.exe'

def image_to_excel(image_path, excel_path):
    # Load the image
    img = Image.open(image_path)
    
    # Use pytesseract to do OCR on the image
    table_data = pytesseract.image_to_string(img)

    # Print the OCR output for debugging
    print("OCR Output:", table_data)  

    # Split the data into rows and columns
    rows = table_data.split('\n')
    data = []  

    for row in rows:
        if row.strip():
            columns = row.split()
            if len(columns) >0:
                data.append(columns)
    x_values = []
    y_values = []
    # Track the last seen label
    last_label = None
    for entry in data:
        if 'X' in entry:
            last_label='X'
            continue            
        if 'Y' in entry:
            last_label='Y'
            continue
        if last_label=='X':
            for value in entry:
                try:
                    if '.' in value:
                        float_value = float(value)
                        x_values.append(float_value)
                    else:
                        int_value = int(value)
                        x_values.append(int_value)
                except ValueError:
                    continue
        elif last_label=='Y':
            for value in entry:
                try:
                    if '.' in value:
                        float_value = float(value)
                        y_values.append(float_value)
                    else:
                        int_value = int(value)
                        y_values.append(int_value)
                except ValueError:
                    continue
    # Debugging: Print the extracted values
    print("Extracted X Values:", x_values)
    print("Extracted Y Values:", y_values)

    # Create a DataFrame from the data
    df = pd.DataFrame({
        'X': x_values,
        'Y': y_values
    })

    # Debugging: Print the DataFrame to check its contents
    print("DataFrame:\n", df)

    # Create a new Excel workbook and select the active worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Write DataFrame to the worksheet
    for r in dataframe_to_rows(df,index=True, header=True):
        worksheet.append(r)

    # Set column widths for better readability
    for column in worksheet.columns:
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

    # Save the DataFrame to an Excel file
    workbook.save(excel_path)
    print(f"Data has been written to {excel_path}")
# Example usage
image_path = r'C:\Users\thread0\Downloads\LocalSend\耕地.png'  # Update with your image path
excel_path = r'D:\home\WindProject\TableOCR\output_table.xlsx'        # Desired output Excel file path
image_to_excel(image_path, excel_path)

print("Table has been extracted and saved to Excel.")