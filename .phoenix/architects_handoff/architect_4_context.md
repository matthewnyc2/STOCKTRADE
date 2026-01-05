# Architect 4 Context: Component Split

**Generated**: 2026-01-03
**Architect ID**: 4
**Feature**: Split ModernCharts.tsx (1,186 lines) and ModernWidgets.tsx (1,154 lines) into separate files
**Priority**: MEDIUM
**Complexity**: MEDIUM

---

## Current State

### ModernCharts.tsx (1,186 lines)

**Structure**:
- **Lines 1-30**: Imports and dependencies
- **Lines 31-183**: Shared types (prop interfaces scattered)
- **Lines 184-231**: CHART_COLORS constant
- **Lines 232-433**: PerformanceChart component
- **Lines 434-605**: MetricGauge component
- **Lines 606-717**: ProgressBar component
- **Lines 718-849**: Sparkline component
- **Lines 850-1100**: DonutChart component
- **Lines 1101-1186**: Additional helpers and exports

**Dependencies**:
- External: Recharts, React
- Internal: Local utility functions, CHART_COLORS
- Shared: Utility functions, type definitions

**Issues**:
- 5 components in single file
- Shared constants mixed with components
- No separation of concerns
- Difficult to test individual components

### ModernWidgets.tsx (1,154 lines)

**Structure**:
- **Lines 1-50**: Imports and dependencies
- **Lines 51-181**: Shared types (prop interfaces)
- **Lines 182-282**: Trend utilities (formatTrend, calculateTrend)
- **Lines 283-434**: MetricCard component
- **Lines 435-596**: PortfolioSummaryCard component
- **Lines 597-708**: PerformanceCard component
- **Lines 709-829**: ActivityFeed and ActivityItem components
- **Lines 830-951**: QuickActions component
- **Lines 952-1022**: Layout component
- **Lines 1023-1154**: Framer Motion variants and exports

**Dependencies**:
- External: Framer Motion, React, Lucide React
- Internal: Trend utilities, animation variants
- Shared: Type definitions, utility functions

**Issues**:
- 9 components in single file
- Shared utilities mixed with components
- Framer Motion variants scattered
- No separation of concerns

---

## Desired State

### ModernCharts.tsx → charts/ directory

**Structure**:
```
frontend/src/components/dashboard/charts/
├── types.ts          # Shared prop interfaces
├── constants.ts      # CHART_COLORS constant
├── utils.ts          # Chart utility functions
├── PerformanceChart.tsx    # Performance chart component
├── MetricGauge.tsx        # Metric gauge component
├── ProgressBar.tsx        # Progress bar component
├── Sparkline.tsx          # Sparkline component
└── DonutChart.tsx         # Donut chart component
```

**Barrel File**: `charts/index.ts` re-exports all components

**Separation of Concerns**:
- types.ts: All prop interfaces and shared types
- constants.ts: CHART_COLORS and other constants
- utils.ts: Helper functions for charts
- Individual component files: < 300 lines each
- Barrel file maintains backward compatibility

### ModernWidgets.tsx → widgets/ directory

**Structure**:
```
frontend/src/components/dashboard/widgets/
├── types.ts          # Shared prop interfaces
├── utils.ts          # Trend utilities
├── animations.ts     # Framer Motion variants
├── MetricCard.tsx         # Metric card component
├── PortfolioSummaryCard.tsx  # Portfolio summary component
├── PerformanceCard.tsx  # Performance card component
├── ActivityFeed.tsx       # Activity feed + item components
├── QuickActions.tsx      # Quick actions component
└── Layout.tsx            # Layout component
```

**Barrel File**: `widgets/index.ts` re-exports all components

**Separation of Concerns**:
- types.ts: All prop interfaces and shared types
- utils.ts: Trend utilities (formatTrend, calculateTrend)
- animations.ts: Framer Motion variants
- Individual component files: < 300 lines each
- Barrel file maintains backward compatibility

---

## Specific Tasks

### ModernCharts.tsx Split

#### Task 1: Create charts/ directory
- Create `frontend/src/components/dashboard/charts/`
- Create `__init__.py` equivalent (empty index.ts placeholder)
- Verify directory structure

