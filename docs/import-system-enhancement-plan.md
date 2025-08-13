# Enhanced Import System: URL Discovery & State Management

## 🎯 Overview
**STATUS: IMPLEMENTED** - This document describes the enhanced import system that has been successfully implemented with discovery_service.py, database_driven_importer.py, and pipeline_orchestrator.py. The system now features smart URL discovery, incremental processing, and state management through ImportStatus tracking.

## 🏗️ Architecture Changes

### Phase 1: Database Schema Enhancement
**New Model: `ImportUrlDiscovery`**
```python
class ImportUrlDiscovery(Base):
    __tablename__ = 'import_url_discovery'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    
    # URL Classification
    section_name = Column(String(200))      # "Registo Biografico"
    data_type = Column(String(100))         # "registo_biografico" 
    legislature = Column(String(20))        # "XVII", "XVI", etc.
    content_type = Column(String(50))       # "xml", "json", "pdf"
    
    # Discovery State
    first_discovered = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)
    discovery_status = Column(String(20), default='active')  # active, inactive, error
    
    # Content State
    current_etag = Column(String(200))      # HTTP ETag if available
    current_last_modified = Column(DateTime) # HTTP Last-Modified
    current_content_hash = Column(String(64))   # SHA1 of current content
    current_file_size = Column(Integer)
    
    # Change Detection
    content_changed = Column(Boolean, default=True)  # Needs processing
    last_content_change = Column(DateTime)
    change_detection_method = Column(String(20))  # 'etag', 'hash', 'size', 'date'
    
    # Processing Link
    current_import_status_id = Column(Integer, ForeignKey('import_status.id'))
    current_import_status = relationship("ImportStatus", back_populates="url_discovery")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Enhanced ImportStatus Model**
- Add `url_discovery` relationship back-reference
- Add `retry_count` and `retry_after` for intelligent retry logic
- Add `processing_duration` for performance tracking

### Phase 2: Unified Discovery Service
**New Script: `unified_discovery.py`**

**Core Functions:**
1. **URL Discovery**: Extract all parlament.pt resource URLs (reuse existing logic)
2. **URL Classification**: Categorize by data type, legislature, content type
3. **Change Detection**: Use HTTP headers (ETag, Last-Modified) + SHA1 comparison
4. **State Management**: Update discovery database with current state
5. **Processing Queue**: Mark changed URLs for import

**Smart Discovery Features:**
- **Incremental Discovery**: Only re-scan sections periodically (daily/weekly)
- **Parallel Discovery**: Discover URLs in parallel using ThreadPoolExecutor
- **HTTP Optimization**: Use HEAD requests where possible, respect cache headers
- **Error Handling**: Track failing URLs, exponential backoff for retries
- **URL Deduplication**: Handle URL variations (query params, fragments)

### Phase 3: Enhanced Import Orchestration
**Implemented: `database_driven_importer.py`**

**Current Processing Modes:**
1. **Discovery Mode**: `discovery_service.py --save-to-db` - Populate URL database
2. **Smart Import Mode**: `database_driven_importer.py` - Process only changed content  
3. **Force Mode**: Use `--force` flags - Ignore change detection
4. **Retry Mode**: Built-in retry logic with exponential backoff

**Processing Pipeline:**
1. Discovery service finds and catalogs URLs with metadata
2. ImportStatus tracks file states with SHA1 deduplication
3. Database-driven importer processes only discovered files
4. Smart retry logic with exponential backoff for failed imports
5. Transaction-per-file processing for data integrity
6. Pipeline orchestrator coordinates the entire workflow

### Phase 4: Performance Optimizations

**Intelligent Caching:**
- **HTTP Caching**: Respect `Cache-Control`, `ETag`, `Last-Modified` headers
- **Discovery Caching**: Cache URL discovery results for 24h
- **Content Fingerprinting**: Use HTTP HEAD requests to check changes without downloading
- **Parallel Processing**: Multi-threaded discovery and download

**Retry Logic Enhancement:**
- **Exponential Backoff**: 1s → 2s → 4s → 8s → 16s → 32s (max)
- **Jitter**: Add randomization to prevent thundering herd
- **Circuit Breaker**: Temporarily disable failing endpoints
- **Smart Retry**: Different retry strategies for different error types

**Bandwidth Optimization:**
- **Conditional Downloads**: Use `If-None-Match` and `If-Modified-Since` headers  
- **Range Requests**: Support partial downloads for large files
- **Compression**: Request gzip/deflate encoding
- **Connection Pooling**: Reuse HTTP connections

### Phase 5: Monitoring & Observability

**New Dashboard Metrics:**
- URLs discovered vs. processed vs. failed
- Discovery frequency and duration by section
- Content change rate by data type and legislature
- Processing speed improvements (before/after comparison)
- Error patterns and retry success rates

**Enhanced Logging:**
- Discovery phase: URLs found, changes detected, processing queued
- Import phase: Files processed, skipped, failed with context
- Performance metrics: Discovery time, download time, processing time
- Error tracking: URL-level failures with retry history

## 🚀 Implementation Benefits

### Efficiency Gains
- **90%+ Bandwidth Reduction**: Only download changed files
- **80%+ Time Reduction**: Skip discovery on incremental runs
- **95%+ Processing Reduction**: Only process new/changed content
- **Intelligent Scheduling**: Different refresh rates per data type

### Reliability Improvements  
- **Granular Error Tracking**: URL-level failure tracking and recovery
- **Smart Retry Logic**: Exponential backoff with success rate optimization
- **Resilient Discovery**: Continue processing even if some URLs fail
- **Audit Trail**: Complete history of URL discovery and processing

### Operational Benefits
- **Incremental Processing**: Run more frequently with lower resource usage
- **Better Monitoring**: Real-time visibility into processing state
- **Rollback Capability**: Re-process specific URLs or date ranges
- **Maintenance Mode**: Easy to pause/resume specific data types

## 📋 Implementation Plan

### Week 1: Foundation
1. Create database schema migration for `ImportUrlDiscovery`
2. Build core discovery engine with URL classification
3. Implement change detection logic (HTTP headers + SHA1)

### Week 2: Integration
1. Integrate discovery service with existing downloader logic
2. Modify unified_importer to consume discovery queue
3. Add retry logic and error handling

### Week 3: Optimization
1. Add parallel processing capabilities
2. Implement HTTP caching and bandwidth optimizations
3. Add monitoring and metrics collection

### Week 4: Testing & Rollout
1. Comprehensive testing with current parlament.pt data
2. Performance benchmarking against current system
3. Production deployment and monitoring setup

## 🎛️ Usage Examples

```bash
# Discovery (populate URL database)
python scripts/data_processing/discovery_service.py --save-to-db

