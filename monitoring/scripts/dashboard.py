#!/usr/bin/env python3
"""
실시간 모니터링 대시보드
Flask 기반 웹 인터페이스
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

# 로그 디렉토리 생성
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 로깅 설정 (7일 보관, 매일 로테이션)
logger = logging.getLogger('Dashboard')
logger.setLevel(logging.INFO)

# 파일 핸들러 (일일 로테이션, 7일 보관)
file_handler = TimedRotatingFileHandler(
    f'{LOG_DIR}/dashboard.log',
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'gaji-monitor-secret-key-change-in-production')

# 로그인 페이지 템플릿
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Gaji Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .login-container {
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h1 {
            font-size: 2rem;
            color: #1f2937;
            margin-bottom: 10px;
        }
        
        .login-header p {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #374151;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn-login {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
        }
        
        .btn-login:active {
            transform: translateY(0);
        }
        
        .error-message {
            background: #fef2f2;
            border: 2px solid #fecaca;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 0.9rem;
        }
        
        .icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <div class="icon">🎮</div>
            <h1>Gaji Monitor</h1>
            <p>시스템 모니터링 대시보드</p>
        </div>
        
        {% if error %}
        <div class="error-message">
            ❌ {{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn-login">로그인</button>
        </form>
    </div>
</body>
</html>
"""

