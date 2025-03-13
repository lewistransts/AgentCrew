from modules.code_analysis import CodeAnalysisService


if __name__ == "__main__":
    analyze = CodeAnalysisService()
    result = analyze.analyze_code_structure(
        "./",
    )
    print(result)
