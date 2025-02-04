# craws directory and subdirectories to count lines of code in files

import os
import sys
import argparse

def count_lines(directory, file_types=['.py', '.js', '.html', '.css', '.scss', '.sass', '.less', '.json', '.xml', '.txt', '.md']):
    total_lines = 0
    total_files = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(file_types)):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        total_files += 1
                except Exception as e:
                    print(f'Error reading file {os.path.join(root, file)}: {e}')
        
        for dir in dirs:
            new_dir = os.path.join(root, dir)
            lines, files = count_lines(new_dir, file_types)
            total_lines += lines
            total_files += files
    return total_lines, total_files

def main():
    parser = argparse.ArgumentParser(description='Count lines of code in files in a directory')
    parser.add_argument('-d', '--directory', type=str, help='directory to search for files', default='.')
    parser.add_argument('-t', '--file_types', nargs='+', type=str, help='file types to search for')
    args = parser.parse_args()

    directory = args.directory
    file_types = args.file_types

    if file_types is None:
        file_types = ['.py', '.js', '.html', '.css', '.scss', '.sass', '.less', '.json', '.xml', '.txt', '.md']

    lines, files = count_lines(directory, file_types)
    print(f'Total lines: {lines}')
    print(f'Total files: {files}')
    
if __name__ == '__main__':
    main()