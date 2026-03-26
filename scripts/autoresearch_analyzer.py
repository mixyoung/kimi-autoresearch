#!/usr/bin/env python3
"""
Autoresearch Code Analyzer - 代码分析器

自动分析代码库，识别改进点并生成变换建议。

Usage:
    python autoresearch_analyzer.py --goal "add type hints" --scope "scripts/*.py"
    python autoresearch_analyzer.py --goal "remove unused imports" --scope "src/**/*.py"
"""

import argparse
import ast
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class AnalysisIssue:
    """发现的问题"""
    type: str  # missing_type_hint, unused_import, missing_docstring, etc.
    file: str
    line: int
    column: int
    message: str
    severity: str = "info"  # info, warning, error
    suggestion: Optional[str] = None


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    line: int
    params: List[str]
    has_type_hints: bool
    has_docstring: bool
    returns: Optional[str] = None


@dataclass
class AnalysisResult:
    """分析结果"""
    files_analyzed: int
    issues: List[AnalysisIssue]
    functions: List[FunctionInfo]
    suggestions: List[dict]


class PythonAnalyzer:
    """Python 代码分析器"""
    
    def __init__(self, goal: str):
        self.goal = goal.lower()
        self.issues = []
        self.functions = []
    
    def analyze_file(self, file_path: Path) -> None:
        """分析单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except SyntaxError as e:
            self.issues.append(AnalysisIssue(
                type="syntax_error",
                file=str(file_path),
                line=e.lineno or 1,
                column=e.offset or 0,
                message=f"Syntax error: {e}",
                severity="error"
            ))
            return
        except Exception as e:
            self.issues.append(AnalysisIssue(
                type="read_error",
                file=str(file_path),
                line=1,
                column=0,
                message=f"Failed to read: {e}",
                severity="error"
            ))
            return
        
        # 根据目标选择分析方法
        if 'type' in self.goal or 'hint' in self.goal:
            self._analyze_type_hints(tree, file_path, content)
        
        if 'import' in self.goal or 'unused' in self.goal:
            self._analyze_imports(tree, file_path, content)
        
        if 'docstring' in self.goal or 'document' in self.goal:
            self._analyze_docstrings(tree, file_path, content)
        
        if 'format' in self.goal:
            self._analyze_formatting(tree, file_path, content)
    
    def _analyze_type_hints(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """分析类型注解缺失"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查参数类型
                missing_params = []
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != 'self':
                        missing_params.append(arg.arg)
                
                # 检查返回值类型
                missing_return = node.returns is None
                
                func_info = FunctionInfo(
                    name=node.name,
                    line=node.lineno,
                    params=[arg.arg for arg in node.args.args],
                    has_type_hints=len(missing_params) == 0 and not missing_return,
                    has_docstring=self._has_docstring(node),
                    returns=ast.unparse(node.returns) if node.returns else None
                )
                self.functions.append(func_info)
                
                # 记录问题
                if missing_params or missing_return:
                    message = f"Function '{node.name}' missing type hints"
                    details = []
                    if missing_params:
                        details.append(f"params: {', '.join(missing_params)}")
                    if missing_return:
                        details.append("return type")
                    
                    self.issues.append(AnalysisIssue(
                        type="missing_type_hint",
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"{message} ({', '.join(details)})",
                        severity="warning",
                        suggestion=f"Add type hints to {node.name}"
                    ))
    
    def _analyze_imports(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """分析未使用的导入"""
        imports = {}
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name] = {
                        'name': alias.name,
                        'asname': alias.asname,
                        'node': node,
                        'used': False
                    }
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = {
                        'name': name,
                        'full': f"{node.module}.{alias.name}" if node.module else alias.name,
                        'node': node,
                        'used': False
                    }
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        # 检查使用情况
        for name, info in imports.items():
            if name not in used_names and name != '*':
                self.issues.append(AnalysisIssue(
                    type="unused_import",
                    file=str(file_path),
                    line=info['node'].lineno,
                    column=info['node'].col_offset,
                    message=f"Unused import: {name}",
                    severity="info",
                    suggestion=f"Remove unused import: {name}"
                ))
    
    def _analyze_docstrings(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """分析文档字符串缺失"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if not self._has_docstring(node):
                    self.issues.append(AnalysisIssue(
                        type="missing_docstring",
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"{node.__class__.__name__} '{node.name}' missing docstring",
                        severity="info",
                        suggestion=f"Add docstring to {node.name}"
                    ))
    
    def _analyze_formatting(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """分析格式问题"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 行尾空格
            if line.rstrip() != line:
                self.issues.append(AnalysisIssue(
                    type="trailing_whitespace",
                    file=str(file_path),
                    line=i,
                    column=len(line.rstrip()),
                    message="Trailing whitespace",
                    severity="info",
                    suggestion="Remove trailing whitespace"
                ))
        
        # 文件末尾空行
        if content and not content.endswith('\n'):
            self.issues.append(AnalysisIssue(
                type="missing_final_newline",
                file=str(file_path),
                line=len(lines),
                column=0,
                message="File does not end with newline",
                severity="info",
                suggestion="Add final newline"
            ))
    
    def _has_docstring(self, node) -> bool:
        """检查节点是否有文档字符串"""
        if not node.body:
            return False
        first = node.body[0]
        return isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
    
    def generate_suggestions(self) -> List[dict]:
        """基于分析结果生成变换建议"""
        suggestions = []
        
        # 按文件分组
        by_file = {}
        for issue in self.issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)
        
        # 为每个文件生成建议
        for file_path, issues in by_file.items():
            for issue in issues:
                suggestion = self._issue_to_suggestion(issue)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _issue_to_suggestion(self, issue: AnalysisIssue) -> Optional[dict]:
        """将问题转换为变换建议"""
        if issue.type == "missing_type_hint":
            # 解析函数名
            import re
            match = re.search(r"Function '(.+)'", issue.message)
            if match:
                func_name = match.group(1)
                return {
                    "type": "add_type_hint",
                    "file": issue.file,
                    "function": func_name,
                    "description": issue.suggestion,
                    "confidence": 0.8
                }
        
        elif issue.type == "unused_import":
            import re
            match = re.search(r"Unused import: (.+)", issue.message)
            if match:
                import_name = match.group(1)
                return {
                    "type": "remove_unused_import",
                    "file": issue.file,
                    "import_name": import_name,
                    "description": issue.suggestion,
                    "confidence": 0.9
                }
        
        elif issue.type == "missing_docstring":
            import re
            match = re.search(r"'(.+)' missing", issue.message)
            if match:
                name = match.group(1)
                return {
                    "type": "add_docstring",
                    "file": issue.file,
                    "function": name,
                    "docstring": f"TODO: Add documentation for {name}",
                    "description": issue.suggestion,
                    "confidence": 0.7
                }
        
        elif issue.type == "trailing_whitespace":
            return {
                "type": "fix_formatting",
                "file": issue.file,
                "description": "Fix formatting issues",
                "confidence": 0.95
            }
        
        return None