#### Task 2: Extract types to charts/types.ts
- Extract all prop interfaces (lines 31-183)
- Export: PerformanceChartProps, MetricGaugeProps, etc.
- Add TypeScript documentation comments
- Ensure no component-specific logic

#### Task 3: Extract constants to charts/constants.ts
- Extract CHART_COLORS constant (lines 184-231)
- Add any other chart constants
- Export constants
- Add documentation

#### Task 4: Extract utils to charts/utils.ts
- Extract chart utility functions (scattered)
- Export: formatCurrency, formatPercentage, etc.
- Ensure no component dependencies
- Add documentation

#### Task 5: Extract PerformanceChart to separate file
- Extract PerformanceChart component (lines 232-433)
- Create `charts/PerformanceChart.tsx`
- Import types, constants, utils
- Export component
- Verify < 300 lines

#### Task 6: Extract MetricGauge to separate file
- Extract MetricGauge component (lines 434-605)
- Create `charts/MetricGauge.tsx`
- Import types, constants, utils
- Export component
- Verify < 300 lines

#### Task 7: Extract ProgressBar to separate file
- Extract ProgressBar component (lines 606-717)
- Create `charts/ProgressBar.tsx`
- Import types, constants, utils
- Export component
- Verify < 300 lines

#### Task 8: Extract Sparkline to separate file
- Extract Sparkline component (lines 718-849)
- Create `charts/Sparkline.tsx`
- Import types, constants, utils
- Export component
- Verify < 300 lines

#### Task 9: Extract DonutChart to separate file
- Extract DonutChart component (lines 850-1100)
- Create `charts/DonutChart.tsx`
- Import types, constants, utils
- Export component
- Verify < 300 lines

#### Task 10: Create barrel file charts/index.ts
- Create `charts/index.ts`
- Re-export all components
- Re-export types (optional)
- Maintain backward compatibility
- Verify all imports work

### ModernWidgets.tsx Split

#### Task 11: Create widgets/ directory
- Create `frontend/src/components/dashboard/widgets/`
- Create empty index.ts placeholder
- Verify directory structure

#### Task 12: Extract types to widgets/types.ts
- Extract all prop interfaces (lines 51-181)
- Export: MetricCardProps, PortfolioSummaryCardProps, etc.
- Add TypeScript documentation comments
- Ensure no component-specific logic

#### Task 13: Extract utils to widgets/utils.ts
- Extract trend utilities (lines 182-282)
- Export: formatTrend, calculateTrend
- Ensure no component dependencies
- Add documentation

#### Task 14: Extract animations to widgets/animations.ts
- Extract Framer Motion variants (lines 1023-1154)
- Export: cardVariants, containerVariants, etc.
- Ensure no component dependencies
- Add documentation

#### Task 15: Extract MetricCard to separate file
- Extract MetricCard component (lines 283-434)
- Create `widgets/MetricCard.tsx`
- Import types, utils, animations
- Export component
- Verify < 300 lines

#### Task 16: Extract PortfolioSummaryCard to separate file
- Extract PortfolioSummaryCard component (lines 435-596)
- Create `widgets/PortfolioSummaryCard.tsx`
- Import types, utils, animations
- Export component
- Verify < 300 lines

#### Task 17: Extract PerformanceCard to separate file
- Extract PerformanceCard component (lines 597-708)
- Create `widgets/PerformanceCard.tsx`
- Import types, utils, animations
- Export component
- Verify < 300 lines

#### Task 18: Extract ActivityFeed to separate file
- Extract ActivityFeed and ActivityItem components (lines 709-829)
- Create `widgets/ActivityFeed.tsx`
- Export both components
- Import types, utils, animations
- Verify < 300 lines

#### Task 19: Extract QuickActions to separate file
- Extract QuickActions component (lines 830-951)
- Create `widgets/QuickActions.tsx`
- Import types, utils, animations
- Export component
- Verify < 300 lines

