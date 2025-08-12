# Utils module initialization
from .text_utils import (
    detect_encoding,
    normalize_text,
    extract_number_from_string,
    calculate_text_similarity,
    split_text_by_years,
    clean_path_string
)
from .file_utils import (
    is_valid_text_file,
    get_file_size_formatted,
    create_backup,
    ensure_directory_exists,
    resolve_path_safely
)
from .display_utils import (
    print_colored,
    print_header,
    print_section,
    print_progress,
    format_table,
    truncate_path
)

__all__ = [
    # text_utils
    'detect_encoding',
    'normalize_text',
    'extract_number_from_string',
    'calculate_text_similarity',
    'split_text_by_years',
    'clean_path_string',
    # file_utils
    'is_valid_text_file',
    'get_file_size_formatted',
    'create_backup',
    'ensure_directory_exists',
    'resolve_path_safely',
    # display_utils
    'print_colored',
    'print_header',
    'print_section',
    'print_progress',
    'format_table',
    'truncate_path',
]