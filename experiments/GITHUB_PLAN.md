# Brandmint Resilience Optimization — GitHub Delivery Plan

**Generated:** 2026-04-02  
**Repository:** https://github.com/Sheshiyer/brandmint-oracle-aleph  
**Methodology:** Swarm Architect + Autoresearch

---

## Discovery Summary

**Planning Depth:** Standard (80 tasks target)  
**Delivery Mode:** Production hardening  
**CI/CD:** Production-grade (existing GitHub Actions)  
**Release Model:** Phased rollout (3 releases)  
**Quality Bar:** High (tests + validation required)  
**Team Topology:** Solo + external contributors

**Current State:**
- Baseline: 7.1/10 → Current: 8.5/10 (+1.4)
- 2 optimizations implemented but not yet integrated
- 18 experiments designed across 5 batches
- Target: 9.0+ score (90% reliability)

**Constraints:**
- Backward compatibility required
- No breaking changes to brand-config.yaml
- Maintain existing CLI interface
- Support both interactive and non-interactive modes

---

## Assumptions and Constraints

### Technical
- Python 3.10+ (existing constraint)
- All existing tests must pass
- State migration handled automatically
- Provider fallback is opt-in via config

### Release
- v4.4.1: State validation + provider fallback
- v4.4.2: NotebookLM hardening + error messages
- v4.5.0: Skill dependency checks + config validation

### Testing
- Unit tests for new modules
- Integration tests for fallback chain
- Manual testing with corrupted state files
- E2E testing with failed providers

---

## Agent Ownership Model

**Solo execution with review milestones:**
- Primary: Implementation + integration
- Review: Self-review before PR creation
- Validation: Automated tests + manual verification

**External contributors:**
- Clear issue templates with test requirements
- Integration examples provided
- Documentation updates required

---

## Phase Map

### Phase 1: Foundation Hardening (v4.4.1)
**Status:** Ready for implementation  
**Duration:** 2-3 days  
**Waves:** 3

- Wave 1.1: Provider fallback integration
- Wave 1.2: State validation integration
- Wave 1.3: Testing + documentation

### Phase 2: Publishing Robustness (v4.4.2)
**Status:** Designed, pending Phase 1  
**Duration:** 3-4 days  
**Waves:** 3

- Wave 2.1: NotebookLM retry logic
- Wave 2.2: Visual pipeline error messages
- Wave 2.3: Testing + release

### Phase 3: Pipeline Validation (v4.5.0)
**Status:** Designed, pending Phase 2  
**Duration:** 4-5 days  
**Waves:** 3

- Wave 3.1: Skill dependency pre-flight
- Wave 3.2: Config schema validation
- Wave 3.3: Wave rollback capability

---

## Phase 1 Detailed Plan

### Wave 1.1: Provider Fallback Integration

**Goal:** Integrate `ProviderFallbackChain` into visual pipeline  
**Owner:** Primary developer  
**Duration:** 1 day

#### Swarm 1.1.1: Core Integration
**Tasks:**
1. Update `pipeline/visual_backend.py` to use `ProviderFallbackChain`
2. Add fallback logging to execution reports
3. Update brand-config schema for `fallback_order`
4. Add provider attempt summary to visual asset metadata

#### Swarm 1.1.2: Configuration
**Tasks:**
5. Add fallback_order to example configs
6. Update docs/providers.md with fallback examples
7. Add migration guide to CHANGELOG
8. Create config validation for fallback_order format

**Dependencies:** None  
**Verification:**
- Manual test with FAL_KEY unset
- Check logs for fallback attempts
- Verify config validation works

---

### Wave 1.2: State Validation Integration

**Goal:** Replace all state file operations with safe validators  
**Owner:** Primary developer  
**Duration:** 1 day

#### Swarm 1.2.1: Executor Integration
**Tasks:**
9. Update `pipeline/executor.py` to use `load_state_safe`
10. Update `pipeline/executor.py` to use `save_state_safe`
11. Add repair notification to CLI output
12. Update state backup location docs

#### Swarm 1.2.2: NotebookLM Integration
**Tasks:**
13. Update `publishing/notebooklm_publisher.py` state functions
14. Add state repair logging
15. Update NotebookLM state schema documentation

#### Swarm 1.2.3: Testing
**Tasks:**
16. Create corrupted state test fixtures
17. Write unit tests for StateValidator
18. Write integration test for auto-repair
19. Test backup file creation

**Dependencies:** None  
**Verification:**
- Tests pass for corrupted state files
- Backup files created correctly
- Repaired state is valid

---

### Wave 1.3: Testing + Documentation

**Goal:** Ensure quality and document changes  
**Owner:** Primary developer  
**Duration:** 1 day

