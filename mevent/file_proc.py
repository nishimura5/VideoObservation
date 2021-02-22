import shutil
import pathlib
import re

def is_all_ascii_in_path(src_path):
    match = re.fullmatch('[ -~]+', src_path)
    if match is None:
        return 'ng'
    else:
        return 'ok'

def gen_mevent_path(tar_path):
    tar_path = pathlib.Path(tar_path)
    parent_path = tar_path.parents[1]
    mevent_path = parent_path.joinpath('mevent', tar_path.name).with_suffix('.mevent')
    return mevent_path

def move_file(tar_path, folder_name_list):
    tar_path = pathlib.Path(tar_path)
    parent_path = tar_path.parent
    if parent_path.name not in (folder_name_list):
        new_path = parent_path.joinpath(folder_name_list[0])
        new_path.mkdir(exist_ok=True)
        ## 移動先に同名ファイルがあったら例外吐く
        moved_path = shutil.move(str(tar_path), str(new_path))
    else:
        moved_path = tar_path
    return moved_path

if __name__ == "__main__":
    pass

