# API Contract Quick Reference

**Architect**: API Contract Architect (Architect 5)
**Status**: ✅ COMPLETE

## What Was Done

Established a type-safe contract between frontend and backend using OpenAPI specification and automated TypeScript type generation.

## Key Files

| File | Purpose |
|------|---------|
| `frontend/openapi.json` | OpenAPI 3.0 specification (source of truth) |
| `frontend/src/api/generated/schema.d.ts` | Auto-generated TypeScript types |
| `frontend/src/api/generated/client.ts` | Type-safe API client |
| `frontend/src/__tests__/contract/api-contract.test.ts` | Contract validation tests |
| `.github/workflows/contract-test.yml` | CI/CD contract validation |
| `frontend/docs/API_CONTRACT_SETUP.md` | Full documentation |

## Quick Start

### 1. Generate Types
```bash
cd frontend
npm run generate:api
```

### 2. Use in Components
```typescript
import apiClient from '@/api/generated'

// Fully typed!
const strategies = await apiClient.listStrategies()
const strategy = await apiClient.getStrategy({ strategy_id: '123' })
```

### 3. Run Tests
```bash
npm run test:contract
```

## Architecture

```
Pydantic Models → FastAPI → OpenAPI Spec → TypeScript Types → Frontend
```

## Benefits

- ✅ **Type Safety**: Full autocomplete and type checking
- ✅ **Single Source of Truth**: Backend drives frontend types
- ✅ **Automated**: One command regenerates all types
- ✅ **Validated**: Contract tests prevent breaking changes

## Workflow

### Backend Changes
1. Update Pydantic models
2. Export OpenAPI: `curl http://localhost:8000/openapi.json > frontend/openapi.json`

### Frontend Updates
1. Regenerate: `npm run generate:api`
2. Use new types

### Automated
- CI/CD validates contract on every push
- Pre-build hooks regenerate types

## Dependencies

- `openapi-typescript@^7.10.1` - Type generation
- `orval@^7.17.2` - Alternative generator

## Documentation

See `frontend/docs/API_CONTRACT_SETUP.md` for complete guide.

## Status

✅ **ALL DELIVERABLES COMPLETE**

- OpenAPI 3.0 specification
- TypeScript type generation
- Type-safe API client
- Contract testing
- CI/CD integration
- Developer documentation

## Next Steps

1. Backend API Architect: Complete OpenAPI spec with all endpoints
2. Frontend Design Architect: Integrate generated types
3. All: Review documentation and adopt workflow

---

**For detailed information, see:**
- Completion Report: `.phoenix/architects_reports/architect_5_completion_report.md`
- Full Documentation: `frontend/docs/API_CONTRACT_SETUP.md`
