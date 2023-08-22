import os
import os.path as p
import re

from NikoKit.NikoMaya.public_functions import get_texture_from_text


def sort_shots(lst):
    def key_func(s):
        numeric_part = ''.join(filter(str.isdigit, s))
        non_numeric_part = ''.join(filter(str.isalpha, s))
        return int(numeric_part), non_numeric_part

    return sorted(lst, key=key_func)


def get_shots_from_dir(target_dir, hide_type=True):
    scene_to_shots = {}

    for root, dirs, files in os.walk(target_dir):
        pattern = r"sc(\d+[a-zA-Z]?)_shot(\d+[a-zA-Z]?)_([a-zA-Z]+)_v\d+\.(?:ma|mov)"

        for file in files:
            match = re.match(pattern, file.lower())
            if match:
                scene_no = match.group(1)
                shot_no = match.group(2)
                while len(shot_no) > 1 and shot_no[0] == "0":
                    shot_no = shot_no[1:]
                ma_type = match.group(3)
                if scene_no not in scene_to_shots:
                    scene_to_shots[scene_no] = set()
                if hide_type:
                    scene_to_shots[scene_no].add(f"{shot_no}")
                else:
                    scene_to_shots[scene_no].add(f"{shot_no}{ma_type}")

    for scene_no in scene_to_shots.keys():
        scene_to_shots[scene_no] = sort_shots(list(scene_to_shots[scene_no]))
        scene_to_shots[scene_no] = [str(shot) for shot in scene_to_shots[scene_no]]

    scene_info_list = []
    for scene_no, shot_no in scene_to_shots.items():
        scene_info_list.append(f"sc{scene_no}:{','.join(shot_no)}")

    return ";".join(scene_info_list)


def compare_shots(str_a, str_b):
    # Split the strings into scenes and shots
    a = str_a.split(":")
    b = str_b.split(":")

    # Check if the scenes match
    if a[0] != b[0]:
        return "Scene unmatched", "Scene unmatched"

    # Split the shots into a set to easily find additions and subtractions
    a_shots = set(a[1].split(","))
    b_shots = set(b[1].split(","))

    # Find the additions and subtractions
    additions = sort_shots(list(b_shots - a_shots))
    subtractions = sort_shots(list(a_shots - b_shots))

    return additions, subtractions


def get_latest_maya_file(maya_dir):
    ma_files = [file for file in os.listdir(maya_dir) if file.endswith('.ma')]

    version_pattern = r'_v(\d+)\.ma'
    latest_version = 0
    latest_file = None

    for file_name in ma_files:
        match = re.search(version_pattern, file_name)
        if match:
            version_number = int(match.group(1))
            if version_number > latest_version:
                latest_version = version_number
                latest_file = p.join(maya_dir, file_name)

    return latest_file


def analyze_low_model_resource(asset_dir, asset_type):
    low_mod_dir = p.join(asset_dir, "Mod", "Low")
    low_rig_dir = p.join(asset_dir, "Rig", "Low")
    low_mod_path = get_latest_maya_file(low_mod_dir)
    low_rig_path = get_latest_maya_file(low_rig_dir)
    folder_list = [p.join(low_mod_dir, "*"),
                   p.join(low_rig_dir, "*"),
                   p.join(asset_dir, "Xgen", "*")]

    required_texture_paths = []

    if low_mod_path is not None:
        required_texture_paths.extend(get_texture_from_text(low_mod_path))
    if low_rig_path is not None:
        required_texture_paths.extend(get_texture_from_text(low_rig_path))

    required_texture_paths = list(set([p.normpath(t_path) for t_path in required_texture_paths]))
    texture_valid_paths = []
    texture_invalid_paths = []
    for t_path in required_texture_paths:
        if p.isfile(t_path):
            texture_valid_paths.append(t_path)
        else:
            texture_invalid_paths.append(t_path)

    return folder_list, texture_valid_paths, texture_invalid_paths
