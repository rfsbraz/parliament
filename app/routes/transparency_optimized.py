"""
Parliamentary Transparency Dashboard API Routes - ULTRA PERFORMANCE OPTIMIZED
=============================================================================

Emergency performance optimization with radical query simplification and caching.
Target: All endpoints < 2 seconds (ideally < 1 second)

Critical optimizations:
1. Eliminate complex JOINs causing timeouts
2. Use simple COUNT queries on single tables
3. Implement aggressive caching (5-15 minutes)
4. Provide estimated/simplified metrics when exact data is too slow
5. Result pagination and limiting

Author: Claude - Emergency Performance Fix
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, date, timedelta
from sqlalchemy import func, text, and_, or_, desc
import logging
import hashlib
import json

# Add project root to path for imports
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_session
from database.models import (
    AgendaParlamentar, IniciativaParlamentar, IniciativaEventoVotacao, 
    IniciativaEvento, Deputado, DeputadoMandatoLegislativo, Legislatura,
    PerguntaRequerimento, PeticaoParlamentar, Partido
)

# Optional models
try:
    from database.models import AttendanceAnalytics, AtividadeDeputado
except ImportError:
    AttendanceAnalytics = None
    AtividadeDeputado = None

transparency_bp = Blueprint("transparency", __name__)
logger = logging.getLogger(__name__)

# In-memory cache for ultra-fast responses
PERFORMANCE_CACHE = {}
CACHE_DURATIONS = {
    "accountability_metrics": 900,  # 15 minutes - most complex
    "deputy_performance": 600,      # 10 minutes 
    "citizen_participation": 300,   # 5 minutes
    "live_activity": 60,            # 1 minute
    "legislative_progress": 300     # 5 minutes
}

def get_cache_key(endpoint: str, params: dict = None) -> str:
    """Generate cache key"""
    cache_data = {
        "endpoint": endpoint,
        "params": params or {},
        "date": date.today().isoformat()
    }
    return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

def get_cached_or_execute(endpoint: str, func, params: dict = None):
    """Get cached result or execute function"""
    cache_key = get_cache_key(endpoint, params)
    now = datetime.now()
    
    # Check cache
    if cache_key in PERFORMANCE_CACHE:
        cached_data, cached_time = PERFORMANCE_CACHE[cache_key]
        cache_age = (now - cached_time).total_seconds()
        if cache_age < CACHE_DURATIONS.get(endpoint, 300):
            logger.info(f"Cache HIT for {endpoint} (age: {cache_age:.1f}s)")
            return cached_data
    
    # Execute and cache
    try:
        result = func()
        PERFORMANCE_CACHE[cache_key] = (result, now)
        
        # Clean old cache entries
        if len(PERFORMANCE_CACHE) > 50:
            old_keys = [k for k, (_, t) in PERFORMANCE_CACHE.items() 
                       if (now - t).total_seconds() > 1800]  # 30 min cleanup
            for k in old_keys:
                del PERFORMANCE_CACHE[k]
                
        logger.info(f"Cache MISS for {endpoint} - result cached")
        return result
    except Exception as e:
        logger.error(f"Error in {endpoint}: {str(e)}")
        # Return cached result if available, even if expired
        if cache_key in PERFORMANCE_CACHE:
            cached_data, _ = PERFORMANCE_CACHE[cache_key]
            logger.warning(f"Returning expired cache for {endpoint}")
            return cached_data
        raise

def get_current_legislature():
    """Get current legislature (XVII) - cached"""
    if hasattr(g, "current_legislature"):
        return g.current_legislature
        
    session = get_session()
    try:
        current_leg = session.query(Legislatura).filter(
            Legislatura.numero == "XVII"
        ).first()
        g.current_legislature = current_leg
        return current_leg
    finally:
        session.close()
