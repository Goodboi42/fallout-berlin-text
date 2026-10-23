import sys
import textwrap

def create_asset_entry(archive_path):
    """
    Interactive tool to extract ASCII art from an archive and generate
    a Python dictionary entry for the ArtAssetManager.
    """
    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Archive file not found at '{archive_path}'")
        sys.exit(1)

    print("--- ASCII Art Asset Importer ---")
    print(f"Loaded {len(lines)} lines from {archive_path}\n")

    while True:
        asset_id = input("Enter Asset ID (e.g., 'brandenburg_gate_ruins'): ")
        if not asset_id:
            print("Asset ID cannot be empty.")
            continue

        try:
            start_line = int(input(f"Enter start line number for '{asset_id}': ")) - 1
            end_line = int(input(f"Enter end line number for '{asset_id}': "))
        except ValueError:
            print("Invalid line number. Please enter integers.")
            continue

        if not (0 <= start_line < end_line <= len(lines)):
            print("Invalid line range.")
            continue

        alt_text = input("Enter a one-line alt_text description: ")

        # Extract and format the art
        art_lines = [line.rstrip('\n') for line in lines[start_line:end_line]]
        art_string = "\n".join(art_lines)

        # Create the Python dictionary entry string
        formatted_art = textwrap.indent(f'r"""\n{art_string}\n"""', '            ')

        output = textwrap.dedent(f"""
        "{asset_id}": {{
            "art": (
{formatted_art.lstrip()}
            ),
            "alt_text": "{alt_text}"
        }},
        """)

        print("\n--- Generated Asset Entry ---\n")
        print(output)
        print("\nCopy the above text into your art library dictionary.")

        another = input("Add another asset? (y/n): ").lower()
        if another != 'y':
            break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/art_importer.py <path_to_art_archive.txt>")
        sys.exit(1)
    
    archive_file = sys.argv[1]
    create_asset_entry(archive_file)