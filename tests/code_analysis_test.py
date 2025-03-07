from modules.code_analysis import CodeAnalysisService


if __name__ == "__main__":
    analyze = CodeAnalysisService()
    result = analyze.get_file_content(
        "./tests/clipboard_test.py",
        element_type="function",
        element_name="test_clipboard_write_handler",
    )
    print(result)