# Smart import (only discovered files)
python scripts/data_processing/database_driven_importer.py

# Full pipeline orchestration
python scripts/data_processing/pipeline_orchestrator.py

# Cleanup operations
python scripts/data_processing/database_driven_importer.py --cleanup
python scripts/data_processing/database_driven_importer.py --full-cleanup

# Status monitoring
python scripts/data_processing/database_driven_importer.py --status
```

This architecture transforms your import system from reactive bulk processing to intelligent incremental updates, dramatically improving efficiency while maintaining data accuracy and providing better operational visibility.

## Current System Analysis

### Current Implementation
- `discovery_service.py`: Discovers and catalogs URLs from parlament.pt with metadata extraction
- `database_driven_importer.py`: Processes discovered files using ImportStatus queue
- `pipeline_orchestrator.py`: Coordinates discovery, download, and import phases
- `ImportStatus` model: Tracks file processing status with SHA1 deduplication and retry logic
- Enhanced mapper system: Transaction-per-file processing with data integrity validation

### Pain Points Addressed
1. **Full Discovery Every Run**: Currently re-discovers all URLs each time
2. **Bulk Downloads**: Downloads all files regardless of changes
3. **No Change Detection**: Processes files even if unchanged
4. **Limited Retry Logic**: Basic exponential backoff without intelligence
5. **Poor Observability**: Limited visibility into processing efficiency

### Migration Strategy
1. Keep existing system functional during transition
2. Add new discovery layer as optional enhancement
3. Gradually migrate processing to use discovery queue
4. Maintain backward compatibility with existing CLI flags
5. Preserve all existing data and processing logic