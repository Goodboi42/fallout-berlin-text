"""
Map Visualization Tool for Fallout: Berlin
Generates a Graphviz diagram of the game world connectivity.
"""
import sys
import os

# Ensure we can import the game modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock colorama if missing to allow visualization without game dependencies
try:
    import colorama
except ImportError:
    import types
    mock_colorama = types.ModuleType("colorama")
    mock_colorama.init = lambda *args, **kwargs: None
    class MockAnsi:
        def __getattr__(self, name): return ""
    mock_colorama.Fore = MockAnsi()
    mock_colorama.Back = MockAnsi()
    mock_colorama.Style = MockAnsi()
    sys.modules["colorama"] = mock_colorama

from fallout_berlin.location import LocationManager

try:
    from graphviz import Digraph
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

def main():
    print("Loading Fallout: Berlin World Data...")
    manager = LocationManager()
    
    # The manager automatically restores missing content in __init__
    locations = manager.locations
    print(f"Found {len(locations)} locations.")

    if HAS_GRAPHVIZ:
        visualize_graphviz(locations)
    else:
        print("\n[!] 'graphviz' library not found. Install with: pip install graphviz")
        print("    You also need the Graphviz software installed on your OS.")
        print("\nGenerating text-based map instead...\n")
        visualize_text(locations)

def visualize_graphviz(locations):
    dot = Digraph(comment='Fallout: Berlin Map', format='png')
    dot.attr(rankdir='TB', overlap='false', splines='ortho', nodesep='0.8', ranksep='1.0')
    
    # Styling
    dot.attr('node', shape='box', style='filled,rounded', fontname='Courier', penwidth='2')
    dot.attr('edge', fontname='Courier', fontsize='10')

    # Subgraphs for logical zones
    with dot.subgraph(name='cluster_surface') as surface:
        surface.attr(label='Surface Level', color='grey', style='dashed')
        
        with dot.subgraph(name='cluster_underground') as underground:
            underground.attr(label='Underground / U-Bahn', color='black', style='filled', fillcolor='#222222', fontcolor='white')
            
            for loc_id, loc in locations.items():
                # Determine type/color
                fillcolor = '#ffffff' # Default white
                fontcolor = 'black'
                
                is_underground = any(x in loc_id for x in ['u_bahn', 'vault', 'bunker', 'tunnel', 'sewer'])
                
                if loc.get_property('hostile'):
                    fillcolor = '#ffcccc' # Red tint
                elif loc.get_property('safe'):
                    fillcolor = '#ccffcc' # Green tint
                
                if is_underground:
                    if fillcolor == '#ffffff': fillcolor = '#444444'
                    fontcolor = 'white'
                    underground.node(loc_id, f"{loc.name}\n[{loc_id}]", fillcolor=fillcolor, fontcolor=fontcolor)
                else:
                    surface.node(loc_id, f"{loc.name}\n[{loc_id}]", fillcolor=fillcolor, fontcolor=fontcolor)

    # Edges
    for loc_id, loc in locations.items():
        for direction, target_id in loc.connections.items():
            # Color code vertical movement
            color = 'black'
            style = 'solid'
            if direction in ['up', 'down', 'enter', 'exit']:
                color = 'blue'
                style = 'dashed'
            
            dot.edge(loc_id, target_id, label=direction, color=color, style=style)

    output_file = 'fallout_berlin_map'
    try:
        output_path = dot.render(output_file, view=True)
        print(f"\nMap generated successfully: {output_path}")
    except Exception as e:
        print(f"\nError generating map image: {e}")

def visualize_text(locations):
    # Simple adjacency list
    for loc_id in sorted(locations.keys()):
        loc = locations[loc_id]
        print(f"LOCATION: {loc.name} [{loc_id}]")
        if loc.get_property('hostile'): print("  (Hostile Area)")
        if loc.get_property('safe'): print("  (Safe Zone)")
        
        print("  Connections:")
        if not loc.connections:
            print("    None")
        for direction, target_id in loc.connections.items():
            target_name = locations[target_id].name if target_id in locations else "UNKNOWN"
            print(f"    -> {direction.upper()}: {target_name}")
        print("-" * 40)

if __name__ == "__main__":
    main()