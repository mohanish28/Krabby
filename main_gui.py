import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from council import Council
from council.utils.logging import setup_logging, get_logger
from council.utils.validation import validate_input, ValidationError
from config import MODELS, DISCUSSION_ROUNDS
import ollama
import time

# Setup logging
setup_logging(level="INFO")
logger = get_logger("gui")

class CouncilGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏛️ Council of LLM Models - Parliamentary System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0a0e27")
        
        # Modern color scheme
        self.colors = {
            "bg": "#0a0e27",
            "card": "#1a1f3a",
            "card_hover": "#252b4a",
            "primary": "#6366f1",
            "primary_hover": "#818cf8",
            "secondary": "#8b5cf6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "text": "#e5e7eb",
            "text_secondary": "#9ca3af",
            "accent": "#06b6d4"
        }
        
        self.council = None
        self.current_result = None
        self.animation_running = False
        self.available_models = []  # Store all available models
        self.selected_models = []  # Store user-selected models
        self.model_checkboxes = {}  # Store checkbox variables
        
        self.setup_ui()
        self.check_availability()
        self.animate_entrance()
    
    def animate_entrance(self):
        """Smooth entrance animation"""
        self.root.attributes('-alpha', 0)
        self.root.update()
        
        def fade_in():
            for i in range(0, 101, 5):
                self.root.attributes('-alpha', i / 100)
                self.root.update()
                time.sleep(0.02)
        
        threading.Thread(target=fade_in, daemon=True).start()
    
    def setup_ui(self):
        # Custom style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TNotebook', background=self.colors["bg"], borderwidth=0)
        style.configure('Custom.TNotebook.Tab', background=self.colors["card"], 
                       foreground=self.colors["text"], padding=[20, 10])
        style.map('Custom.TNotebook.Tab', background=[('selected', self.colors["primary"])])
        
        # Header with gradient effect
        header_frame = tk.Frame(self.root, bg=self.colors["bg"], height=100)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Animated header
        header_canvas = tk.Canvas(header_frame, bg=self.colors["bg"], highlightthickness=0, height=100)
        header_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Gradient background
        for i in range(100):
            color_intensity = int(99 + (156 - 99) * (i / 100))
            color = f"#{color_intensity:02x}{color_intensity:02x}{255:02x}"
            header_canvas.create_rectangle(0, i, 1200, i+1, fill=color, outline="")
        
        # Title with shadow effect
        title_label = tk.Label(
            header_canvas,
            text="🏛️ Council of LLM Models",
            font=("Segoe UI", 28, "bold"),
            bg="#6366f1",
            fg="white",
            padx=30,
            pady=15
        )
        header_canvas.create_window(600, 50, window=title_label)
        
        subtitle_label = tk.Label(
            header_canvas,
            text="Democratic AI Parliamentary System",
            font=("Segoe UI", 12),
            bg="#6366f1",
            fg="#e0e7ff",
            padx=30
        )
        header_canvas.create_window(600, 80, window=subtitle_label)
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Left panel - Input (Card style)
        left_panel = tk.Frame(main_container, bg=self.colors["bg"])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Input card
        input_card = tk.Frame(left_panel, bg=self.colors["card"], relief=tk.FLAT, bd=0)
        input_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Card header
        card_header = tk.Frame(input_card, bg=self.colors["primary"], height=50)
        card_header.pack(fill=tk.X)
        card_header.pack_propagate(False)
        
        input_title = tk.Label(
            card_header,
            text="💭 Enter Your Question",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["primary"],
            fg="white",
            padx=15,
            pady=12
        )
        input_title.pack(side=tk.LEFT)
        
        # Input area with modern styling
        input_frame = tk.Frame(input_card, bg=self.colors["card"], padx=15, pady=15)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder text
        self.placeholder_text = "Ask the council anything... What is the best approach to learn programming? What are the pros and cons of remote work?"
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=10,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            bg="#252b4a",
            fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            selectbackground=self.colors["primary"],
            selectforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=15,
            highlightthickness=2,
            highlightbackground=self.colors["card"],
            highlightcolor=self.colors["primary"]
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg=self.colors["text_secondary"])
        
        def on_focus_in(event):
            if self.input_text.get("1.0", tk.END).strip() == self.placeholder_text:
                self.input_text.delete("1.0", tk.END)
                self.input_text.config(fg=self.colors["text"])
        
        def on_focus_out(event):
            if not self.input_text.get("1.0", tk.END).strip():
                self.input_text.insert("1.0", self.placeholder_text)
                self.input_text.config(fg=self.colors["text_secondary"])
        
        self.input_text.bind("<FocusIn>", on_focus_in)
        self.input_text.bind("<FocusOut>", on_focus_out)
        
        # Submit button with hover effect
        self.submit_btn = tk.Button(
            input_card,
            text="🚀 Submit to Council",
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["primary"],
            fg="white",
            activebackground=self.colors["primary_hover"],
            activeforeground="white",
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor="hand2",
            command=self.submit_question
        )
        self.submit_btn.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Add hover effect
        def on_enter(e):
            if self.submit_btn['state'] != 'disabled':
                self.submit_btn.config(bg=self.colors["primary_hover"])
        
        def on_leave(e):
            if self.submit_btn['state'] != 'disabled':
                self.submit_btn.config(bg=self.colors["primary"])
        
        self.submit_btn.bind("<Enter>", on_enter)
        self.submit_btn.bind("<Leave>", on_leave)
        
        # Model Selection card
        model_selection_card = tk.Frame(left_panel, bg=self.colors["card"], relief=tk.FLAT, bd=0)
        model_selection_card.pack(fill=tk.X, pady=(0, 10))
        
        model_selection_header = tk.Frame(model_selection_card, bg=self.colors["primary"], height=40)
        model_selection_header.pack(fill=tk.X)
        model_selection_header.pack_propagate(False)
        
        model_selection_title = tk.Label(
            model_selection_header,
            text="🤖 Select Models",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["primary"],
            fg="white",
            padx=15,
            pady=10
        )
        model_selection_title.pack(side=tk.LEFT)
        
        # Model selection content frame
        model_selection_content = tk.Frame(model_selection_card, bg=self.colors["card"], padx=15, pady=12)
        model_selection_content.pack(fill=tk.X)
        
        # Dropdown-style model selector
        dropdown_frame = tk.Frame(model_selection_content, bg=self.colors["card"])
        dropdown_frame.pack(fill=tk.X)
        
        # Label for dropdown
        model_label = tk.Label(
            dropdown_frame,
            text="Ollama Model",
            font=("Segoe UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"],
            anchor=tk.W
        )
        model_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Dropdown button frame (styled like a dropdown)
        self.model_dropdown_frame = tk.Frame(
            dropdown_frame,
            bg="white",
            relief=tk.SOLID,
            bd=1,
            cursor="hand2"
        )
        self.model_dropdown_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Selected models display
        self.model_dropdown_text = tk.Label(
            self.model_dropdown_frame,
            text="Select models...",
            font=("Segoe UI", 10),
            bg="white",
            fg="#666666",
            anchor=tk.W,
            padx=10,
            pady=10
        )
        self.model_dropdown_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Dropdown arrow
        dropdown_arrow = tk.Label(
            self.model_dropdown_frame,
            text="▼",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666666",
            padx=10
        )
        dropdown_arrow.pack(side=tk.RIGHT)
        
        # Bind click to open dropdown
        self.model_dropdown_frame.bind("<Button-1>", self.open_model_selection_dialog)
        self.model_dropdown_text.bind("<Button-1>", self.open_model_selection_dialog)
        dropdown_arrow.bind("<Button-1>", self.open_model_selection_dialog)
        
        # Hover effect
        def on_enter(e):
            self.model_dropdown_frame.config(bg="#f5f5f5")
            self.model_dropdown_text.config(bg="#f5f5f5")
            dropdown_arrow.config(bg="#f5f5f5")
        
        def on_leave(e):
            self.model_dropdown_frame.config(bg="white")
            self.model_dropdown_text.config(bg="white")
            dropdown_arrow.config(bg="white")
        
        self.model_dropdown_frame.bind("<Enter>", on_enter)
        self.model_dropdown_frame.bind("<Leave>", on_leave)
        
        # Status card with animation
        status_card = tk.Frame(left_panel, bg=self.colors["card"], relief=tk.FLAT, bd=0)
        status_card.pack(fill=tk.X)
        
        status_header = tk.Frame(status_card, bg=self.colors["secondary"], height=40)
        status_header.pack(fill=tk.X)
        status_header.pack_propagate(False)
        
        status_title = tk.Label(
            status_header,
            text="📊 Status",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["secondary"],
            fg="white",
            padx=15,
            pady=10
        )
        status_title.pack(side=tk.LEFT)
        
        status_content = tk.Frame(status_card, bg=self.colors["card"], padx=15, pady=12)
        status_content.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_content,
            text="✨ Ready",
            font=("Segoe UI", 10),
            bg=self.colors["card"],
            fg=self.colors["success"],
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
        
        # Animated progress bar
        self.progress_frame = tk.Frame(status_content, bg=self.colors["card"])
        self.progress_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            height=6,
            bg=self.colors["card"],
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X)
        self.progress_rect = None
        
        # Right panel - Results (Card style)
        right_panel = tk.Frame(main_container, bg=self.colors["bg"])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Results card
        results_card = tk.Frame(right_panel, bg=self.colors["card"], relief=tk.FLAT, bd=0)
        results_card.pack(fill=tk.BOTH, expand=True)
        
        results_header = tk.Frame(results_card, bg=self.colors["accent"], height=50)
        results_header.pack(fill=tk.X)
        results_header.pack_propagate(False)
        
        results_title = tk.Label(
            results_header,
            text="📋 Council Results",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent"],
            fg="white",
            padx=15,
            pady=12
        )
        results_title.pack(side=tk.LEFT)
        
        # Results notebook with custom style
        self.notebook = ttk.Notebook(results_card, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Final Output Tab
        output_frame = tk.Frame(self.notebook, bg="#252b4a")
        self.notebook.add(output_frame, text="🏆 Final Output")
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            bg="#252b4a",
            fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            selectbackground=self.colors["primary"],
            selectforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=20,
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Opinions Tab
        opinions_frame = tk.Frame(self.notebook, bg="#252b4a")
        self.notebook.add(opinions_frame, text="💬 All Opinions")
        
        self.opinions_text = scrolledtext.ScrolledText(
            opinions_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            bg="#252b4a",
            fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            selectbackground=self.colors["primary"],
            selectforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=20,
            state=tk.DISABLED
        )
        self.opinions_text.pack(fill=tk.BOTH, expand=True)
        
        # Voting Tab
        voting_frame = tk.Frame(self.notebook, bg="#252b4a")
        self.notebook.add(voting_frame, text="🗳️ Voting Results")
        
        self.voting_text = scrolledtext.ScrolledText(
            voting_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            bg="#252b4a",
            fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            selectbackground=self.colors["primary"],
            selectforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=20,
            state=tk.DISABLED
        )
        self.voting_text.pack(fill=tk.BOTH, expand=True)
        
        # Bottom action buttons
        button_frame = tk.Frame(self.root, bg=self.colors["bg"])
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.save_btn = self.create_modern_button(
            button_frame,
            "💾 Export Results",
            self.colors["success"],
            self.save_results,
            tk.LEFT
        )
        # Keep button visible but disabled until results are available
        self.save_btn.config(state=tk.DISABLED)
        
        self.clear_btn = self.create_modern_button(
            button_frame,
            "🗑️ Clear",
            self.colors["error"],
            self.clear_all,
            tk.LEFT
        )
        
        # Model count label
        self.model_count_label = tk.Label(
            button_frame,
            text="",
            font=("Segoe UI", 9),
            bg=self.colors["bg"],
            fg=self.colors["text_secondary"],
            padx=10
        )
        self.model_count_label.pack(side=tk.RIGHT)
    
    def create_modern_button(self, parent, text, color, command, side):
        """Create a modern button with hover effects"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=command
        )
        btn.pack(side=side, padx=5)
        
        # Hover effect
        def on_enter(e):
            if btn['state'] != 'disabled':
                # Lighten color
                btn.config(bg=self.lighten_color(color))
        
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def lighten_color(self, hex_color):
        """Lighten a hex color"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lightened = tuple(min(255, int(c * 1.2)) for c in rgb)
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
    
    def animate_progress(self):
        """Animate progress bar"""
        if not self.animation_running:
            return
        
        self.progress_canvas.delete("all")
        width = self.progress_frame.winfo_width()
        if width > 1:
            # Animated gradient progress bar
            for i in range(0, width, 20):
                offset = (time.time() * 200) % 40
                x1 = (i - offset) % width
                x2 = min(x1 + 40, width)
                if x2 > x1:
                    self.progress_canvas.create_rectangle(
                        x1, 0, x2, 6,
                        fill=self.colors["primary"],
                        outline=""
                    )
        
        if self.animation_running:
            self.root.after(50, self.animate_progress)
    
    def check_availability(self):
        """Check which models are available - Auto-detect Ollama models"""
        self.update_status("🔍 Checking model availability...", "blue")
        
        def check():
            # Check Ollama and get ALL installed models
            is_ollama_connected, ollama_models_base = self.check_ollama_connection()
            
            # Get full model names from Ollama (with tags like :latest, :4b, etc.)
            ollama_full_models = []
            if is_ollama_connected:
                try:
                    client = ollama.Client()
                    models_list = client.list()
                    if isinstance(models_list, dict) and 'models' in models_list:
                        for model in models_list['models']:
                            model_name = model.get('model') or model.get('name', '')
                            if model_name:
                                ollama_full_models.append(model_name)
                                print(f"  ✓ Auto-detected Ollama model: {model_name}")
                except Exception as e:
                    print(f"  ⚠️ Error getting full Ollama model list: {e}")
            
            # Build available models list
            available_models = []
            skipped_models = []
            
            # 1. Auto-detect ALL Ollama models (not just from config)
            if is_ollama_connected and ollama_full_models:
                for model_name in ollama_full_models:
                    # Create model config dynamically
                    model_config = {
                        "name": model_name,
                        "provider": "ollama"
                    }
                    available_models.append(model_config)
                    print(f"  ✓ Added Ollama model: {model_name}")
            
            # 2. Add API models from config (if they have keys)
            for model_config in MODELS:
                model_name = model_config["name"]
                provider = model_config["provider"]
                
                if provider == "ollama":
                    # Skip - we already auto-detected all Ollama models above
                    # This prevents duplicates if model is in both config and auto-detected
                    continue
                else:
                    # For API models, check if API key exists
                    api_key = model_config.get("api_key", "")
                    if api_key:
                        # Check if not already added (avoid duplicates)
                        if not any(m["name"] == model_name and m["provider"] == provider 
                                  for m in available_models):
                            available_models.append(model_config)
                            print(f"  ✓ {provider} model '{model_name}' has API key")
                    else:
                        skipped_models.append(f"{model_name} (no API key)")
                        print(f"  ✗ {provider} model '{model_name}' - no API key")
            
            if skipped_models:
                print(f"\n  Skipped {len(skipped_models)} API model(s) (no keys)")
            
            # Store available models and populate checkboxes
            self.available_models = available_models
            self.root.after(0, lambda: self.populate_model_checkboxes(available_models))
            
            if available_models:
                ollama_count = sum(1 for m in available_models if m["provider"] == "ollama")
                api_count = len(available_models) - ollama_count
                status_msg = f"✅ {len(available_models)} models available"
                if ollama_count > 0:
                    status_msg += f" ({ollama_count} Ollama"
                if api_count > 0:
                    status_msg += f"{', ' if ollama_count > 0 else ' ('}{api_count} API" if ollama_count > 0 else f" ({api_count} API"
                if ollama_count > 0 or api_count > 0:
                    status_msg += ")"
                status_msg += " - Select models to use"
                self.root.after(0, lambda: self.update_status(status_msg, "green"))
            else:
                self.root.after(0, lambda: self.update_status(
                    "⚠️ No models available. Check API keys or Ollama.", "red"
                ))
        
        threading.Thread(target=check, daemon=True).start()
    
    def populate_model_checkboxes(self, available_models):
        """Store available models and update dropdown display"""
        self.available_models = available_models
        
        if not available_models:
            self.model_dropdown_text.config(
                text="No models available",
                fg=self.colors["error"]
            )
            return
        
        # Auto-select all by default
        self.model_checkboxes = {}
        for model_config in available_models:
            model_name = model_config["name"]
            var = tk.BooleanVar(value=True)
            self.model_checkboxes[model_name] = var
        
        # Update dropdown text to show selected count
        self.update_dropdown_display()
        
        # Auto-apply selection
        self.apply_model_selection()
    
    def update_dropdown_display(self):
        """Update the dropdown text to show selected models"""
        if not self.available_models:
            return
        
        selected_count = sum(1 for var in self.model_checkboxes.values() if var.get())
        total_count = len(self.available_models)
        
        if selected_count == 0:
            self.model_dropdown_text.config(
                text="No models selected",
                fg="#666666"
            )
        elif selected_count == total_count:
            self.model_dropdown_text.config(
                text=f"All models selected ({total_count})",
                fg="#333333"
            )
        else:
            selected_names = [name for name, var in self.model_checkboxes.items() if var.get()]
            if len(selected_names) <= 2:
                display_text = ", ".join(selected_names)
            else:
                display_text = f"{selected_names[0]}, {selected_names[1]}, +{len(selected_names)-2} more"
            
            self.model_dropdown_text.config(
                text=display_text,
                fg="#333333"
            )
    
    def open_model_selection_dialog(self, event=None):
        """Open a popup dialog for model selection"""
        if not self.available_models:
            messagebox.showinfo("No Models", "No models are available. Please check your Ollama connection.")
            return
        
        # Create popup window
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Models")
        dialog.geometry("400x500")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header = tk.Frame(dialog, bg=self.colors["primary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="Select Models to Use",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["primary"],
            fg="white",
            pady=15
        )
        header_label.pack()
        
        # Scrollable frame for checkboxes
        canvas_frame = tk.Frame(dialog, bg="white")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        checkbox_frame = tk.Frame(canvas, bg="white")
        
        def update_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        checkbox_frame.bind("<Configure>", update_scroll)
        canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create checkboxes
        for model_config in self.available_models:
            model_name = model_config["name"]
            provider = model_config["provider"]
            
            checkbox_item = tk.Frame(checkbox_frame, bg="white")
            checkbox_item.pack(fill=tk.X, pady=5)
            
            var = self.model_checkboxes.get(model_name)
            if var is None:
                var = tk.BooleanVar(value=False)
                self.model_checkboxes[model_name] = var
            
            checkbox = tk.Checkbutton(
                checkbox_item,
                text=f"{model_name}",
                variable=var,
                font=("Segoe UI", 10),
                bg="white",
                fg="#333333",
                selectcolor="white",
                activebackground="white",
                activeforeground="#333333",
                cursor="hand2",
                command=self.update_dropdown_display
            )
            checkbox.pack(side=tk.LEFT, anchor=tk.W)
            
            provider_label = tk.Label(
                checkbox_item,
                text=f"({provider})",
                font=("Segoe UI", 9),
                bg="white",
                fg="#666666"
            )
            provider_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(dialog, bg="white")
        button_frame.pack(fill=tk.X, padx=15, pady=15)
        
        def select_all():
            for var in self.model_checkboxes.values():
                var.set(True)
            self.update_dropdown_display()
        
        def deselect_all():
            for var in self.model_checkboxes.values():
                var.set(False)
            self.update_dropdown_display()
        
        def apply_and_close():
            self.apply_model_selection()
            dialog.destroy()
        
        select_all_btn = tk.Button(
            button_frame,
            text="Select All",
            font=("Segoe UI", 9),
            bg="#e0e0e0",
            fg="#333333",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=select_all
        )
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        deselect_all_btn = tk.Button(
            button_frame,
            text="Deselect All",
            font=("Segoe UI", 9),
            bg="#e0e0e0",
            fg="#333333",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=deselect_all
        )
        deselect_all_btn.pack(side=tk.LEFT)
        
        apply_btn = tk.Button(
            button_frame,
            text="Apply",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["success"],
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=apply_and_close
        )
        apply_btn.pack(side=tk.RIGHT)
        
        # Update scroll region
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def apply_model_selection(self):
        """Apply the selected models and initialize council"""
        # Get selected models
        selected_models = []
        for model_config in self.available_models:
            model_name = model_config["name"]
            if model_name in self.model_checkboxes and self.model_checkboxes[model_name].get():
                selected_models.append(model_config)
        
        if not selected_models:
            messagebox.showwarning("No Models Selected", "Please select at least one model to use.")
            return
        
        self.selected_models = selected_models
        
        # Initialize council with selected models
        def init_council():
            try:
                logger.info(f"Initializing council with {len(selected_models)} selected models")
                self.council = Council(selected_models, discussion_rounds=DISCUSSION_ROUNDS)
                self.root.after(0, lambda: self.update_status(
                    f"✅ Ready - {len(selected_models)} model(s) active", "green"
                ))
                self.root.after(0, lambda: self.model_count_label.config(
                    text=f"🤖 {len(selected_models)} Active Models"
                ))
                logger.info("Council initialized successfully")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to initialize council: {error_msg}", exc_info=True)
                self.root.after(0, lambda: self.update_status(
                    f"❌ Error: {error_msg}", "red"
                ))
                self.root.after(0, lambda: messagebox.showerror("Initialization Error", error_msg))
        
        threading.Thread(target=init_council, daemon=True).start()
    
    def check_ollama_connection(self):
        """Check if Ollama is running and return base model names for compatibility"""
        try:
            client = ollama.Client()
            models_list = client.list()
            
            # Ollama client.list() returns a dict with 'models' key
            if isinstance(models_list, dict) and 'models' in models_list:
                models = models_list['models']
                # Extract base names (remove :latest, :4b, etc. tags) for matching
                # This is kept for backward compatibility but we'll get full names in check_availability
                available_models = []
                for model in models:
                    # Each model is a dict with 'model' or 'name' key
                    model_name = model.get('model') or model.get('name', '')
                    if model_name:
                        base_name = model_name.split(':')[0]
                        if base_name not in available_models:
                            available_models.append(base_name)
                
                if available_models:
                    print(f"  ✓ Ollama detected: {len(available_models)} base model(s) found")
                    print(f"  ✓ Ollama models: {available_models}")
                    return True, available_models
                else:
                    print(f"  ✗ Ollama is running but no models found")
                    return True, []
            else:
                print(f"  ✗ Ollama is running but no models found")
                return True, []  # Ollama is running but no models
        except Exception as e:
            print(f"  ✗ Ollama not available: {str(e)}")
            print(f"  Make sure Ollama is running. Start it with: ollama serve")
            return False, []
    
    def update_status(self, message, color="black"):
        """Update status label with animation"""
        color_map = {
            "green": self.colors["success"],
            "red": self.colors["error"],
            "blue": self.colors["primary"],
            "warning": self.colors["warning"],
            "black": self.colors["text"]
        }
        self.status_label.config(text=message, fg=color_map.get(color, self.colors["text"]))
        self.root.update_idletasks()
    
    def submit_question(self):
        """Submit question to council"""
        input_text = self.input_text.get("1.0", tk.END).strip()
        
        # Remove placeholder
        if input_text == self.placeholder_text:
            input_text = ""
        
        # Validate input
        try:
            input_text = validate_input(input_text, max_length=10000, min_length=1)
        except ValidationError as e:
            messagebox.showerror(
                "Invalid Input",
                f"Please check your input:\n\n{str(e)}\n\n"
                "Your input must be between 1 and 10,000 characters."
            )
            logger.warning(f"Input validation failed: {e}")
            return
        
        if not self.council:
            error_msg = "Council not initialized. Please check your API keys and model availability."
            messagebox.showerror("Initialization Error", error_msg)
            logger.error(error_msg)
            return
        
        # Disable submit button
        self.submit_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.animation_running = True
        self.animate_progress()
        self.update_status("🚀 Processing... Gathering opinions from council...", "blue")
        
        # Clear previous results
        self.clear_results()
        
        # Run in separate thread
        def run_deliberation():
            try:
                logger.info(f"Starting deliberation for input: {input_text[:50]}...")
                result = self.council.deliberate(input_text)
                self.root.after(0, lambda: self.display_results(result))
                logger.info("Deliberation completed successfully")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Deliberation failed: {error_msg}", exc_info=True)
                # Show user-friendly error message
                user_msg = self._format_error_message(error_msg)
                self.root.after(0, lambda: self.show_error(user_msg))
        
        threading.Thread(target=run_deliberation, daemon=True).start()
    
    def display_results(self, result):
        """Display results in the GUI with animations"""
        self.animation_running = False
        self.progress_canvas.delete("all")
        self.submit_btn.config(state=tk.NORMAL, text="🚀 Submit to Council")
        self.current_result = result
        
        # Animate text appearance
        def animate_text_insert(text_widget, content, tag=None):
            text_widget.config(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            
            if content:
                # Insert with typing effect
                def type_text(index=0):
                    if index < len(content):
                        chunk = content[index:index+10]
                        text_widget.insert(tk.END, chunk)
                        if tag:
                            text_widget.tag_add(tag, f"1.0+{index}c", tk.END)
                        self.root.update()
                        self.root.after(5, lambda: type_text(index+10))
                    else:
                        text_widget.config(state=tk.DISABLED)
                
                type_text()
            else:
                text_widget.insert("1.0", "No output generated.")
                text_widget.config(state=tk.DISABLED)
        
        # Update Final Output
        if result["final_output"]:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", result["final_output"])
            self.output_text.config(state=tk.DISABLED)
        else:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", "No output generated.")
            self.output_text.config(state=tk.DISABLED)
        
        # Update Opinions Tab
        self.opinions_text.config(state=tk.NORMAL)
        self.opinions_text.delete("1.0", tk.END)
        opinions_text = "🎯 INITIAL OPINIONS FROM ALL MODELS:\n"
        opinions_text += "=" * 70 + "\n\n"
        for i, opinion in enumerate(result["initial_opinions"], 1):
            opinions_text += f"🤖 Model {i}: {opinion['model']}\n"
            opinions_text += "─" * 70 + "\n"
            opinions_text += opinion["content"] + "\n\n"
        self.opinions_text.insert("1.0", opinions_text)
        self.opinions_text.config(state=tk.DISABLED)
        
        # Update Voting Tab
        self.voting_text.config(state=tk.NORMAL)
        self.voting_text.delete("1.0", tk.END)
        voting_text = "🗳️ VOTING RESULTS:\n"
        voting_text += "=" * 70 + "\n\n"
        voting_text += f"📊 Total Votes: {result['results']['total_votes']}\n"
        voting_text += f"🏆 Winning Opinion ID: {result['results']['winner_id']}\n"
        voting_text += f"✅ Winning Votes: {result['results']['winning_votes']}\n\n"
        voting_text += "📈 Vote Breakdown:\n"
        voting_text += "─" * 70 + "\n"
        for op_id, count in result['results']['vote_counts'].items():
            bar = "█" * count
            voting_text += f"  {op_id}: {bar} {count} vote(s)\n"
        voting_text += "\n" + "=" * 70 + "\n\n"
        voting_text += "📝 Individual Votes:\n"
        voting_text += "─" * 70 + "\n"
        for vote in result['votes']:
            voting_text += f"🤖 {vote['model']} → {vote.get('chosen_id', 'N/A')}\n"
        self.voting_text.insert("1.0", voting_text)
        self.voting_text.config(state=tk.DISABLED)
        
        # Switch to output tab with animation
        self.notebook.select(0)
        
        # Enable save button
        self.save_btn.config(state=tk.NORMAL)
        
        self.update_status("✨ Complete! Results displayed.", "green")
        
        # Success animation
        self.animate_success()
    
    def animate_success(self):
        """Animate success indicator"""
        original_bg = self.status_label.cget("bg")
        for i in range(3):
            self.status_label.config(bg=self.colors["success"])
            self.root.update()
            self.root.after(200)
            self.status_label.config(bg=original_bg)
            self.root.update()
            self.root.after(200)
    
    def _format_error_message(self, error_msg: str) -> str:
        """Format error message to be more user-friendly"""
        error_lower = error_msg.lower()
        
        if "api key" in error_lower or "api_key" in error_lower:
            return (
                "API Key Error:\n\n"
                "One or more API keys may be missing or invalid.\n\n"
                "Please check:\n"
                "1. Your .env file has valid API keys\n"
                "2. API keys are not expired\n"
                "3. You have internet connection\n\n"
                f"Technical details: {error_msg}"
            )
        elif "ollama" in error_lower:
            return (
                "Ollama Connection Error:\n\n"
                "Unable to connect to Ollama service.\n\n"
                "Please check:\n"
                "1. Ollama is installed and running\n"
                "2. Run 'ollama serve' if needed\n"
                "3. Required models are installed\n\n"
                f"Technical details: {error_msg}"
            )
        elif "timeout" in error_lower:
            return (
                "Timeout Error:\n\n"
                "The request took too long to complete.\n\n"
                "This could be due to:\n"
                "1. Slow internet connection\n"
                "2. API service temporarily unavailable\n"
                "3. Large input text\n\n"
                "Please try again.\n\n"
                f"Technical details: {error_msg}"
            )
        else:
            return (
                "An error occurred during processing:\n\n"
                f"{error_msg}\n\n"
                "Please check your input and try again. "
                "If the problem persists, check the logs for more details."
            )
    
    def show_error(self, error_msg):
        """Show error message with improved formatting"""
        self.animation_running = False
        self.progress_canvas.delete("all")
        self.submit_btn.config(state=tk.NORMAL, text="🚀 Submit to Council")
        
        # Truncate error message for status bar
        status_msg = error_msg.split('\n')[0][:50] + "..." if len(error_msg) > 50 else error_msg.split('\n')[0]
        self.update_status(f"❌ Error: {status_msg}", "red")
        
        # Show detailed error in messagebox
        messagebox.showerror("Error", error_msg)
    
    def clear_results(self):
        """Clear all result displays"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        self.opinions_text.config(state=tk.NORMAL)
        self.opinions_text.delete("1.0", tk.END)
        self.opinions_text.config(state=tk.DISABLED)
        
        self.voting_text.config(state=tk.NORMAL)
        self.voting_text.delete("1.0", tk.END)
        self.voting_text.config(state=tk.DISABLED)
        
        self.current_result = None
        self.save_btn.config(state=tk.DISABLED)
    
    def clear_all(self):
        """Clear input and results"""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg=self.colors["text_secondary"])
        self.clear_results()
        self.update_status("✨ Ready", "green")
    
    def save_results(self):
        """Save results to JSON file"""
        if not self.current_result:
            messagebox.showwarning("No Results", "No results to save.")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Council Results"
        )
        
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.current_result, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"✅ Results saved to:\n{filename}")
                self.update_status(f"💾 Saved to {filename.split('/')[-1]}", "green")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

def main():
    root = tk.Tk()
    app = CouncilGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
