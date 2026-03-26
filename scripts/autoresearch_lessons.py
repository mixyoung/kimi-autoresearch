#!/usr/bin/env python3
"""
Lessons management for autoresearch.
Tracks what worked, what didn't, and why across runs.
"""
import argparse
import json
import os
from datetime import datetime
from typing import Optional

LESSONS_FILE = "autoresearch-lessons.md"
STATE_FILE = "autoresearch-state.json"


class LessonManager:
    def __init__(self):
        self.lessons_file = LESSONS_FILE
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Create lessons file if not exists."""
        if not os.path.exists(self.lessons_file):
            with open(self.lessons_file, 'w') as f:
                f.write("# Autoresearch Lessons Learned\n\n")
                f.write("Track what works and what doesn't across runs.\n\n")
                f.write("---\n\n")
    
    def add_lesson(self, lesson: str, lesson_type: str = 'positive',
                   context: Optional[dict] = None):
        """Add a new lesson."""
        timestamp = datetime.now().isoformat()
        
        entry = f"\n## {timestamp}\n\n"
        entry += f"**Type**: {lesson_type}\n\n"
        
        if context:
            entry += f"**Context**:\n"
            for key, value in context.items():
                entry += f"- {key}: {value}\n"
            entry += "\n"
        
        entry += f"**Lesson**: {lesson}\n\n"
        entry += "---\n"
        
        with open(self.lessons_file, 'a') as f:
            f.write(entry)
        
        return True
    
    def list_lessons(self, lesson_type: Optional[str] = None,
                    limit: int = 10) -> list[dict]:
        """List recent lessons."""
        if not os.path.exists(self.lessons_file):
            return []
        
        with open(self.lessons_file, 'r') as f:
            content = f.read()
        
        # Parse lessons (simple parsing)
        lessons = []
        sections = content.split('\n## ')
        
        for section in sections[1:]:  # Skip header
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            timestamp = lines[0].strip()
            
            lesson_data = {
                'timestamp': timestamp,
                'type': 'unknown',
                'context': {},
                'lesson': ''
            }
            
            in_lesson = False
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('**Type**:'):
                    lesson_data['type'] = line.split(':', 1)[1].strip()
                elif line.startswith('**Context**:'):
                    in_lesson = False
                elif line.startswith('- ') and not in_lesson:
                    parts = line[2:].split(':', 1)
                    if len(parts) == 2:
                        lesson_data['context'][parts[0]] = parts[1].strip()
                elif line.startswith('**Lesson**:'):
                    in_lesson = True
                    lesson_data['lesson'] = line.split(':', 1)[1].strip()
                elif in_lesson and line:
                    lesson_data['lesson'] += ' ' + line
            
            if lesson_type and lesson_data['type'] != lesson_type:
                continue
            
            lessons.append(lesson_data)
        
        # Sort by timestamp (newest first) and limit
        lessons.reverse()
        return lessons[:limit]
    
    def get_relevant_lessons(self, context: dict, limit: int = 5) -> list[dict]:
        """Get lessons relevant to current context."""
        all_lessons = self.list_lessons(limit=50)
        
        # Simple relevance scoring
        scored = []
        for lesson in all_lessons:
            score = 0
            lesson_context = lesson.get('context', {})
            
            for key, value in context.items():
                if key in lesson_context:
                    if lesson_context[key] == value:
                        score += 2
                    else:
                        score += 1
            
            scored.append((score, lesson))
        
        # Sort by score and return top
        scored.sort(key=lambda x: x[0], reverse=True)
        return [lesson for _, lesson in scored[:limit]]
    
    def summarize(self) -> dict:
        """Summarize lessons learned."""
        lessons = self.list_lessons(limit=1000)
        
        by_type = {}
        for lesson in lessons:
            t = lesson.get('type', 'unknown')
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            'total_lessons': len(lessons),
            'by_type': by_type,
            'recent': lessons[:5]
        }


def cmd_add(args):
    """Add a lesson."""
    manager = LessonManager()
    
    context = {}
    if args.goal:
        context['goal'] = args.goal
    if args.strategy:
        context['strategy'] = args.strategy
    if args.iteration:
        context['iteration'] = args.iteration
    
    manager.add_lesson(args.lesson, args.type, context)
    print(f"✓ Lesson added ({args.type})")
    return 0


def cmd_list(args):
    """List lessons."""
    manager = LessonManager()
    lessons = manager.list_lessons(args.type, args.limit)
    
    if args.json:
        print(json.dumps(lessons, indent=2))
        return 0
    
    if not lessons:
        print("No lessons found")
        return 0
    
    print(f"Recent Lessons (showing {len(lessons)}):")
    print("=" * 50)
    
    for lesson in lessons:
        print(f"\n[{lesson['timestamp']}] {lesson['type'].upper()}")
        print(f"  {lesson['lesson'][:100]}...")
    
    return 0


def cmd_relevant(args):
    """Get relevant lessons for context."""
    manager = LessonManager()
    
    context = {}
    if args.goal:
        context['goal'] = args.goal
    if args.strategy:
        context['strategy'] = args.strategy
    
    lessons = manager.get_relevant_lessons(context, args.limit)
    
    if not lessons:
        print("No relevant lessons found")
        return 0
    
    print(f"Relevant Lessons ({len(lessons)}):")
    print("=" * 50)
    
    for lesson in lessons:
        print(f"\n[{lesson['timestamp']}] {lesson['type'].upper()}")
        print(f"  {lesson['lesson'][:150]}...")
    
    return 0


def cmd_summarize(args):
    """Summarize all lessons."""
    manager = LessonManager()
    summary = manager.summarize()
    
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0
    
    print("Lessons Summary")
    print("=" * 50)
    print(f"Total lessons: {summary['total_lessons']}")
    
    if summary['by_type']:
        print("\nBy type:")
        for t, count in summary['by_type'].items():
            print(f"  {t}: {count}")
    
    if summary['recent']:
        print("\nRecent lessons:")
        for lesson in summary['recent']:
            print(f"  - [{lesson['type']}] {lesson['lesson'][:60]}...")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Autoresearch Lessons Manager'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # add
    add_parser = subparsers.add_parser('add', help='Add a lesson')
    add_parser.add_argument('lesson', help='Lesson text')
    add_parser.add_argument('--type', default='positive',
                          choices=['positive', 'negative', 'strategic'])
    add_parser.add_argument('--goal', help='Related goal')
    add_parser.add_argument('--strategy', help='Related strategy')
    add_parser.add_argument('--iteration', type=int, help='Iteration number')
    
    # list
    list_parser = subparsers.add_parser('list', help='List lessons')
    list_parser.add_argument('--type', help='Filter by type')
    list_parser.add_argument('--limit', type=int, default=10)
    list_parser.add_argument('--json', action='store_true')
    
    # relevant
    rel_parser = subparsers.add_parser('relevant', 
                                      help='Get relevant lessons')
    rel_parser.add_argument('--goal', help='Current goal')
    rel_parser.add_argument('--strategy', help='Current strategy')
    rel_parser.add_argument('--limit', type=int, default=5)
    
    # summarize
    sum_parser = subparsers.add_parser('summarize', help='Summarize lessons')
    sum_parser.add_argument('--json', action='store_true')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'relevant': cmd_relevant,
        'summarize': cmd_summarize
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
