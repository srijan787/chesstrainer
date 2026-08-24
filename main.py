# main.py
from ai.styles import load_all_styles, get_style_description

styles = load_all_styles()
for name, weights in styles.items():
    print(f"\n{name.upper()}")
    print(f"  Description: {get_style_description(name)}")
    print(f"  Weights:     {weights}")