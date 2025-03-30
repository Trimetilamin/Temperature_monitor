import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from PIL import Image
from matplotlib.font_manager import FontProperties

# Global variables
data = pd.DataFrame()
months = []
ALARM_LOWER = 2.0
ALARM_UPPER = 10.0
LOGGER_ID = ""  # Initialize as empty string

# Load Calibri Math font for text in the PDF
calibri_math = FontProperties(fname='C:/Windows/Fonts/calibriz.ttf')  # Update the path if necessary

def read_file(file_path):
    global data, months, LOGGER_ID
    data = pd.DataFrame()
    months.clear()

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        parsed_data = []
        for i, line in enumerate(lines):
            cleaned_line = line.strip().replace("\x00", "")
            parts = cleaned_line.split()
            if len(parts) >= 6:
                date = parts[0].strip()
                time = parts[1].strip()
                if i == 0:
                    LOGGER_ID = parts[2].strip()  # Set the global LOGGER_ID to the value of the first row of the third column
                try:
                    timestamp = dt.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                month = "-".join(date.split("-")[:2])
                temperature = float(parts[3])
                humidity = float(parts[4])
                parsed_data.append([timestamp, temperature, humidity, month])

        data = pd.DataFrame(parsed_data, columns=['timestamp', 'temperature', 'humidity', 'month'])
        months = sorted(data['month'].unique().tolist())
        update_dropdown()
    except FileNotFoundError:
        tk.messagebox.showerror("Error", "File not found.")
    except Exception as e:
        tk.messagebox.showerror("Error", f"An error occurred while reading the file: {e}")

def update_dropdown():
    month_var.set("")
    dropdown_menu["values"] = months

def generate_statistics(series):
    avg, std = series.mean(), series.std()
    min_val, max_val = series.min(), series.max()
    out_of_bounds = series[(series < ALARM_LOWER) | (series > ALARM_UPPER)].count()
    within_1_std = series[(series >= avg - std) & (series <= avg + std)].count() / len(series) * 100
    within_2_std = series[(series >= avg - 2 * std) & (series <= avg + 2 * std)].count() / len(series) * 100
    return {
        "avg": avg, "std": std, "min": min_val, "max": max_val,
        "out_of_bounds": out_of_bounds, "within_1_std": within_1_std, "within_2_std": within_2_std
    }

def generate_additional_statistics(filtered_data):
    num_measurements = len(filtered_data)
    avg_measurements_per_day = num_measurements / filtered_data['timestamp'].dt.date.nunique()
    max_time_diff = (filtered_data['timestamp'].diff().max()).total_seconds() / 3600  # in hours
    return {
        "num_measurements": num_measurements,
        "avg_measurements_per_day": avg_measurements_per_day,
        "max_time_diff": max_time_diff
    }

