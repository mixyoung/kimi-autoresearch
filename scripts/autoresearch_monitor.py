#!/usr/bin/env python3
"""
Autoresearch Monitor - 实时监控和报告

提供详细的运行监控、进度报告和可视化。

Features:
1. Real-time progress tracking - 实时进度跟踪
2. Metric visualization - 指标可视化
3. Trend analysis - 趋势分析
4. HTML dashboard - Web 仪表板
5. Alert system - 告警系统
"""

import json
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

RESULTS_FILE = "autoresearch-results.tsv"
STATE_FILE = "autoresearch-state.json"
MONITOR_LOG = "autoresearch-monitor.jsonl"
DASHBOARD_FILE = "autoresearch-dashboard.html"


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self):
        self.metrics_history = []
        self.last_report_time = None
        
    def load_results(self) -> list[dict]:
        """加载结果历史"""
        results = []
        if not os.path.exists(RESULTS_FILE):
            return results
        
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    results.append({
                        'iteration': int(row.get('iteration', 0)),
                        'commit': row.get('commit', ''),
                        'metric': float(row.get('metric', 0)),
                        'delta': row.get('delta', '0'),
                        'status': row.get('status', ''),
                        'description': row.get('description', ''),
                        'timestamp': row.get('timestamp', '')
                    })
        except Exception as e:
            print(f"Error loading results: {e}")
        
        return results
    
    def load_state(self) -> dict[str, Any]:
        """加载当前状态"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def calculate_progress(self, results: list[dict]) -> dict:
        """计算进度统计"""
        if not results:
            return {
                'total_iterations': 0,
                'kept': 0,
                'discarded': 0,
                'success_rate': 0,
                'current_metric': 0,
                'baseline': 0,
                'improvement': 0,
                'improvement_pct': 0
            }
        
        total = len(results)
        kept = sum(1 for r in results if r.get('status') == 'keep')
        discarded = sum(1 for r in results if r.get('status') == 'discard')
        
        baseline = results[0]['metric'] if results else 0
        current = results[-1]['metric'] if results else 0
        
        return {
            'total_iterations': total,
            'kept': kept,
            'discarded': discarded,
            'success_rate': (kept / (kept + discarded) * 100) if (kept + discarded) > 0 else 0,
            'baseline': baseline,
            'current_metric': current,
            'improvement': current - baseline,
            'improvement_pct': ((current - baseline) / baseline * 100) if baseline != 0 else 0
        }
    
    def analyze_trends(self, results: list[dict], window: int = 10) -> dict:
        """分析趋势"""
        if len(results) < window:
            return {'error': 'Not enough data for trend analysis'}
        
        recent = results[-window:]
        metrics = [r['metric'] for r in recent]
        
        # 计算趋势
        first_half = metrics[:len(metrics)//2]
        second_half = metrics[len(metrics)//2:]
        
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        
        trend = 'improving' if avg_second < avg_first else 'worsening' if avg_second > avg_first else 'stable'
        
        return {
            'window': window,
            'trend': trend,
            'avg_first_half': avg_first,
            'avg_second_half': avg_second,
            'improvement_rate': (avg_first - avg_second) / window,
            'recent_kept': sum(1 for r in recent if r['status'] == 'keep'),
            'recent_discarded': sum(1 for r in recent if r['status'] == 'discard')
        }
    
    def generate_text_report(self) -> str:
        """生成文本报告"""
        results = self.load_results()
        state = self.load_state()
        progress = self.calculate_progress(results)
        trends = self.analyze_trends(results) if len(results) >= 10 else {}
        
        lines = []
        lines.append("=" * 70)
        lines.append("  Autoresearch Progress Report")
        lines.append("=" * 70)
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 进度概览
        lines.append("\n📊 Progress Overview")
        lines.append("-" * 40)
        lines.append(f"Total iterations: {progress['total_iterations']}")
        lines.append(f"Kept: {progress['kept']} | Discarded: {progress['discarded']}")
        lines.append(f"Success rate: {progress['success_rate']:.1f}%")
        
        # 指标
        lines.append("\n📈 Metrics")
        lines.append("-" * 40)
        lines.append(f"Baseline: {progress['baseline']:.2f}")
        lines.append(f"Current: {progress['current_metric']:.2f}")
        lines.append(f"Improvement: {progress['improvement']:+.2f} ({progress['improvement_pct']:+.1f}%)")
        
        # 趋势
        if trends:
            lines.append("\n📉 Trends (last 10 iterations)")
            lines.append("-" * 40)
            lines.append(f"Trend: {trends.get('trend', 'N/A')}")
            lines.append(f"Recent kept/discarded: {trends.get('recent_kept', 0)}/{trends.get('recent_discarded', 0)}")
        
        # 最近迭代
        if results:
            lines.append("\n🔄 Recent Iterations")
            lines.append("-" * 40)
            for r in results[-5:]:
                status_emoji = "✅" if r['status'] == 'keep' else "❌" if r['status'] == 'discard' else "📊"
                lines.append(f"{status_emoji} #{r['iteration']}: {r['metric']:.2f} ({r['delta']}) - {r['status']}")
                if r['description']:
                    lines.append(f"   {r['description'][:50]}...")
        
        # 配置
        config = state.get('config', {})
        if config:
            lines.append("\n⚙️ Configuration")
            lines.append("-" * 40)
            lines.append(f"Goal: {config.get('goal', 'N/A')}")
            lines.append(f"Direction: {config.get('direction', 'N/A')}")
            lines.append(f"Target: {config.get('target', 'N/A')}")
        
        lines.append("\n" + "=" * 70)
        
        return '\n'.join(lines)
    
    def generate_html_dashboard(self) -> str:
        """生成 HTML 仪表板"""
        results = self.load_results()
        progress = self.calculate_progress(results)
        
        # 生成图表数据
        iterations = [r['iteration'] for r in results]
        metrics = [r['metric'] for r in results]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Autoresearch Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .status-good {{ color: #10b981; }}
        .status-bad {{ color: #ef4444; }}
        .status-neutral {{ color: #6b7280; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Autoresearch Dashboard</h1>
        <p>Real-time progress monitoring</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{progress['total_iterations']}</div>
            <div class="stat-label">Iterations</div>
        </div>
        <div class="stat-card">
            <div class="stat-value status-good">{progress['kept']}</div>
            <div class="stat-label">Kept</div>
        </div>
        <div class="stat-card">
            <div class="stat-value status-bad">{progress['discarded']}</div>
            <div class="stat-label">Discarded</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{progress['success_rate']:.1f}%</div>
            <div class="stat-label">Success Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{progress['current_metric']:.2f}</div>
            <div class="stat-label">Current Metric</div>
        </div>
        <div class="stat-card">
            <div class="stat-value {'status-good' if progress['improvement'] < 0 else 'status-bad' if progress['improvement'] > 0 else 'status-neutral'}">{progress['improvement']:+.2f}</div>
            <div class="stat-label">Improvement</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>Metric Trend</h2>
        <canvas id="trendChart" height="100"></canvas>
    </div>
    
    <script>
        const ctx = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {iterations},
                datasets: [{{
                    label: 'Metric',
                    data: {metrics},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: false
                    }}
                }}
            }}
        }});
    </script>
    
    <div style="text-align: center; color: #666; margin-top: 20px;">
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><a href="autoresearch-results.tsv" download>Download Results (TSV)</a></p>
    </div>
</body>
</html>"""
        
        return html
    
    def save_dashboard(self) -> str:
        """保存仪表板"""
        html = self.generate_html_dashboard()
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        return DASHBOARD_FILE
    
    def log_monitor_event(self, event_type: str, data: dict) -> None:
        """记录监控事件"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        
        with open(MONITOR_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')


def main():
    """CLI for monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autoresearch Monitor')
    subparsers = parser.add_subparsers(dest='command')
    
    # report
    subparsers.add_parser('report', help='Generate text report')
    
    # dashboard
    dashboard_parser = subparsers.add_parser('dashboard', help='Generate HTML dashboard')
    dashboard_parser.add_argument('--open', action='store_true', help='Open in browser')
    
    # watch
    watch_parser = subparsers.add_parser('watch', help='Watch for changes')
    watch_parser.add_argument('--interval', type=int, default=5, help='Check interval (seconds)')
    
    args = parser.parse_args()
    
    tracker = ProgressTracker()
    
    if args.command == 'report':
        print(tracker.generate_text_report())
    
    elif args.command == 'dashboard':
        filepath = tracker.save_dashboard()
        print(f"Dashboard saved to: {filepath}")
        if args.open:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
    
    elif args.command == 'watch':
        import time
        print(f"Watching for changes every {args.interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        last_modified = 0
        try:
            while True:
                if os.path.exists(RESULTS_FILE):
                    mtime = os.path.getmtime(RESULTS_FILE)
                    if mtime != last_modified:
                        last_modified = mtime
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(tracker.generate_text_report())
                time.sleep(args.interval)
        except KeyboardInterrupt:  # pragma: no cover (user interrupt)
            print("\nStopped watching")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
