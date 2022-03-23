import os
import time
import pickle
import gzip
import shutil
import yaml
from functools import reduce
import argparse

# Il programma crea una backup directory se non esiste
# la prima volta genera index.gz dal dizionario con le absolute path dei file della working directory locale
# le volte successive aggiorna il dizionario e riscrive index.gz
# nella backup directory copia i soli file modificati o nuovi

def backup(source_dir: str, destination_dir: str, index: dict):
    idx = {}
    source_dir = source_dir.rstrip(os.sep)
    start = source_dir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(source_dir):
        folders = path[start:].split(os.sep)
        cur_dest_dir = os.path.join(destination_dir, path[start:])
        try:
            # check if folder exists (without going to the destination filesystem)
            index_cur = index
            for element in folders:
                index_cur = index_cur[element]
        except Exception as ex:
            # create folder
            try:
                os.mkdir(cur_dest_dir)
            except FileExistsError:
                print(f'Error folder {cur_dest_dir} was not in the index, but already exists. Continuing.')
            index_cur = {}

        subdir = {}
        for f in files:
            # check if file exists (without going to the destination filesystem)
            cur_src_file = os.path.join(path, f)
            subdir[f] = os.path.getmtime(cur_src_file)
            if f not in index_cur or index_cur[f] < subdir[f]:
                # create or update file
                cur_dst_file = os.path.join(cur_dest_dir, f)
                shutil.copy2(cur_src_file, cur_dst_file)

        parent = reduce(dict.get, folders[:-1], idx)
        parent[folders[-1]] = subdir
    return idx


def rebuild_index(destination_dir: str):
    idx = {}
    destination_dir = destination_dir.rstrip(os.sep)
    start = destination_dir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(destination_dir):
        folders = path[start:].split(os.sep)
        subdir = {}
        for f in files:
            cur_src_file = os.path.join(path, f)
            subdir[f] = os.path.getmtime(cur_src_file)
        parent = reduce(dict.get, folders[:-1], idx)
        parent[folders[-1]] = subdir
    return idx[destination_dir[start:]]


def main():
    def is_list_of_strings(lst):
        if lst and isinstance(lst, list):
            return all(isinstance(elem, str) for elem in lst)
        else:
            return False

    parser = argparse.ArgumentParser(description='A simple incremental backup script, with destination indexing.')
    parser.add_argument('-c', '--config_filename', help='Name of the configuration file', default='config.yaml')
    parser.add_argument('-i', '--index_filename', help='Name of the index file', default='index.gz')
    parser.add_argument('-r', '--rebuild', action='store_true', help="Rebuild the destination index", default=False)
    args = parser.parse_args()

    start_time = time.time()

    config = {}
    try:
        config = yaml.safe_load(open(args.config_filename))
    except Exception as ex:
        print(f'Error {ex}')
        exit()

    source_dir: list[str] = config['source_dir']
    if isinstance(source_dir, str):
        source_dir = [source_dir]
    if not is_list_of_strings(source_dir):
        print('Error: source_dir must be a folder or a list of folders')
        exit()

    destination_dir: str = config['dest_dir']
    # check if the backup directory exists
    if os.path.exists(destination_dir) and os.path.isdir(destination_dir):
        print("Backup Directory:", destination_dir)
    else:
        try:
            os.mkdir(destination_dir)
            print("Created Backup Directory:" + destination_dir)
        except OSError as e:
            print("Error:", e.strerror)
            print("Failed to create Backup Directory:" + destination_dir)
            return

    index_filename = os.path.join(destination_dir, args.index_filename)
    index = None
    if args.rebuild:
        print(f'Rebuilding index of {destination_dir}...', end='')
        index = rebuild_index(destination_dir)
        print(' done.')
    else:
        try:
            index = pickle.load(gzip.open(index_filename, "rb"))
        except IOError as err:
            pass

    new_index = {}
    for cur_source_dir in source_dir:
        print(f'Backup of {cur_source_dir}...', end='')
        new_index.update(backup(cur_source_dir, destination_dir, index))
        print(' done.')

    print(f'Saving index {index_filename}...', end='')
    pickle.dump(new_index, gzip.open(index_filename, "wb"))
    print(' done.')

    end_time = time.time()
    total_time = end_time - start_time
    print(f'Total time: {total_time} s ({total_time/60} min)')


if __name__ == '__main__':
    main()