def export_to_pdf():
    selected_month = month_var.get()
    if not selected_month:
        return

    filtered_data = data[data['month'] == selected_month]
    filtered_data.insert(0, 'Seq', range(1, len(filtered_data) + 1))  # Shortened column name
    filtered_data.drop(columns=['month'], inplace=True)
    temp_stats = generate_statistics(filtered_data['temperature'])
    hum_stats = generate_statistics(filtered_data['humidity'])
    additional_stats = generate_additional_statistics(filtered_data)

    # Suggested file name
    year_month = selected_month.replace("-", ".")
    suggested_file_name = f"Export_{LOGGER_ID}_{year_month}.pdf"

    pdf_file_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=suggested_file_name, filetypes=[("PDF files", "*.pdf")])
    if pdf_file_path:
        with PdfPages(pdf_file_path) as pdf:
            fig, axs = plt.subplots(3, 1, figsize=(8.27, 11.69))
            fig.suptitle(f"Temperature and Humidity Data \n {LOGGER_ID} - {selected_month}", fontsize=18, fontweight='bold', fontproperties=calibri_math, y=0.95)

            # Add logo
            try:
                logo = Image.open("logo.png").resize((150, 150))
                fig.figimage(logo, xo=0, yo=fig.bbox.ymax - 150)
            except FileNotFoundError:
                print("logo.png not found.")

            # Text boxes
            temp_text_stats = (
                f"Average = ({temp_stats['avg']:.2f} \u00b1 {temp_stats['std']:.2f}) \u00b0C  \n\nMinimum = {temp_stats['min']:.2f}\u00b0C \nMaximum = {temp_stats['max']:.2f}\u00b0C\n"
                f"\n\nPercentage of datapoints within \n - 1 standard deviation = {temp_stats['within_1_std']:.1f}% \n - 2 standard deviation = {temp_stats['within_2_std']:.1f}% \n\nData points outside \n2-10\u00b0C interval: {temp_stats['out_of_bounds']}"
            )
            hum_text_stats = (
                f"Average = ({hum_stats['avg']:.2f} \u00b1 {hum_stats['std']:.2f}) %\n\nMinimum = {hum_stats['min']:.2f}% \nMaximum = {hum_stats['max']:.2f}%\n"
                f"\n\nPercentage of datapoints within \n - 1 standard deviation = {hum_stats['within_1_std']:.1f}% \n - 2 standard deviation = {hum_stats['within_2_std']:.1f}%"
            )
            additional_text_stats = (
                f"Number of measurements: {additional_stats['num_measurements']}\n\n"
                f"Average number of \nmeasurements per day: {additional_stats['avg_measurements_per_day']:.2f}\n\n"
                f"Maximum time between \ntwo signal transmissions: {additional_stats['max_time_diff']:.2f} hours"
            )
            axs[0].text(0.01, 0.8, "Temperature:", transform=axs[0].transAxes, verticalalignment='top', fontproperties=calibri_math, fontweight='bold')
            axs[0].text(0.01, 0.65, temp_text_stats, transform=axs[0].transAxes, verticalalignment='top', bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'), fontproperties=calibri_math, linespacing=1.5)
            axs[0].text(0.7, 0.8, "Humidity:", transform=axs[0].transAxes, verticalalignment='top', fontproperties=calibri_math, fontweight='bold')
            axs[0].text(0.7, 0.65, hum_text_stats, transform=axs[0].transAxes, verticalalignment='top', bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'), fontproperties=calibri_math, linespacing=1.5)
            axs[0].text(0.33, 0.8, "Additional Stats:", transform=axs[0].transAxes, verticalalignment='top', fontproperties=calibri_math, fontweight='bold')
            axs[0].text(0.33, 0.65, additional_text_stats, transform=axs[0].transAxes, verticalalignment='top', bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'), fontproperties=calibri_math, linespacing=1.5)
            axs[0].axis('off')

            # Graphs
            axs[1].plot(filtered_data['timestamp'], filtered_data['temperature'])
            axs[1].set_title("Temperature over time", fontsize=12, fontproperties=calibri_math)
            axs[1].set_xlabel("Time", fontsize=10, fontproperties=calibri_math, style='italic')
            axs[1].set_ylabel("Temp (\u00b0C)", fontsize=10, fontproperties=calibri_math, style='italic')  # Shortened column name
            axs[1].tick_params(axis='x', rotation=45)
            axs[1].set_ylim(0, 15)
            axs[1].axhline(y=2, color='r', linestyle='--')
            axs[1].axhline(y=10, color='r', linestyle='--')

            if filtered_data['temperature'].min() < 0 or filtered_data['temperature'].max() > 15:
                axs[1].set_ylim(filtered_data['temperature'].min() - 1, filtered_data['temperature'].max() + 1)

            axs[2].plot(filtered_data['timestamp'], filtered_data['humidity'])
            axs[2].set_title("Humidity over time", fontsize=12, fontproperties=calibri_math)
            axs[2].set_xlabel("Time", fontsize=10, fontproperties=calibri_math, style='italic')
            axs[2].set_ylabel("Hum (%)", fontsize=10, fontproperties=calibri_math, style='italic')  # Shortened column name
            axs[2].tick_params(axis='x', rotation=45)
            axs[2].set_ylim(0, 100)

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            pdf.savefig(fig)
            plt.close(fig)

            # Table data
            rows_per_page = 70  # Adjust this value as needed
            num_pages = int(np.ceil(len(filtered_data) / (rows_per_page * 2)))
            for page in range(num_pages):
                fig_table, ax_table = plt.subplots(figsize=(8.27, 11.69))
                ax_table.axis('off')
                start_row = page * rows_per_page * 2
                end_row = start_row + rows_per_page
                left_table_data = filtered_data.iloc[start_row:end_row].rename(columns={
                    'Seq': 'Number', 'timestamp': 'Time', 'temperature': 'Temperature', 'humidity': 'Humidity'}).to_markdown(index=False)
                right_table_data = filtered_data.iloc[end_row:end_row + rows_per_page].rename(columns={
                    'Seq': 'Number', 'timestamp': 'Time', 'temperature': 'Temperature', 'humidity': 'Humidity'}).to_markdown(index=False)
                ax_table.text(0.05, 0.95, left_table_data, transform=ax_table.transAxes, verticalalignment='top', fontsize=8, fontproperties=calibri_math)
                ax_table.text(0.55, 0.95, right_table_data, transform=ax_table.transAxes, verticalalignment='top', fontsize=8, fontproperties=calibri_math)
                ax_table.plot([0.5, 0.5], [0.05, 0.95], color='black', linewidth=1, transform=ax_table.transAxes, clip_on=False)

                # Add logo on each page
                try:
                    logo = Image.open("logo.png").resize((150, 150))
                    fig_table.figimage(logo, xo=0, yo=fig_table.bbox.ymax - 150)
                except FileNotFoundError:
                    print("logo.png not found.")

                pdf.savefig(fig_table)
                plt.close(fig_table)

# GUI Setup
root = tk.Tk()
root.title("Temperature Data Viewer")

# Remove overrideredirect to allow normal window behavior
# root.overrideredirect(True)
root.geometry("+100+100")
root.bind("<B1-Motion>", lambda event: root.geometry(f"+{event.x_root}+{event.y_root}"))

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

btn_open = tk.Button(frame, text="Open File", command=lambda: read_file(filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])))
btn_open.pack()

month_var = tk.StringVar()
dropdown_menu = ttk.Combobox(frame, textvariable=month_var, state="readonly")
dropdown_menu.pack()
export_button = tk.Button(frame, text="Export to PDF", command=export_to_pdf)
export_button.pack()

root.mainloop()
