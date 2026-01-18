"""
Performance Timing Logger
Tüm işlemlerin süresini dosyaya kaydeder
"""
import time
import json
import os
from datetime import datetime
from functools import wraps

LOG_FILE = os.path.join(os.path.dirname(__file__), '../../logs/performance.log')

# Log dizinini oluştur
log_dir = os.path.dirname(LOG_FILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)


class Timer:
    """Context manager ve decorator olarak kullanılabilir timer"""
    
    def __init__(self, operation: str, metadata: dict = None):
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None
        self.end_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration_ms = int((self.end_time - self.start_time) * 1000)
        self._log(status='error' if exc_type else 'success', 
                  error=str(exc_val) if exc_val else None)
        return False
    
    def _log(self, status='success', error=None):
        duration_sec = self.duration_ms / 1000
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': self.operation,
            'duration_ms': self.duration_ms,
            'duration_sec': round(duration_sec, 2),
            'status': status,
            **self.metadata
        }
        if error:
            log_entry['error'] = error
        
        # Console'a yaz
        print(f"⏱️ [{self.operation}] {duration_sec:.2f}s")
        
        # Dosyaya yaz
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def start_timer(operation: str, metadata: dict = None):
    """Süre ölçümü başlat"""
    return {
        'operation': operation,
        'start_time': time.time(),
        'metadata': metadata or {}
    }


def end_timer(timer: dict, extra_metadata: dict = None):
    """Süre ölçümünü bitir ve logla"""
    end_time = time.time()
    duration_ms = int((end_time - timer['start_time']) * 1000)
    duration_sec = duration_ms / 1000
    
    metadata = {**timer['metadata'], **(extra_metadata or {})}
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'operation': timer['operation'],
        'duration_ms': duration_ms,
        'duration_sec': round(duration_sec, 2),
        'status': 'success',
        **metadata
    }
    
    # Console'a yaz
    print(f"⏱️ [{timer['operation']}] {duration_sec:.2f}s")
    
    # Dosyaya yaz
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return log_entry


def timed(operation: str = None):
    """Decorator: Fonksiyonun süresini ölç"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            with Timer(op_name):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            with Timer(op_name):
                return await func(*args, **kwargs)
        
        if asyncio_available(func):
            return async_wrapper
        return wrapper
    return decorator


def asyncio_available(func):
    """Check if function is async"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


def clear_log():
    """Log dosyasını temizle"""
    with open(LOG_FILE, 'w') as f:
        f.write('')
    print('📋 Performance log temizlendi')


def get_summary():
    """Log dosyasını oku ve özet çıkar"""
    if not os.path.exists(LOG_FILE):
        return {'operations': {}}
    
    with open(LOG_FILE, 'r') as f:
        content = f.read()
    
    lines = [l for l in content.strip().split('\n') if l]
    entries = [json.loads(l) for l in lines]
    
    # İşlem bazlı gruplama
    by_operation = {}
    for entry in entries:
        op = entry['operation']
        if op not in by_operation:
            by_operation[op] = {
                'count': 0,
                'total_ms': 0,
                'min_ms': float('inf'),
                'max_ms': 0
            }
        stats = by_operation[op]
        stats['count'] += 1
        stats['total_ms'] += entry['duration_ms']
        stats['min_ms'] = min(stats['min_ms'], entry['duration_ms'])
        stats['max_ms'] = max(stats['max_ms'], entry['duration_ms'])
    
    # Ortalama hesapla
    for stats in by_operation.values():
        stats['avg_ms'] = round(stats['total_ms'] / stats['count'])
        stats['avg_sec'] = round(stats['avg_ms'] / 1000, 2)
        stats['min_sec'] = round(stats['min_ms'] / 1000, 2)
        stats['max_sec'] = round(stats['max_ms'] / 1000, 2)
    
    return {
        'total_entries': len(entries),
        'operations': by_operation
    }


def print_summary():
    """Özet tablosu yazdır"""
    summary = get_summary()
    
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if not summary['operations']:
        print("Henüz kayıt yok.")
        return
    
    # Ortalamaya göre sırala (en yavaştan en hızlıya)
    sorted_ops = sorted(
        summary['operations'].items(),
        key=lambda x: x[1]['avg_ms'],
        reverse=True
    )
    
    print(f"{'İşlem':<35} {'Ort':<10} {'Min':<10} {'Max':<10} {'Sayı':<6}")
    print("-" * 60)
    
    for op, stats in sorted_ops:
        print(f"{op:<35} {stats['avg_sec']:<10}s {stats['min_sec']:<10}s {stats['max_sec']:<10}s {stats['count']:<6}")
    
    print("=" * 60 + "\n")