#### Swarm 1.3.1: Unit Tests
**Tasks:**
20. Test ProviderFallbackChain with mock providers
21. Test state validation schema matching
22. Test auto-repair logic
23. Test safe_save rejects invalid state
24. Test provider capability filtering

#### Swarm 1.3.2: Integration Tests
**Tasks:**
25. E2E test with failed primary provider
26. E2E test with corrupted state file
27. E2E test with full pipeline
28. Performance test (no regression)

#### Swarm 1.3.3: Documentation
**Tasks:**
29. Update README with new features
30. Add INTEGRATION_EXAMPLES to docs/
31. Update CHANGELOG.md for v4.4.1
32. Add migration guide
33. Update brand-config-schema.yaml

**Dependencies:** Swarm 1.1.*, 1.2.*  
**Verification:**
- All tests pass
- Documentation complete
- No performance regression

---

## Full Task List (Phase 1)

### Wave 1.1: Provider Fallback (8 tasks)
1. ✅ Create `brandmint/core/providers/fallback_chain.py`
2. ✅ Export `ProviderFallbackChain` from `__init__.py`
3. ⬜ Update `pipeline/visual_backend.py` to use fallback chain
4. ⬜ Add fallback attempt logging to execution reports
5. ⬜ Add `fallback_order` to brand-config schema
6. ⬜ Update example configs with fallback_order
7. ⬜ Document fallback chain in docs/providers.md
8. ⬜ Add config validation for fallback_order

### Wave 1.2: State Validation (11 tasks)
9. ✅ Create `brandmint/models/state_validator.py`
10. ✅ Implement JSON schema validation
11. ✅ Implement auto-repair logic
12. ⬜ Update `executor.py` to use `load_state_safe`
13. ⬜ Update `executor.py` to use `save_state_safe`
14. ⬜ Add repair notification to CLI
15. ⬜ Update `notebooklm_publisher.py` state functions
16. ⬜ Add state repair logging for NotebookLM
17. ⬜ Create corrupted state test fixtures
18. ⬜ Document state backup behavior
19. ⬜ Update state schema docs

### Wave 1.3: Testing + Docs (14 tasks)
20. ⬜ Write unit test: fallback chain with mocks
21. ⬜ Write unit test: state validation schemas
22. ⬜ Write unit test: auto-repair preserves data
23. ⬜ Write unit test: safe_save validation
24. ⬜ Write unit test: provider capability filter
25. ⬜ Write integration test: failed provider fallback
26. ⬜ Write integration test: corrupted state recovery
27. ⬜ Write integration test: full pipeline E2E
28. ⬜ Run performance regression tests
29. ⬜ Update README features section
30. ⬜ Add INTEGRATION_EXAMPLES to docs/
31. ⬜ Write v4.4.1 CHANGELOG entry
32. ⬜ Write migration guide
33. ⬜ Update brand-config-schema.yaml

**Total Phase 1:** 33 tasks

---

## Phase 2 Preview (NotebookLM Robustness)

### Wave 2.1: Retry Logic (12 tasks)
- Add `@with_retry` to NotebookLM API calls
- Exponential backoff: 2s → 4s → 8s
- Rate limit detection and backoff
- Test retry behavior

### Wave 2.2: Error Messages (10 tasks)
- Parse subprocess stderr for errors
- Add actionable suggestions
- Better visual pipeline error propagation
- Test error message quality

### Wave 2.3: Release (8 tasks)
- Integration testing
- Documentation updates
- v4.4.2 release prep
- Deploy to PyPI

**Total Phase 2:** ~30 tasks

---

## Phase 3 Preview (Pipeline Validation)

### Wave 3.1: Dependency Checks (15 tasks)
- Pre-flight validator for skill dependencies
- Fail fast with clear messages
- Test dependency validation

### Wave 3.2: Config Validation (12 tasks)
- JSON schema for brand-config.yaml
- Helpful error messages
- Validation CLI command

### Wave 3.3: Wave Rollback (13 tasks)
- Rollback command implementation
- State management for rollback
- Test rollback scenarios

**Total Phase 3:** ~40 tasks

---

## GitHub Issue Mapping

### Milestone 1: v4.4.1 Foundation Hardening
**Due:** 2026-04-09

#### Issue #1: Provider Fallback Chain Integration
**Labels:** enhancement, priority-high, v4.4.1  
**Assignee:** @Sheshiyer  
**Tasks:** 1-8  
**Dependencies:** None

**Description:**
Integrate the new `ProviderFallbackChain` into the visual pipeline to enable automatic retry with alternative providers when the primary fails.

**Acceptance Criteria:**
- [ ] Visual backend uses fallback chain
- [ ] Fallback attempts logged in execution reports
- [ ] Config validation for fallback_order
- [ ] Documentation updated
- [ ] Manual test: FAL_KEY unset, fallback succeeds

---

