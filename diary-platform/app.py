#!/usr/bin/env python3
"""
日記プラットフォーム - メインアプリケーション
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# データベースモデル
class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image_path = db.Column(db.String(300))
    
    def __repr__(self):
        return f'<DiaryEntry {self.title}>'

# ルート
@app.route('/')
def index():
    """トップページ - 日記一覧"""
    entries = DiaryEntry.query.order_by(DiaryEntry.created_at.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    """新規日記作成"""
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', '未分類')
        
        entry = DiaryEntry(
            title=title,
            content=content,
            category=category
        )
        
        db.session.add(entry)
        db.session.commit()
        
        flash('日記を投稿しました！', 'success')
        return redirect(url_for('index'))
    
    return render_template('new.html')

@app.route('/entry/<int:id>')
def view_entry(id):
    """日記詳細表示"""
    entry = DiaryEntry.query.get_or_404(id)
    return render_template('view.html', entry=entry)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    """日記編集"""
    entry = DiaryEntry.query.get_or_404(id)
    
    if request.method == 'POST':
        entry.title = request.form['title']
        entry.content = request.form['content']
        entry.category = request.form.get('category', '未分類')
        entry.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('日記を更新しました！', 'success')
        return redirect(url_for('view_entry', id=entry.id))
    
    return render_template('edit.html', entry=entry)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    """日記削除"""
    entry = DiaryEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('日記を削除しました', 'info')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    """日記検索"""
    query = request.args.get('q', '')
    if query:
        entries = DiaryEntry.query.filter(
            DiaryEntry.title.contains(query) | 
            DiaryEntry.content.contains(query)
        ).order_by(DiaryEntry.created_at.desc()).all()
    else:
        entries = []
    
    return render_template('search.html', entries=entries, query=query)

# アプリケーション初期化
def init_db():
    """データベース初期化"""
    with app.app_context():
        db.create_all()
        # アップロードフォルダ作成
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)