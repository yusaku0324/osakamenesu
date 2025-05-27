#!/usr/bin/env python3
"""
X DM Bot 監視ダッシュボード
リアルタイムで開発進捗と品質を可視化
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

def create_dashboard_app(manager=None):
    """ダッシュボードアプリケーションを作成"""
    
    app = dash.Dash(__name__)
    
    # CSSスタイル
    app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f8f9fa'}, children=[
        # ヘッダー
        html.Div(style={'backgroundColor': '#1DA1F2', 'color': 'white', 'padding': '20px'}, children=[
            html.H1('🤖 X DM Bot 自動開発ダッシュボード', style={'margin': 0}),
            html.P('AI駆動型開発の進捗をリアルタイム監視', style={'margin': '10px 0 0 0'})
        ]),
        
        # メトリクスカード
        html.Div(style={'padding': '20px'}, children=[
            html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}, children=[
                # 品質スコアカード
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    html.H3('品質スコア', style={'margin': '0 0 10px 0', 'color': '#666'}),
                    html.H1(id='quality-score', children='--', style={'margin': 0, 'color': '#28a745'}),
                    html.P('目標: 85+', style={'margin': '5px 0 0 0', 'color': '#999'})
                ]),
                
                # 完了機能数カード
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    html.H3('完了機能', style={'margin': '0 0 10px 0', 'color': '#666'}),
                    html.H1(id='completed-features', children='--', style={'margin': 0, 'color': '#007bff'}),
                    html.P('自動実装済み', style={'margin': '5px 0 0 0', 'color': '#999'})
                ]),
                
                # アクティブタスクカード
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    html.H3('実行中タスク', style={'margin': '0 0 10px 0', 'color': '#666'}),
                    html.P(id='current-task', children='--', style={'margin': 0, 'fontSize': '16px', 'fontWeight': 'bold'})
                ]),
                
                # システム状態カード
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    html.H3('システム状態', style={'margin': '0 0 10px 0', 'color': '#666'}),
                    html.Div(id='system-status', children=[
                        html.P('🟢 稼働中', style={'margin': 0, 'fontSize': '16px', 'fontWeight': 'bold', 'color': '#28a745'})
                    ])
                ])
            ]),
            
            # グラフエリア
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
                # 開発進捗グラフ
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    html.H3('開発進捗', style={'marginBottom': '20px'}),
                    dcc.Graph(id='progress-chart')
                ]),
                
                # 品質メトリクスグラフ
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    html.H3('品質メトリクス', style={'marginBottom': '20px'}),
                    dcc.Graph(id='quality-metrics-chart')
                ])
            ]),
            
            # タイムラインとログ
            html.Div(style={'marginTop': '20px', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                html.H3('開発タイムライン', style={'marginBottom': '20px'}),
                html.Div(id='timeline', style={'maxHeight': '300px', 'overflowY': 'auto'})
            ])
        ]),
        
        # 自動更新用インターバル
        dcc.Interval(
            id='interval-component',
            interval=5*1000,  # 5秒ごとに更新
            n_intervals=0
        )
    ])
    
    # コールバック：品質スコア更新
    @app.callback(Output('quality-score', 'children'),
                  Input('interval-component', 'n_intervals'))
    def update_quality_score(n):
        try:
            status_file = Path('status.json')
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status = json.load(f)
                    score = status.get('quality_score', 0)
                    return f"{score:.1f}"
        except:
            pass
        return "--"
    
    # コールバック：完了機能数更新
    @app.callback(Output('completed-features', 'children'),
                  Input('interval-component', 'n_intervals'))
    def update_completed_features(n):
        try:
            status_file = Path('status.json')
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status = json.load(f)
                    return str(len(status.get('completed_features', [])))
        except:
            pass
        return "--"
    
    # コールバック：現在のタスク更新
    @app.callback(Output('current-task', 'children'),
                  Input('interval-component', 'n_intervals'))
    def update_current_task(n):
        try:
            status_file = Path('status.json')
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status = json.load(f)
                    task = status.get('current_task')
                    if task:
                        return task.get('name', 'タスク実行中...')
        except:
            pass
        return "待機中"
    
    # コールバック：進捗グラフ更新
    @app.callback(Output('progress-chart', 'figure'),
                  Input('interval-component', 'n_intervals'))
    def update_progress_chart(n):
        features = [
            '複数アカウント管理',
            'セキュリティ強化',
            'リアルタイムダッシュボード',
            'API最適化',
            'ユーザー管理',
            '分析エンジン'
        ]
        
        try:
            completed_file = Path('completed_features.json')
            if completed_file.exists():
                with open(completed_file, 'r') as f:
                    completed = json.load(f)
            else:
                completed = []
                
            progress = [100 if f in completed else 0 for f in ['multiple_accounts_enhancement', 'advanced_security', 'real_time_dashboard', 'api_optimization', 'user_management', 'analytics_engine']]
        except:
            progress = [0] * len(features)
        
        fig = go.Figure(data=[
            go.Bar(
                x=progress,
                y=features,
                orientation='h',
                marker_color=['#28a745' if p == 100 else '#ffc107' for p in progress]
            )
        ])
        
        fig.update_layout(
            xaxis_title="完了率 (%)",
            yaxis_title="",
            showlegend=False,
            margin=dict(l=150, r=20, t=20, b=40),
            xaxis=dict(range=[0, 100])
        )
        
        return fig
    
    # コールバック：品質メトリクスグラフ更新
    @app.callback(Output('quality-metrics-chart', 'figure'),
                  Input('interval-component', 'n_intervals'))
    def update_quality_metrics(n):
        metrics = ['コードカバレッジ', 'セキュリティ', 'パフォーマンス', 'ドキュメント']
        
        try:
            report_file = Path('quality_report.md')
            if report_file.exists():
                # 実際の値を読み込む（ここではダミーデータ）
                values = [85, 95, 90, 80]
            else:
                values = [0, 0, 0, 0]
        except:
            values = [0, 0, 0, 0]
        
        fig = go.Figure(data=[
            go.Scatterpolar(
                r=values,
                theta=metrics,
                fill='toself',
                name='現在値'
            ),
            go.Scatterpolar(
                r=[85, 95, 90, 80],
                theta=metrics,
                fill='toself',
                name='目標値',
                line=dict(dash='dash')
            )
        ])
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True
        )
        
        return fig
    
    # コールバック：タイムライン更新
    @app.callback(Output('timeline', 'children'),
                  Input('interval-component', 'n_intervals'))
    def update_timeline(n):
        timeline_items = []
        
        try:
            # ログファイルから最新のイベントを読み込む
            log_file = Path('auto_dev.log')
            if log_file.exists():
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-10:]  # 最新10件
                    
                for line in reversed(lines):
                    if '開始' in line or '完了' in line or 'エラー' in line:
                        parts = line.strip().split(' - ')
                        if len(parts) >= 3:
                            time_str = parts[0]
                            message = parts[-1]
                            
                            # アイコンの選択
                            if '完了' in message:
                                icon = '✅'
                                color = '#28a745'
                            elif 'エラー' in message:
                                icon = '❌'
                                color = '#dc3545'
                            else:
                                icon = '🔧'
                                color = '#007bff'
                            
                            timeline_items.append(
                                html.Div(style={'borderLeft': f'3px solid {color}', 'paddingLeft': '20px', 'marginBottom': '15px'}, children=[
                                    html.P(f"{icon} {message}", style={'margin': '0', 'fontWeight': 'bold'}),
                                    html.P(time_str, style={'margin': '0', 'fontSize': '12px', 'color': '#666'})
                                ])
                            )
        except:
            pass
        
        if not timeline_items:
            return [html.P('イベントがありません', style={'color': '#999'})]
        
        return timeline_items
    
    return app


if __name__ == '__main__':
    app = create_dashboard_app()
    app.run(debug=True, port=9000)