#### Issue #2: State File Validation Integration
**Labels:** enhancement, priority-high, v4.4.1  
**Assignee:** @Sheshiyer  
**Tasks:** 9-19  
**Dependencies:** None

**Description:**
Replace all state file operations with safe load/save functions that validate and auto-repair corrupted state files.

**Acceptance Criteria:**
- [ ] Executor uses load_state_safe/save_state_safe
- [ ] NotebookLM publisher updated
- [ ] Corrupted state auto-repairs with backup
- [ ] Unit tests for validation logic
- [ ] Integration test with corrupted fixture

---

#### Issue #3: Testing and Documentation
**Labels:** testing, documentation, v4.4.1  
**Assignee:** @Sheshiyer  
**Tasks:** 20-33  
**Dependencies:** #1, #2

**Description:**
Complete test coverage and documentation for v4.4.1 release.

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No performance regression
- [ ] README updated
- [ ] CHANGELOG written
- [ ] Migration guide available

---

### Milestone 2: v4.4.2 Publishing Robustness
**Due:** 2026-04-16

#### Issue #4: NotebookLM Retry Logic
**Labels:** enhancement, priority-medium, v4.4.2  
**Estimated Tasks:** 12

#### Issue #5: Visual Pipeline Error Messages
**Labels:** enhancement, priority-medium, v4.4.2  
**Estimated Tasks:** 10

#### Issue #6: v4.4.2 Release
**Labels:** release, v4.4.2  
**Estimated Tasks:** 8

---

### Milestone 3: v4.5.0 Pipeline Validation
**Due:** 2026-04-30

#### Issue #7: Skill Dependency Pre-flight
**Labels:** enhancement, priority-medium, v4.5.0  
**Estimated Tasks:** 15

#### Issue #8: Config Schema Validation
**Labels:** enhancement, priority-low, v4.5.0  
**Estimated Tasks:** 12

#### Issue #9: Wave Rollback Capability
**Labels:** enhancement, priority-low, v4.5.0  
**Estimated Tasks:** 13

---

## Verification Strategy

### Per-Wave Gates
- All tests pass
- No linting errors
- Documentation complete
- Manual verification checklist

### Per-Phase Gates
- Full E2E pipeline test
- Performance benchmarks
- Breaking change analysis
- Migration path validated

### Release Gates
- All phase gates passed
- CHANGELOG complete
- PyPI package builds
- Installation test on clean system

---

## Dispatch Strategy

### Phase 1 Execution
```bash
# Create milestone
gh milestone create "v4.4.1 Foundation Hardening" --due-date 2026-04-09

# Create issues
gh issue create --title "Provider Fallback Chain Integration" \
  --milestone "v4.4.1 Foundation Hardening" \
  --label enhancement,priority-high,v4.4.1 \
  --assignee Sheshiyer \
  --body-file .github/issue-templates/issue-1.md

gh issue create --title "State File Validation Integration" \
  --milestone "v4.4.1 Foundation Hardening" \
  --label enhancement,priority-high,v4.4.1 \
  --assignee Sheshiyer \
  --body-file .github/issue-templates/issue-2.md

gh issue create --title "Testing and Documentation" \
  --milestone "v4.4.1 Foundation Hardening" \
  --label testing,documentation,v4.4.1 \
  --assignee Sheshiyer \
  --body-file .github/issue-templates/issue-3.md
```

### Branch Strategy
```bash
# Wave-based branches
git checkout -b feature/provider-fallback-v4.4.1
git checkout -b feature/state-validation-v4.4.1
git checkout -b feature/testing-docs-v4.4.1

# Merge to release branch
git checkout -b release/v4.4.1
```

---

## Risks and Fallback Plan

### Risk 1: Breaking Changes
**Mitigation:** Extensive backward compatibility tests  
**Fallback:** Feature flags for new behavior

### Risk 2: Performance Regression
**Mitigation:** Benchmark tests before merge  
**Fallback:** Optimize validation logic

### Risk 3: State Migration Issues
**Mitigation:** Backup before repair  
**Fallback:** Manual repair tool

### Risk 4: Provider Fallback Loops
**Mitigation:** Max attempts limit  
**Fallback:** Circuit breaker pattern

---

## Success Metrics

### Quality
- Code quality score: 8.5 → 9.0+
- Test coverage: maintain 80%+
- Zero critical bugs in release

### Performance
- No regression in pipeline execution time
- State validation < 10ms overhead
- Fallback chain < 100ms overhead (when primary works)

### Adoption
- Zero breaking changes
- Migration guide usage
- Community feedback positive

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create GitHub issues** from templates
3. **Set up milestones** and labels
4. **Begin Wave 1.1** implementation
5. **Track progress** in GitHub project board

**Ready to execute?** Run the dispatch commands above to create the GitHub issues.