# HTML 템플릿 (기존 DASHBOARD_TEMPLATE에 로그아웃 버튼 추가)
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gaji Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            position: relative;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header .subtitle {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        .logout-btn {
            position: absolute;
            top: 0;
            right: 0;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .status-healthy {
            background: #10b981;
            color: white;
        }
        
        .status-warning {
            background: #f59e0b;
            color: white;
        }
        
        .status-error {
            background: #ef4444;
            color: white;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            transition: transform 0.2s;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1f2937;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-icon {
            font-size: 1.5rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .metric-value {
            font-weight: 600;
            font-size: 1.1rem;
            color: #1f2937;
        }
        
        .metric-value.good {
            color: #10b981;
        }
        
        .metric-value.warning {
            color: #f59e0b;
        }
        
        .metric-value.bad {
            color: #ef4444;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        .refresh-info {
            text-align: center;
            color: white;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        
        .refresh-info .time {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 1.2rem;
        }
        
        .error-message {
            background: #fef2f2;
            border: 2px solid #fecaca;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/monitor/logout" class="logout-btn">🚪 로그아웃</a>
            <h1>🎮 Gaji System Monitor</h1>
            <p class="subtitle">Real-time Infrastructure Monitoring Dashboard</p>
        </div>
        
        <div id="dashboard" class="loading pulse">
            📊 Loading metrics...
        </div>
        
        <div class="refresh-info">
            <div class="time">Last updated: <span id="lastUpdate">-</span></div>
            <div class="time">Auto-refresh every 5 seconds</div>
        </div>
    </div>
    
    <script>
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function getStatusClass(value, thresholds) {
            if (value >= thresholds.good) return 'good';
            if (value >= thresholds.warning) return 'warning';
            return 'bad';
        }
        
        function getStatusBadge(status) {
            const badges = {
                'healthy': '<span class="status-badge status-healthy">✓ Healthy</span>',
                'warning': '<span class="status-badge status-warning">⚠ Warning</span>',
                'error': '<span class="status-badge status-error">✗ Error</span>'
            };
            return badges[status] || badges['error'];
        }
        
        function renderDashboard(data) {
            const dashboard = document.getElementById('dashboard');
            
            if (!data || data.error) {
                dashboard.innerHTML = `
                    <div class="error-message">
                        ❌ Failed to load metrics: ${data?.error || 'Unknown error'}
                    </div>
                `;
                return;
            }
            
            let html = '<div class="grid">';
            
            // PostgreSQL Card
            if (data.postgresql) {
                const pg = data.postgresql;
                const cacheHitRate = parseFloat(pg.cache_hit_rate || 0);
                const connUsage = (pg.active_connections / pg.max_connections * 100).toFixed(1);
                
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <span class="card-icon">🐘</span>
                                PostgreSQL
                            </div>
                            ${getStatusBadge(pg.status)}
                        </div>
                        <div class="metric">
                            <span class="metric-label">Cache Hit Rate</span>
                            <span class="metric-value ${getStatusClass(cacheHitRate, {good: 95, warning: 85})}">${cacheHitRate.toFixed(2)}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${cacheHitRate}%"></div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Active Connections</span>
                            <span class="metric-value">${pg.active_connections} / ${pg.max_connections}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${connUsage}%"></div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Database Size</span>
                            <span class="metric-value">${formatBytes(pg.database_size)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Queries</span>
                            <span class="metric-value">${(pg.total_queries || 0).toLocaleString()}</span>
                        </div>
                    </div>
                `;
            }
            
            // Redis Card
            if (data.redis) {
                const redis = data.redis;
                const memUsage = (redis.used_memory / redis.total_system_memory * 100).toFixed(1);
                const hitRate = parseFloat(redis.hit_rate || 0);
                
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <span class="card-icon">⚡</span>
                                Redis
                            </div>
                            ${getStatusBadge(redis.status)}
                        </div>
                        <div class="metric">
                            <span class="metric-label">Hit Rate</span>
                            <span class="metric-value ${getStatusClass(hitRate, {good: 90, warning: 70})}">${hitRate.toFixed(2)}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${hitRate}%"></div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Memory Usage</span>
                            <span class="metric-value">${formatBytes(redis.used_memory)} / ${formatBytes(redis.total_system_memory)}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${memUsage}%"></div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Connected Clients</span>
                            <span class="metric-value">${redis.connected_clients}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Keys</span>
                            <span class="metric-value">${(redis.total_keys || 0).toLocaleString()}</span>
                        </div>
                    </div>
                `;
            }
            
            // Elasticsearch Card
            if (data.elasticsearch) {
                const es = data.elasticsearch;
                
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <span class="card-icon">🔎</span>
                                Elasticsearch
                            </div>
                            ${getStatusBadge(es.status)}
                        </div>
                        <div class="metric">
                            <span class="metric-label">Cluster</span>
                            <span class="metric-value">${es.cluster_status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Indices</span>
                            <span class="metric-value">${es.indices_count}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Documents</span>
                            <span class="metric-value">${(es.total_documents || 0).toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Store</span>
                            <span class="metric-value">${es.store_mb} MB</span>
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            dashboard.innerHTML = html;
            
            // Update timestamp
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('ko-KR');
        }
        
        function fetchMetrics() {
            fetch('/monitor/api/metrics')
                .then(response => response.json())
                .then(data => renderDashboard(data))
                .catch(error => {
                    console.error('Error fetching metrics:', error);
                    renderDashboard({error: error.message});
                });
        }
        
        // Initial load
        fetchMetrics();
        
        // Auto-refresh every 5 seconds
        setInterval(fetchMetrics, 5000);
    </script>
</body>
</html>
"""


class MonitorDashboard:
    """모니터링 대시보드 클래스"""
    
    def __init__(self):
        self.pg_conn = None
        self.redis_client = None
        self._connect_databases()
    
    def _connect_databases(self):
        """데이터베이스 연결"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                database=os.getenv('DB_NAME', 'gaji_db'),
                user=os.getenv('DB_USER', 'gaji_user'),
                password=os.getenv('DB_PASSWORD'),
                connect_timeout=5
            )
            logger.info("✓ PostgreSQL 연결 성공")
        except Exception as e:
            logger.error(f"✗ PostgreSQL 연결 실패: {e}")
            self.pg_conn = None
        
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info("✓ Redis 연결 성공")
        except Exception as e:
            logger.error(f"✗ Redis 연결 실패: {e}")
            self.redis_client = None
    
    def get_postgresql_metrics(self) -> Dict[str, Any]:
        """PostgreSQL 메트릭 수집"""
        if not self.pg_conn:
            return {"status": "error", "error": "Not connected"}
        
        try:
            # 트랜잭션 롤백 (이전 에러 복구)
            self.pg_conn.rollback()
            
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            # 캐시 히트율
            cursor.execute("""
                SELECT 
                    COALESCE(sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 0) as cache_hit_rate
                FROM pg_statio_user_tables
            """)
            cache_hit = cursor.fetchone()
            
            # 연결 정보
            cursor.execute("""
                SELECT 
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) as total,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_conn
                FROM pg_stat_activity
            """)
            conn_info = cursor.fetchone()
            
            # 데이터베이스 크기
            cursor.execute("""
                SELECT pg_database_size(current_database()) as size
            """)
            db_size = cursor.fetchone()
            
            # 총 쿼리 수 (pg_stat_statements가 없을 수 있음)
            try:
                cursor.execute("""
                    SELECT sum(calls) as total_queries
                    FROM pg_stat_statements
                """)
                queries = cursor.fetchone()
                total_queries = queries['total_queries'] if queries and queries['total_queries'] else 0
            except:
                total_queries = 0
            
            self.pg_conn.commit()
            
            return {
                "status": "healthy",
                "cache_hit_rate": float(cache_hit['cache_hit_rate'] or 0),
                "active_connections": conn_info['active'],
                "total_connections": conn_info['total'],
                "max_connections": conn_info['max_conn'],
                "database_size": db_size['size'],
                "total_queries": total_queries
            }
        except Exception as e:
            logger.error(f"PostgreSQL 메트릭 수집 실패: {e}")
            self.pg_conn.rollback()
            return {"status": "error", "error": str(e)}
    
    def get_redis_metrics(self) -> Dict[str, Any]:
        """Redis 메트릭 수집"""
        if not self.redis_client:
            return {"status": "error", "error": "Not connected"}
        
        try:
            info = self.redis_client.info()
            
            # 히트율 계산
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
            
            # 총 키 개수
            total_keys = sum(
                self.redis_client.dbsize() 
                for db in range(16) 
                if self.redis_client.exists(f"db{db}")
            )
            
            return {
                "status": "healthy",
                "used_memory": info['used_memory'],
                "total_system_memory": info['total_system_memory'],
                "connected_clients": info['connected_clients'],
                "total_keys": self.redis_client.dbsize(),
                "hit_rate": hit_rate,
                "uptime_seconds": info['uptime_in_seconds']
            }
        except Exception as e:
            logger.error(f"Redis 메트릭 수집 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_elasticsearch_metrics(self) -> Dict[str, Any]:
        """Elasticsearch 메트릭 수집"""
        try:
            import requests

            base_url = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200').rstrip('/')
            health_response = requests.get(f"{base_url}/_cluster/health", timeout=5)
            health_response.raise_for_status()
            health = health_response.json()
            indices_response = requests.get(f"{base_url}/_cat/indices?format=json&bytes=mb", timeout=5)
            indices = indices_response.json() if indices_response.status_code == 200 else []
            total_documents = sum(int(index.get('docs.count') or 0) for index in indices)
            store_mb = sum(float(index.get('store.size') or 0) for index in indices)

            return {
                "status": "healthy" if health.get("status") in {"green", "yellow"} else "error",
                "cluster_status": health.get("status"),
                "indices_count": len(indices) if isinstance(indices, list) else 0,
                "total_documents": total_documents,
                "store_mb": round(store_mb, 2)
            }
        except Exception as e:
            logger.error(f"Elasticsearch 메트릭 수집 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """모든 메트릭 수집"""
        return {
            "timestamp": datetime.now().isoformat(),
            "postgresql": self.get_postgresql_metrics(),
            "redis": self.get_redis_metrics(),
            "elasticsearch": self.get_elasticsearch_metrics()
        }


# Flask 라우트
dashboard = MonitorDashboard()

# 로그인 체크 데코레이터 수정
@app.before_request
def require_login():
    """로그인 필요 체크"""
    allowed_endpoints = ['login', 'static']
    if request.endpoint not in allowed_endpoints and not session.get('logged_in'):
        return redirect('/monitor/login')  # 수정됨

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        correct_username = os.getenv('MONITOR_USERNAME', 'admin')
        correct_password = os.getenv('MONITOR_PASSWORD', 'admin')
        
        if username == correct_username and password == correct_password:
            session['logged_in'] = True
            session.permanent = False
            logger.info(f"로그인 성공: {username}")
            return redirect('/monitor')  # 수정됨
        else:
            logger.warning(f"로그인 실패: {username}")
            return render_template_string(LOGIN_TEMPLATE, error="아이디 또는 비밀번호가 올바르지 않습니다.")
    
    # 이미 로그인된 경우
    if session.get('logged_in'):
        return redirect('/monitor')  # 수정됨
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """로그아웃"""
    session.pop('logged_in', None)
    logger.info("로그아웃")
    return redirect('/monitor/login')  # 수정됨

@app.route('/')
def index():
    """대시보드 메인 페이지"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/metrics')
def metrics():
    """메트릭 API 엔드포인트"""
    try:
        return jsonify(dashboard.get_all_metrics())
    except Exception as e:
        logger.error(f"메트릭 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """헬스체크 엔드포인트"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == '__main__':
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
