import os
import re


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