class CodeAnalyzer:
    """主分析器"""
    
    def __init__(self, goal: str, scope: str):
        self.goal = goal
        self.scope = scope
        self.python_analyzer = PythonAnalyzer(goal)
    
    def analyze(self) -> AnalysisResult:
        """执行分析"""
        # 解析 scope 模式
        files = self._find_files()
        
        # 分析每个文件
        for file_path in files:
            self.python_analyzer.analyze_file(file_path)
        
        # 生成建议
        suggestions = self.python_analyzer.generate_suggestions()
        
        return AnalysisResult(
            files_analyzed=len(files),
            issues=self.python_analyzer.issues,
            functions=self.python_analyzer.functions,
            suggestions=suggestions
        )
    
    def _find_files(self) -> List[Path]:
        """根据 scope 查找文件"""
        files = []
        
        # 简单实现：支持 glob 模式
        import glob
        
        # 如果是目录，递归查找
        scope_path = Path(self.scope)
        if scope_path.is_dir():
            pattern = str(scope_path / "**" / "*.py")
        else:
            pattern = self.scope
        
        for file_path in glob.glob(pattern, recursive=True):
            path = Path(file_path)
            if path.is_file() and path.suffix == '.py':
                files.append(path)
        
        return sorted(files)


def main():
    parser = argparse.ArgumentParser(description='Analyze code for improvements')
    parser.add_argument('--goal', type=str, required=True,
                       help='Analysis goal (e.g., "add type hints", "remove unused imports")')
    parser.add_argument('--scope', type=str, required=True,
                       help='File scope pattern (e.g., "scripts/*.py", "src/")')
    parser.add_argument('--output', type=str,
                       help='Output JSON file')
    parser.add_argument('--format', type=str, default='json',
                       choices=['json', 'text'],
                       help='Output format')
    
    args = parser.parse_args()
    
    # 执行分析
    analyzer = CodeAnalyzer(args.goal, args.scope)
    result = analyzer.analyze()
    
    # 转换为可序列化的格式
    output = {
        'files_analyzed': result.files_analyzed,
        'issues_count': len(result.issues),
        'suggestions_count': len(result.suggestions),
        'issues': [asdict(i) for i in result.issues],
        'functions': [asdict(f) for f in result.functions],
        'suggestions': result.suggestions
    }
    
    # 输出结果
    if args.format == 'json':
        text = json.dumps(output, indent=2)
    else:
        # Text format
        lines = [
            f"Files analyzed: {result.files_analyzed}",
            f"Issues found: {len(result.issues)}",
            f"Suggestions: {len(result.suggestions)}",
            "",
            "Top Issues:",
        ]
        for issue in result.issues[:10]:
            lines.append(f"  [{issue.severity}] {issue.file}:{issue.line} - {issue.message}")
        
        if len(result.issues) > 10:
            lines.append(f"  ... and {len(result.issues) - 10} more")
        
        lines.append("")
        lines.append("Top Suggestions:")
        for sugg in result.suggestions[:5]:
            lines.append(f"  [{sugg['confidence']:.0%}] {sugg['type']} in {sugg['file']}")
        
        text = '\n'.join(lines)
    
    print(text)
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w') as f:
            f.write(text)
        print(f"\nResults saved to {args.output}")
    
    return 0 if len(result.issues) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
