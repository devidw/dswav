import os
import random
import shutil


def copy_files(src_dir, dest_dir):
    for filename in os.listdir(src_dir):
        src_file = os.path.join(src_dir, filename)
        dest_file = os.path.join(dest_dir, filename)

        if os.path.isfile(src_file) and not os.path.exists(dest_file):
            shutil.copy2(src_file, dest_file)


def split_list(input_list, percentage):
    """
    Splits a list into two parts with the given percentage.

    :param input_list: The list to be split.
    :param percentage: The percentage of the first list (between 0 and 1).
    :return: Two lists.
    """
    if not 0 <= percentage <= 1:
        raise ValueError("Percentage must be between 0 and 1")

    list_length = len(input_list)
    split_index = int(list_length * percentage)

    random.shuffle(input_list)
    return input_list[:split_index], input_list[split_index:]
