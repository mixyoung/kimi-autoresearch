#!/usr/bin/env python3
"""
Autoresearch Code Applier - 代码修改执行器

自动执行代码修改，支持多种变换类型：
- add_type_hint: 添加类型注解
- remove_unused_import: 删除未使用的导入
- fix_formatting: 修复格式问题
- rename_variable: 重命名变量
- add_docstring: 添加文档字符串

Usage:
    python autoresearch_applier.py --dry-run --type add_type_hint --file src/utils.py --function parse_data
    python autoresearch_applier.py --apply --config transformation.json
"""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Union


@dataclass
class Transformation:
    """代码变换定义"""
    type: str  # add_type_hint, remove_unused_import, fix_formatting, rename_variable, add_docstring
    file: str
    description: str = ""
    
    # For add_type_hint
    function: Optional[str] = None
    params: Optional[dict] = None
    returns: Optional[str] = None
    
    # For rename_variable
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    line_number: Optional[int] = None
    
    # For remove_unused_import
    import_name: Optional[str] = None
    
    # For add_docstring
    docstring: Optional[str] = None


class CodeApplier:
    """代码修改执行器"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.changes_made = []
    
    def apply(self, transformation: Transformation) -> tuple[bool, str]:
        """
        执行代码修改
        
        Returns:
            (success, message)
        """
        file_path = Path(transformation.file)
        if not file_path.exists():
            return False, f"File not found: {transformation.file}"
        
        # 读取原始代码
        try:
            original_code = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return False, f"Failed to read file: {e}"
        
        # 根据类型执行不同的变换
        handlers = {
            'add_type_hint': self._apply_add_type_hint,
            'remove_unused_import': self._apply_remove_unused_import,
            'fix_formatting': self._apply_fix_formatting,
            'rename_variable': self._apply_rename_variable,
            'add_docstring': self._apply_add_docstring,
        }
        
        handler = handlers.get(transformation.type)
        if not handler:
            return False, f"Unknown transformation type: {transformation.type}"
        
        try:
            new_code = handler(original_code, transformation)
            
            if new_code == original_code:
                return False, "No changes made"
            
            # 验证新代码语法正确
            if not self._validate_syntax(new_code):
                return False, "Generated code has syntax errors"
            
            if self.dry_run:
                return True, "Dry run - changes validated but not applied"
            
            # 写回文件
            file_path.write_text(new_code, encoding='utf-8')
            self.changes_made.append(transformation)
            return True, f"Applied {transformation.type} to {transformation.file}"
            
        except Exception as e:
            return False, f"Failed to apply transformation: {e}"
    
    def _validate_syntax(self, code: str) -> bool:
        """验证代码语法是否正确"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _apply_add_type_hint(self, code: str, t: Transformation) -> str:
        """为函数添加类型注解"""
        if not t.function:
            return code
        
        lines = code.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 查找函数定义
            pattern = rf'^(\s*)def\s+{re.escape(t.function)}\s*\('
            match = re.match(pattern, line)
            
            if match:
                indent = match.group(1)
                
                # 提取当前函数签名
                func_start = i
                func_lines = [line]
                j = i + 1
                
                # 收集多行签名
                while j < len(lines) and not lines[j].strip().endswith(':'):
                    func_lines.append(lines[j])
                    j += 1
                if j < len(lines):
                    func_lines.append(lines[j])
                    j += 1
                
                # 解析并重建函数签名
                original_sig = '\n'.join(func_lines)
                new_sig = self._add_type_annotations(original_sig, t.params, t.returns)
                
                result_lines.extend(new_sig.split('\n'))
                i = j
                continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def _add_type_annotations(self, func_sig: str, params: Optional[dict], returns: Optional[str]) -> str:
        """为函数签名添加类型注解"""
        # 简单实现：使用正则替换
        lines = func_sig.split('\n')
        result = []
        
        for line in lines:
            # 处理参数
            if params:
                for param_name, param_type in params.items():
                    # 匹配参数名，添加类型注解
                    pattern = rf'([(,]\s*){re.escape(param_name)}(\s*[,)])'
                    replacement = rf'\1{param_name}: {param_type}\2'
                    line = re.sub(pattern, replacement, line)
                    
                    # 处理行首的参数（def 后的第一个参数）
                    pattern = rf'(def\s+\w+\s*\(\s*){re.escape(param_name)}(\s*[,)])'
                    replacement = rf'\1{param_name}: {param_type}\2'
                    line = re.sub(pattern, replacement, line)
            
            # 处理返回值
            if returns and line.strip().endswith(':'):
                # 检查是否已有返回类型注解
                if '->' not in line:
                    line = line.rstrip(':') + f' -> {returns}:'
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _apply_remove_unused_import(self, code: str, t: Transformation) -> str:
        """删除未使用的导入"""
        if not t.import_name:
            return code
        
        lines = code.split('\n')
        result = []
        
        for line in lines:
            # 匹配各种导入形式
            patterns = [
                rf'^\s*import\s+{re.escape(t.import_name)}\s*$',
                rf'^\s*from\s+\S+\s+import\s+.*\b{re.escape(t.import_name)}\b.*$',
            ]
            
            should_remove = any(re.match(p, line) for p in patterns)
            
            if not should_remove:
                result.append(line)
        
        return '\n'.join(result)
    
    def _apply_fix_formatting(self, code: str, t: Transformation) -> str:
        """修复格式问题（简单实现）"""
        lines = code.split('\n')
        result = []
        
        for line in lines:
            # 去除行尾空格
            line = line.rstrip()
            # 确保文件末尾有空行
            result.append(line)
        
        # 确保文件末尾有且只有一个空行
        while result and result[-1] == '':
            result.pop()
        result.append('')
        
        return '\n'.join(result)
    
    def _apply_rename_variable(self, code: str, t: Transformation) -> str:
        """重命名变量"""
        if not t.old_name or not t.new_name:
            return code
        
        # 使用正则替换，但要避免替换字符串中的内容
        # 简单实现：只替换标识符
        pattern = rf'\b{re.escape(t.old_name)}\b'
        return re.sub(pattern, t.new_name, code)
    
    def _apply_add_docstring(self, code: str, t: Transformation) -> str:
        """添加文档字符串"""
        if not t.function or not t.docstring:
            return code
        
        lines = code.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            result.append(line)
            
            # 查找函数定义
            pattern = rf'^(\s*)def\s+{re.escape(t.function)}\s*\('
            match = re.match(pattern, line)
            
            if match:
                indent = match.group(1)
                base_indent = indent + '    '
                
                # 找到函数体的开始（冒号后的下一行）
                j = i + 1
                # 跳过函数签名剩余部分
                while j < len(lines) and not lines[j-1].strip().endswith(':'):
                    result.append(lines[j])
                    j += 1
                
                # 检查是否已有文档字符串
                if j < len(lines):
                    next_line = lines[j].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        # 添加文档字符串
                        docstring_lines = [
                            f"{base_indent}\"\"\"{t.docstring}\"\"\""
                        ]
                        result.extend(docstring_lines)
                
                i = j
                continue
            
            i += 1
        
        return '\n'.join(result)


def main():
    parser = argparse.ArgumentParser(description='Apply code transformations')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Validate changes without applying')
    parser.add_argument('--config', type=str,
                       help='JSON config file with transformation')
    parser.add_argument('--type', type=str,
                       choices=['add_type_hint', 'remove_unused_import', 
                               'fix_formatting', 'rename_variable', 'add_docstring'])
    parser.add_argument('--file', type=str, help='Target file')
    parser.add_argument('--function', type=str, help='Target function name')
    parser.add_argument('--output', type=str, help='Output result to JSON file')
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        transformation = Transformation(**config)
    elif args.type and args.file:
        transformation = Transformation(
            type=args.type,
            file=args.file,
            function=args.function
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    # 执行变换
    applier = CodeApplier(dry_run=args.dry_run)
    success, message = applier.apply(transformation)
    
    result = {
        'success': success,
        'message': message,
        'transformation': asdict(transformation),
        'dry_run': args.dry_run
    }
    
    print(json.dumps(result, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
