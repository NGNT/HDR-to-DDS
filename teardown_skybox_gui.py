import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import shutil
from PIL import Image, ImageTk, ImageDraw

# Theme Colors
THEME_COLOR = "#2c3e50"  # Dark blue-gray
ACCENT_COLOR = "#3498db"  # Bright blue
ACCENT_COLOR_DARK = "#2980b9"  # Darker blue
TEXT_COLOR = "#ecf0f1"  # Off-white
BACKGROUND_COLOR = THEME_COLOR  # Slightly lighter than theme color
BUTTON_COLOR = "#3498db"  # Bright blue

class ModernStyle:
    """Creates a modern style for tkinter widgets"""
    def __init__(self, root):
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use 'clam' as base theme

        # General appearance
        self.style.configure('.', background=BACKGROUND_COLOR, foreground=TEXT_COLOR, font=('Segoe UI', 10))

        # Frame
        self.style.configure('TFrame', background=BACKGROUND_COLOR)

        # LabelFrame
        self.style.configure('TLabelframe', background=BACKGROUND_COLOR, foreground=TEXT_COLOR)
        self.style.configure('TLabelframe.Label', background=BACKGROUND_COLOR, foreground=ACCENT_COLOR, font=('Segoe UI', 10, 'bold'))

        # Label
        self.style.configure('TLabel', background=BACKGROUND_COLOR, foreground=TEXT_COLOR)

        # Button
        self.style.configure('TButton', background=BUTTON_COLOR, foreground=TEXT_COLOR, padding=(10, 5), relief='flat')
        self.style.map('TButton', background=[('active', ACCENT_COLOR_DARK), ('disabled', '#7f8c8d')])

        # Entry
        self.style.configure('TEntry', fieldbackground=THEME_COLOR, foreground=TEXT_COLOR, padding=5)

        # Combobox
        self.style.map('TCombobox', fieldbackground=[('readonly', THEME_COLOR)], background=[('readonly', THEME_COLOR)], foreground=[('readonly', TEXT_COLOR)])

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0", relief="solid", borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class SkyboxConverter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Teardown Skybox Converter")
        self.geometry("1280x960")
        self.configure(bg=THEME_COLOR)

        # Apply modern style
        self.style = ModernStyle(self)

        # Create header
        self._create_header()

        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # HDR File Selection
        hdr_frame = ttk.LabelFrame(main_frame, text="HDR File Selection", padding=10)
        hdr_frame.pack(fill="x", pady=10)
        ttk.Label(hdr_frame, text="HDR File:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.hdr_entry = ttk.Entry(hdr_frame, width=50)
        self.hdr_entry.grid(row=0, column=1, padx=10, pady=2, sticky="w")
        ttk.Button(hdr_frame, text="Browse...", command=self.browse_hdr).grid(row=0, column=2, padx=10, pady=2, sticky="w")

        # Output Name
        ttk.Label(hdr_frame, text="Output Name:").grid(row=1, column=0, sticky="w", padx=10, pady=(10, 0))
        self.output_entry = ttk.Entry(hdr_frame, width=50)
        self.output_entry.grid(row=1, column=1, padx=10, pady=2, sticky="w")

        # Create a container frame for the groups
        group_frame = ttk.Frame(main_frame)
        group_frame.pack(fill="both", expand=True, pady=10)

        # Filter Options
        self.create_group(group_frame, "Filter Options", [
            ("Filter", "--filter", "radiance", "Type of filter for processing the skybox. 'Radiance' is good for HDR environments.", ["radiance", "irradiance", "shcoeffs", "none"]),
            ("Exclude Base", "--excludeBase", "true", "Skip the base (full resolution) texture level. Usually keep this on.", ["true", "false"]),
            ("Mip Count", "--mipCount", "20", "Number of smaller texture versions to create. More mips = better performance but larger file size.", None),
            ("Gloss Scale", "--glossScale", "15", "Controls how shiny surfaces appear. Higher = more reflective.", None),
            ("Gloss Bias", "--glossBias", "2", "Adjusts the base shininess level. Higher = more reflective overall.", None),
            ("Lighting Model", "--lightingModel", "ggxbrdf", "How light interacts with surfaces. GGX is modern and realistic.", ["ggxbrdf", "phongbrdf", "blinnbrdf"]),
            ("Edge Fixup", "--edgeFixup", "none", "How to handle cube edges. 'None' is usually best for skyboxes.", ["none", "warp", "stretch"]),
        ], 0, 0)

        # Processing Devices
        self.create_group(group_frame, "Processing Devices", [
            ("CPU Threads", "--numCpuProcessingThreads", "6", "How many CPU cores to use. Set to 0 for auto-detect.", None),
            ("Use OpenCL", "--useOpenCL", "true", "Use GPU for faster processing if available.", ["true", "false"]),
            ("CL Vendor", "--clVendor", "anyGpuVendor", "Which GPU brand to use. Usually leave as 'anyGpuVendor'.", None),
            ("Device Type", "--deviceType", "gpu", "Use GPU for best performance, CPU for compatibility.", ["cpu", "gpu"]),
        ], 0, 1)

        # Additional Operations
        self.create_group(group_frame, "Additional Operations", [
            ("Input Brightness", "--inputGammaNumerator", "1.0", "Make the input image brighter (>1) or darker (<1).", None),
            ("Input Brightness Divider", "--inputGammaDenominator", "1.0", "Advanced: Adjusts input brightness scaling.", None),
            ("Output Brightness", "--outputGammaNumerator", "1.0", "Make the final image brighter (>1) or darker (<1).", None),
            ("Output Brightness Divider", "--outputGammaDenominator", "1.0", "Advanced: Adjusts output brightness scaling.", None),
            ("Generate Mip Chain", "--generateMipChain", "false", "Create smaller texture versions for better performance at a distance.", ["true", "false"]),
        ], 0, 2)

        # Output
        output_group = self.create_group(group_frame, "Output", [
            ("Output Number", "--outputNum", "1", "How many different output files to create. Usually 1.", None),
            ("Output Name", "--output0", "", "Base name for the output file (without extension).", None),
            ("File Format", None, ".dds", "Output will be saved in DDS format.", None),  # Static label
            ("Color Format", "--colorFormat", "bgra8", "Color quality. Higher values = better quality but larger files.", ["bgr8", "bgra8", "rgba16", "rgba16f", "rgba32f"]),
            ("Map Type", "--mapType", "cubemap", "How to map the texture. 'Cubemap' is standard for skyboxes.", ["cubemap", "latlong", "octahedral"]),
            ("Source Face Size", "--srcFaceSize", "1024", "Resolution of input faces (pixels). Higher = more detail.", None),
            ("Output Face Size", "--dstFaceSize", "1024", "Resolution of output faces (pixels). Higher = better quality.", None),
        ], row=0, column=3)  # Specify row and column

        # Debugging Output Box
        debug_frame = ttk.LabelFrame(main_frame, text="Debugging Output", padding=10)
        debug_frame.pack(fill="both", expand=True, pady=10)

        self.debug_output = tk.Text(debug_frame, height=5, wrap="word", state="disabled", bg=THEME_COLOR, fg=TEXT_COLOR)
        self.debug_output.pack(side="left", fill="both", expand=True)

        # Add a scrollbar for the debugging output box
        debug_scrollbar = ttk.Scrollbar(debug_frame, orient="vertical", command=self.debug_output.yview)
        debug_scrollbar.pack(side="right", fill="y")
        self.debug_output.configure(yscrollcommand=debug_scrollbar.set)

        # Convert Button
        ttk.Button(main_frame, text="Convert", command=self.convert).pack(pady=15)

        # Status Label
        self.status = ttk.Label(main_frame, text="", foreground=ACCENT_COLOR)
        self.status.pack()

    def _create_header(self):
        """Creates a header with a gradient background and title."""
        header_frame = ttk.Frame(self)
        header_frame.pack(side="top", fill="x")

        gradient_canvas = tk.Canvas(header_frame, height=100, bg=THEME_COLOR, highlightthickness=0)
        gradient_canvas.pack(fill="x")

        # Draw gradient
        width = self.winfo_screenwidth()
        gradient = Image.new("RGB", (width, 100), THEME_COLOR)
        draw = ImageDraw.Draw(gradient)
        for i in range(100):
            color = f"#{int(44 + i * 0.5):02x}{int(62 + i * 0.5):02x}{int(80 + i * 0.5):02x}"
            draw.line([(0, i), (width, i)], fill=color)
        gradient_image = ImageTk.PhotoImage(gradient)
        gradient_canvas.create_image(0, 0, anchor="nw", image=gradient_image)
        gradient_canvas.image = gradient_image

        # Add title
        gradient_canvas.create_text(20, 50, anchor="w", text="Teardown Skybox Converter", fill=TEXT_COLOR, font=("Segoe UI", 20, "bold"))

    def create_group(self, parent, group_name, fields, row, column):
        frame = ttk.LabelFrame(parent, text=group_name, padding=10)
        frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        max_cpu_threads = os.cpu_count()  # Get the maximum number of CPU threads
        for label, key, default, tooltip_text, options in fields:
            ttk.Label(frame, text=label).pack(anchor="w")
            if options:  # If options are provided, use a drop-down menu
                var = tk.StringVar(value=default)
                dropdown = ttk.Combobox(frame, textvariable=var, values=options, state="readonly")
                dropdown.pack(padx=5, pady=2, anchor="w")
                Tooltip(dropdown, tooltip_text)  # Attach tooltip to the drop-down
                setattr(self, key.replace("--", "").replace("-", "_"), var)
            elif key == "--numCpuProcessingThreads":
                # Use Spinbox for CPU threads with a max limit of available threads
                spinbox = tk.Spinbox(frame, from_=1, to=max_cpu_threads, increment=1, width=10)
                spinbox.delete(0, "end")
                spinbox.insert(0, default)
                spinbox.pack(padx=5, pady=2, anchor="w")
                Tooltip(spinbox, tooltip_text)  # Attach tooltip to the spinbox
                setattr(self, key.replace("--", "").replace("-", "_"), spinbox)
            elif key in ["--mipCount", "--glossScale", "--glossBias", "--srcFaceSize", "--dstFaceSize"]:
                # Use Spinbox for other integer fields
                spinbox = tk.Spinbox(frame, from_=0, to=1000, increment=1, width=10)
                spinbox.delete(0, "end")
                spinbox.insert(0, default)
                spinbox.pack(padx=5, pady=2, anchor="w")
                Tooltip(spinbox, tooltip_text)  # Attach tooltip to the spinbox
                setattr(self, key.replace("--", "").replace("-", "_"), spinbox)
            elif key is None:  # Static label
                ttk.Label(frame, text=default).pack(padx=5, pady=2, anchor="w")
            else:  # Otherwise, use a text entry
                entry = ttk.Entry(frame, width=40)
                entry.insert(0, default)
                entry.pack(padx=5, pady=2, anchor="w")
                Tooltip(entry, tooltip_text)  # Attach tooltip to the entry
                setattr(self, key.replace("--", "").replace("-", "_"), entry)

    def browse_hdr(self):
        file_path = filedialog.askopenfilename(filetypes=[("HDR files", "*.hdr")])
        if file_path:
            self.hdr_entry.delete(0, tk.END)
            self.hdr_entry.insert(0, file_path)
            base = os.path.splitext(os.path.basename(file_path))[0]
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, base)

    def convert(self):
        def log_debug(message):
            """Helper function to log messages to the debugging output box."""
            self.debug_output.configure(state="normal")
            self.debug_output.insert("end", message + "\n")
            self.debug_output.see("end")  # Auto-scroll to the latest message
            self.debug_output.configure(state="disabled")

        hdr_path = self.hdr_entry.get()
        output_name = self.output_entry.get().strip()
        if not hdr_path or not output_name:
            messagebox.showerror("Error", "Please select an HDR file and specify an output name.")
            log_debug("Error: HDR file or output name is missing.")
            return

        # Ensure the output name does not have redundant extensions
        if output_name.endswith(".dds"):
            output_name = output_name[:-4]

        working_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get values from UI controls with defaults matching generate_edited.bat
        params = {
            'filter': 'radiance',
            'srcFaceSize': '1024',
            'excludeBase': 'true',
            'mipCount': '20',
            'glossScale': '15',
            'glossBias': '2',
            'lightingModel': 'ggxbrdf',
            'edgeFixup': 'none',
            'dstFaceSize': '1024',
            'numCpuProcessingThreads': '6',
            'useOpenCL': 'true',
            'clVendor': 'anyGpuVendor',
            'deviceType': 'gpu',
            'generateMipChain': 'false',
            'outputNum': '1',
            'output0params': 'dds,rgba32f,cubemap'
        }
        
        # Update with values from UI controls if they exist
        for param in params.keys():
            if hasattr(self, param):
                value = getattr(self, param)
                if hasattr(value, 'get'):  # For StringVar and similar
                    params[param] = value.get()
                else:  # For direct values
                    params[param] = value
        
        # Log the settings being used
        log_debug("Using the following parameters:")
        for key, value in params.items():
            log_debug(f"  {key}: {value}")
        
        # Get the directory where the executable is located
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            app_dir = os.path.dirname(sys.executable)
        else:
            # Running in a normal Python environment
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        cmft_path = os.path.join(app_dir, "cmft.exe")
        
        if not os.path.exists(cmft_path):
            messagebox.showerror("Error", f"cmft.exe not found in the application directory.\nLooked in: {cmft_path}")
            log_debug(f"Error: cmft.exe not found. Looked in: {cmft_path}")
            return
        
        # Set output path to be in the same directory as the executable
        output_path = os.path.join(app_dir, output_name)
        
        # Debug: Log working directory and output path
        log_debug(f"Working directory: {working_dir}")
        log_debug(f"Output path: {output_path}")
        log_debug(f"Does cmft.exe exist? {os.path.exists(cmft_path)}")
        log_debug(f"Does input file exist? {os.path.exists(hdr_path)}")

        # Get face sizes from GUI or use defaults
        src_face_size = params.get('srcFaceSize', '1024')
        dst_face_size = params.get('dstFaceSize', '1024')
        
        # Build the command with values from GUI
        cmd = [
            cmft_path,
            '--input', os.path.abspath(hdr_path),
            '--filter', 'radiance',
            '--srcFaceSize', str(src_face_size),
            '--excludeBase', 'true',
            '--mipCount', '11',  # Note: The actual execution shows mipCount=11, not 20
            '--glossScale', '15',
            '--glossBias', '2',
            '--lightingModel', 'phong',  # Note: The actual execution shows lightingModel=phong
            '--edgeFixup', 'none',
            '--dstFaceSize', str(dst_face_size),
            '--numCpuProcessingThreads', '6',
            '--useOpenCL', 'true',
            '--clVendor', 'anyGpuVendor',
            '--deviceType', 'gpu',
            '--inputGammaNumerator', '1.0',
            '--inputGammaDenominator', '1.0',
            '--outputGammaNumerator', '1.0',
            '--outputGammaDenominator', '1.0',
            '--generateMipChain', 'false',
            '--outputNum', '1',
            '--output0', output_path,
            '--output0params', 'dds,rgba32f,cubemap'
        ]

        # Debugging: Log the final command and parameters
        log_debug("=== Final Parameters ===")
        for key, value in params.items():
            log_debug(f"{key}: {value}")
        log_debug("======================")
        log_debug(f"Full command: {' '.join(cmd)}")
        log_debug("======================")

        # Run cmft.exe with optimized settings
        self.status.config(text="Converting (this may take a few minutes)...")
        self.update_idletasks()
        log_debug("Starting conversion process...")
        
        try:
            # Build the full command as a single string
            command = ' '.join(cmd)
            log_debug(f"Executing command: {command}")
            
            # Run the command with shell=False (as the batch file would)
            log_debug("Running command...")
            log_debug(f"Command: {cmd}")
            log_debug(f"Command string: {' '.join(cmd)}")
            
            # Print environment for debugging
            log_debug(f"Environment: {os.environ.get('PATH', 'No PATH in environment')}")
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            log_debug(f"cmft.exe output:\n{result.stdout}")
            if result.returncode == 0:
                self.status.config(text="Conversion complete!")
                messagebox.showinfo("Success", "DDS file generated successfully.")
                log_debug("Conversion complete! DDS file generated successfully.")
            else:
                self.status.config(text="Conversion failed.")
                messagebox.showerror("Error", f"cmft.exe failed:\n{result.stderr}")
                log_debug(f"Error: cmft.exe failed:\n{result.stderr}")
        except Exception as e:
            self.status.config(text="Conversion failed.")
            messagebox.showerror("Error", f"Failed to run cmft.exe: {e}")
            log_debug(f"Error: Failed to run cmft.exe: {e}")

if __name__ == "__main__":
    app = SkyboxConverter()
    app.mainloop()