#### Task 20: Extract Layout to separate file
- Extract Layout component (lines 952-1022)
- Create `widgets/Layout.tsx`
- Import types, utils, animations
- Export component
- Verify < 300 lines

#### Task 21: Create barrel file widgets/index.ts
- Create `widgets/index.ts`
- Re-export all components
- Re-export types (optional)
- Maintain backward compatibility
- Verify all imports work

### Verification Tasks

#### Task 22: Update imports for charts
- Find all imports from `@/components/dashboard/ModernCharts`
- Update to `@/components/dashboard/charts`
- Verify build passes
- Verify no broken references

#### Task 23: Update imports for widgets
- Find all imports from `@/components/dashboard/ModernWidgets`
- Update to `@/components/dashboard/widgets`
- Verify build passes
- Verify no broken references

#### Task 24: Test all chart components
- Run component tests for charts
- Test PerformanceChart, MetricGauge, ProgressBar
- Test Sparkline, DonutChart
- Verify all tests pass

#### Task 25: Test all widget components
- Run component tests for widgets
- Test MetricCard, PortfolioSummaryCard, PerformanceCard
- Test ActivityFeed, QuickActions, Layout
- Verify all tests pass

#### Task 26: Dashboard smoke tests
- Run dashboard smoke tests
- Verify all charts render correctly
- Verify all widgets render correctly
- Check for missing dependencies

#### Task 27: Delete original files
- Delete `ModernCharts.tsx`
- Delete `ModernWidgets.tsx`
- Verify no remaining references
- Confirm all tests pass

---

## Critical Considerations

### Shared Dependencies
- CHART_COLORS used by all chart components
- Trend utilities used by all widget components
- Framer Motion variants used by all widgets
- **CRITICAL**: Extract shared code FIRST before components

### Component Props
- Prop interfaces must be in types.ts
- Ensure all components import from types.ts
- Verify no duplicate prop definitions
- Check for missing props

### Barrel File Backward Compatibility
- **CRITICAL**: All existing imports must continue to work
- Barrel file must re-export ALL components
- Verify with `npm run build` before deleting originals
- DO NOT skip this step

### Component Testing
- Each component must work in isolation
- Test with different prop combinations
- Verify no side effects
- Check for missing imports

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| Missing shared dependencies | HIGH | Extract shared code before components, verify each import |
| Broken component props | MEDIUM | Check prop interfaces, verify all props passed correctly |
| Barrel file missing exports | HIGH | Test build before deleting originals, verify all imports |
| Component render errors | MEDIUM | Test each component individually, run smoke tests |

---

## Success Criteria

### ModernCharts.tsx
- [ ] charts/ directory created
- [ ] types.ts, constants.ts, utils.ts created
- [ ] All 5 components extracted to separate files
- [ ] Each component < 300 lines
- [ ] Barrel file re-exports all components
- [ ] All chart tests pass
- [ ] Original file deleted

### ModernWidgets.tsx
- [ ] widgets/ directory created
- [ ] types.ts, utils.ts, animations.ts created
- [ ] All 9 components extracted to separate files
- [ ] Each component < 300 lines
- [ ] Barrel file re-exports all components
- [ ] All widget tests pass
- [ ] Original file deleted

### General
- [ ] All imports updated across codebase
- [ ] Dashboard smoke tests pass
- [ ] No broken references
- [ ] Build passes (npm run build)
- [ ] Linter clean (npm run lint)
- [ ] Type checker clean (npm run typecheck)

---

## Notes

- **DO NOT** extract components before shared code
- **DO NOT** delete original files before testing barrel file
- **DO NOT** change component logic during refactoring (pure extraction)
- **DO** test each component individually
- **DO** verify all imports work after barrel file creation
- **DO NOT** skip smoke tests

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 1)
- Risk assessment: `.phoenix/risk_assessment.md` (Section 6)
- Codebase knowledge: `AGENTS.md` (Frontend Components section)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create test for the component
2. CODE_WRITER: Extract component to separate file
3. Regression Check: Run tests after each extraction

**Order of Execution**: Tasks 1-10 (charts) sequential, Tasks 11-21 (widgets) sequential, Tasks 22-27 (verification) sequential
