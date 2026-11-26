"""Refresh Unreal grip sockets after reimporting the authored wall mesh."""
from pathlib import Path
import runpy
import unreal

project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
route = runpy.run_path(str(project / 'SourceArt/RooftopClimbing/wall_route.py'))
wall = unreal.load_asset('/Game/Parkour/Environment/RooftopClimbing/SM_RooftopHolds')
# Use a transient mesh component to enumerate the existing socket names.
component = unreal.StaticMeshComponent()
component.set_static_mesh(wall)
for name in component.get_all_socket_names():
    if str(name).startswith(('Grip_', 'Toe_')):
        wall.remove_socket(wall.find_socket(name))

def add_socket(name, location):
    socket = unreal.StaticMeshSocket(outer=wall)
    socket.set_editor_property('socket_name', name)
    socket.set_editor_property('relative_location', unreal.Vector(*location))
    wall.add_socket(socket)

for row, band in enumerate(route['WALL_ROUTE']):
    for col, (y, z) in enumerate(band):
        add_socket(f'Grip_{row}_{col}', (-4, y, z))
for index, (y, z) in enumerate(route['TOE_CHIPS']):
    add_socket(f'Toe_{index}', (-3, y, z))
unreal.EditorAssetLibrary.save_loaded_asset(wall, False)
