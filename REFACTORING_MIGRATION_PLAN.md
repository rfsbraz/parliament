# Parliament Mappers Refactoring Migration Plan

## Overview
This plan addresses critical code duplication across 15+ mapper classes with a systematic 4-phase approach to minimize risk and ensure continuous functionality.

## Current State Analysis
- **11 files** with identical SQLAlchemy session initialization
- **10+ files** with identical legislature extraction logic  
- **12 files** with identical legislature creation methods
- **15 files** with similar validate_and_map patterns
- **Estimated Technical Debt**: ~2000 lines of duplicated code

## Phase 1: Foundation (Week 1)
**Goal**: Establish enhanced base classes without breaking existing code

### Tasks:
1. ✅ Create `enhanced_base_mapper.py` with consolidated functionality
2. ✅ Create `common_utilities.py` for shared utilities
3. Create comprehensive test suite for base classes
4. Add backward compatibility layer for existing mappers

### Success Criteria:
- All existing tests pass
- No changes to public API
- Enhanced base classes tested independently

## Phase 2: Pilot Migration (Week 2)
**Goal**: Migrate 2-3 simple mappers to validate approach

### Target Mappers (Low Risk):
1. `cooperacao.py` - Simple structure, well-tested
2. `peticoes.py` - Straightforward mapping logic
3. `diplomas_aprovados.py` - Minimal complexity

### Migration Process:
1. Create `{mapper}_refactored.py` alongside original
2. Run parallel testing (original vs refactored)
3. Validate identical database output
4. Switch imports once validated

### Success Criteria:
- 100% functional parity
- Reduced code size by 40-60%
- Performance improvement or neutral
- All integration tests pass

## Phase 3: Bulk Migration (Weeks 3-4)
**Goal**: Migrate remaining mappers in priority order

### High Priority (Week 3):
- `atividade_deputados.py` - Most complex, highest impact
- `iniciativas.py` - Heavy usage, critical path
- `intervencoes.py` - Performance sensitive
- `composicao_orgaos.py` - Core functionality

### Standard Priority (Week 4):
- `agenda_parlamentar.py`
- `atividades.py`
- `registo_interesses.py`
- `perguntas_requerimentos.py`
- `delegacao_permanente.py`
- `delegacao_eventual.py`
- `registo_biografico.py`

### Migration Process:
1. **Day 1-2**: Create refactored version
2. **Day 3**: Parallel testing and validation
3. **Day 4**: Integration testing
4. **Day 5**: Deploy and monitor

### Success Criteria:
- Zero regression bugs
- 50-70% code reduction across all mappers
- Improved error handling consistency
- Enhanced logging and monitoring

## Phase 4: Optimization & Cleanup (Week 5)
**Goal**: Optimize performance and clean up technical debt

### Tasks:
1. Remove all original mapper files
2. Optimize database session management
3. Implement connection pooling improvements
4. Add performance monitoring
5. Update documentation and type hints
6. Create refactoring report and metrics

### Performance Targets:
- 30% reduction in memory usage
- 20% improvement in processing speed
- 90% reduction in duplicate code
- Zero connection leaks

## Risk Management

### High Risk Scenarios:
1. **Data corruption during migration**
   - Mitigation: Comprehensive parallel testing
   - Rollback: Keep original files until Phase 4

2. **Performance regression**
   - Mitigation: Benchmark before/after each phase
   - Rollback: Feature flags for mapper selection

3. **Integration failures**
   - Mitigation: Staged deployment with monitoring
   - Rollback: Automated rollback procedures

### Testing Strategy:
1. **Unit Tests**: Test each refactored mapper independently
2. **Integration Tests**: Full pipeline testing with real data
3. **Performance Tests**: Load testing with large datasets
4. **Regression Tests**: Compare output between old/new implementations

## Monitoring & Validation

### Key Metrics:
- **Code Quality**: Lines of code, cyclomatic complexity
- **Performance**: Processing time, memory usage, database connections
- **Reliability**: Error rates, transaction success rates
- **Maintainability**: Test coverage, documentation coverage

### Validation Checkpoints:
- End of each phase: Full regression test suite
- Daily during migration: Smoke tests and basic functionality
- Post-migration: 2-week monitoring period with rollback capability

## Success Definition

### Quantitative Goals:
- ✅ Eliminate 90% of code duplication
- ✅ Reduce maintenance overhead by 60%
- ✅ Improve test coverage to 95%+
- ✅ Zero critical bugs introduced
- ✅ 20% performance improvement or neutral

### Qualitative Goals:
- ✅ Consistent error handling across all mappers
- ✅ Improved logging and debugging capabilities
- ✅ Enhanced type safety and documentation
- ✅ Easier onboarding for new developers
- ✅ Foundation for future enhancements

## Post-Migration Benefits

### Immediate:
- Reduced bug surface area
- Consistent behavior across mappers
- Improved error reporting
- Better resource management

### Long-term:
- Faster feature development
- Easier maintenance and debugging
- Better performance and scalability
- Enhanced code quality standards

## Timeline Summary
- **Week 1**: Foundation setup
- **Week 2**: Pilot migration (3 mappers)
- **Week 3**: High-priority migration (4 mappers)
- **Week 4**: Standard migration (8 mappers)
- **Week 5**: Optimization and cleanup

**Total Effort**: ~25 developer days
**Expected ROI**: 3-4x reduction in maintenance effort