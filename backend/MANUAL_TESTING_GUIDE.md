# Manual API Testing Guide for DBurst Redis Integration

## Prerequisites

1. **Start Redis:**
   ```bash
   redis-server
   # Or if using Docker:
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Start Django Backend:**
   ```bash
   cd /home/mrlionbyte/Project/DBurst/backend
   source .venv_dburst/bin/activate
   python manage.py runserver
   ```

3. **Get Authentication Token:**
   - Login via frontend or use Django admin
   - Copy your JWT access token

---

## Test Scenarios

### Scenario 1: Complete Generation → Patch Flow

#### Step 1: Generate UI (Initial Creation)
```bash
curl -X POST http://localhost:8000/api/v1/generation/generate/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a modern landing page for a coffee shop with hero section, menu, and contact form",
    "llm_provider": "groq"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "project_id": "uuid-here",
  "generation_id": "uuid-here",
  "schema": {...},
  "code": "...",
  "meta": {...}
}
```

**Save the `generation_id` for next steps!**

#### Step 2: Verify Redis Caching
```bash
# Check if schema is cached
redis-cli GET "gen:YOUR_GENERATION_ID:schema"

# Check if code is cached
redis-cli GET "gen:YOUR_GENERATION_ID:code"

# List all generation keys
redis-cli KEYS "gen:*"
```

**Expected:** You should see JSON data for schema and code

---

### Scenario 2: Apply Patches (No LLM Calls!)

#### Patch 1: Change Background Color
```bash
curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patch": [
      {
        "op": "replace",
        "path": "/props/className",
        "value": "min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50"
      }
    ],
    "description": "Changed to warm gradient background"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "generation_id": "uuid",
  "schema": {...},  // Updated schema
  "patch_id": "uuid",
  "patch_count": 1,
  "snapshot_created": false
}
```

**⚡ Notice:** Response should be instant (<100ms) - NO LLM call!

#### Patch 2: Add New Component
```bash
curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patch": [
      {
        "op": "add",
        "path": "/children/-",
        "value": {
          "type": "Section",
          "props": {"className": "py-12"},
          "children": [
            {"type": "Text", "content": "New Section Added"}
          ]
        }
      }
    ],
    "description": "Added new section at the end"
  }'
```

#### Patch 3: Modify Text Content
```bash
curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patch": [
      {
        "op": "replace",
        "path": "/children/0/children/0/content",
        "value": "Welcome to Artisan Coffee House"
      }
    ],
    "description": "Updated hero text"
  }'
```

#### Verify Patches in Redis
```bash
# Check patch count
redis-cli LLEN "gen:YOUR_GENERATION_ID:patches"

# View all patches
redis-cli LRANGE "gen:YOUR_GENERATION_ID:patches" 0 -1
```

---

### Scenario 3: Retrieve Current Schema

```bash
curl -X GET http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/schema/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "generation_id": "uuid",
  "schema": {...},  // Schema with all patches applied
  "code": "...",    // Regenerated React code
  "patch_count": 3,
  "cached": true
}
```

---

### Scenario 4: List Patch History

```bash
# Get all patches
curl -X GET http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patches/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get patches with pagination
curl -X GET "http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patches/?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "generation_id": "uuid",
  "total_patches": 3,
  "limit": 20,
  "offset": 0,
  "patches": [
    {
      "id": "uuid",
      "generation_id": "uuid",
      "user_email": "your@email.com",
      "patch_data": [...],
      "description": "Updated hero text",
      "applied_at": "2026-01-05T19:30:00Z",
      "snapshot_created": false
    },
    // ... more patches (newest first)
  ]
}
```

---

### Scenario 5: Test Snapshot Creation (10 Patches)

```bash
# Apply 10 patches in a loop
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"patch\": [{\"op\": \"replace\", \"path\": \"/props/className\", \"value\": \"p-$i\"}],
      \"description\": \"Patch number $i\"
    }"
  echo ""
  sleep 0.5
done
```

**Expected:** 10th patch response should have `"snapshot_created": true`

**Verify in Database:**
```bash
# Connect to Django shell
python manage.py shell

# Check snapshot
from patching.models import Patch
from generation.models import Generations

gen_id = "YOUR_GENERATION_ID"
snapshot_patches = Patch.objects.filter(
    generation_id=gen_id,
    snapshot_created=True
)
print(f"Snapshot patches: {snapshot_patches.count()}")

# Check if generation schema was updated
gen = Generations.objects.get(id=gen_id)
print(f"Schema in DB: {gen.schema}")
```

---

### Scenario 6: Clear Cache

```bash
curl -X DELETE http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/cache/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Cache cleared for generation YOUR_GENERATION_ID"
}
```

**Verify Cache Cleared:**
```bash
redis-cli GET "gen:YOUR_GENERATION_ID:schema"
# Should return (nil)
```

**Schema Still Retrievable from Database:**
```bash
curl -X GET http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/schema/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected:** `"cached": false` (loaded from database)

---

### Scenario 7: Error Handling Tests

#### Test 1: Unauthorized Access
```bash
curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Content-Type: application/json" \
  -d '{
    "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}]
  }'
```

**Expected:** `401 Unauthorized`

#### Test 2: Invalid Patch Format
```bash
curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patch": "not-a-list"
  }'
```

**Expected:** `400 Bad Request` with validation error

#### Test 3: Invalid Operation
```bash
curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patch": [{"op": "invalid_op", "path": "/props/className", "value": "p-10"}]
  }'
```

**Expected:** `400 Bad Request` - Invalid operation type

#### Test 4: Non-existent Generation
```bash
curl -X GET http://localhost:8000/api/v1/patching/00000000-0000-0000-0000-000000000000/schema/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected:** `404 Not Found`

---

## Performance Testing

### Test 1: Measure Patch Application Speed

```bash
# Time a patch application
time curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}],
    "description": "Speed test"
  }'
```

**Expected:** <100ms response time

### Test 2: Redis Memory Usage

```bash
redis-cli INFO memory
```

**Check:**
- `used_memory_human` - Should be reasonable (<100MB for test data)
- `used_memory_peak_human` - Peak memory usage

### Test 3: Concurrent Patches

```bash
# Apply 5 patches concurrently
for i in {1..5}; do
  (curl -X POST http://localhost:8000/api/v1/patching/YOUR_GENERATION_ID/patch/ \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"patch\": [{\"op\": \"replace\", \"path\": \"/props/className\", \"value\": \"concurrent-$i\"}],
      \"description\": \"Concurrent patch $i\"
    }" &)
done
wait
```

**Expected:** All patches should succeed

---

## Monitoring & Debugging

### Check Redis Connection
```bash
redis-cli ping
# Expected: PONG
```

### Monitor Redis Commands
```bash
redis-cli MONITOR
# Shows all Redis commands in real-time
```

### Check Django Logs
```bash
# In another terminal
tail -f /tmp/django-debug.log
# Or check console output from runserver
```

### Database Queries
```bash
# Django shell
python manage.py shell

from patching.models import Patch
from generation.models import Generations

# Count total patches
print(f"Total patches: {Patch.objects.count()}")

# Recent patches
recent = Patch.objects.order_by('-applied_at')[:5]
for p in recent:
    print(f"{p.applied_at}: {p.description}")
```

---

## Success Criteria

✅ **All scenarios should pass with:**
- Correct HTTP status codes
- Expected JSON responses
- Data persisted in Redis and Database
- Fast response times (<100ms for patches)
- Proper error handling
- Snapshot creation at 10th patch

---

## Troubleshooting

### Issue: "Redis connection failed"
**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server
```

### Issue: "401 Unauthorized"
**Solution:**
- Verify JWT token is valid
- Check token hasn't expired
- Ensure `Authorization: Bearer TOKEN` header is set

### Issue: "Schema not found in cache"
**Solution:**
- Generation might not be cached yet
- Run a generation first or manually cache it
- Check Redis keys: `redis-cli KEYS "gen:*"`

### Issue: "Patch application failed"
**Solution:**
- Verify patch format (must be array of operations)
- Check path exists in schema
- Ensure operation type is valid (add/remove/replace/move/copy/test)

---

## Quick Reference

### Common Patch Operations

**Replace:**
```json
{"op": "replace", "path": "/props/className", "value": "new-value"}
```

**Add:**
```json
{"op": "add", "path": "/children/-", "value": {"type": "Text", "content": "New"}}
```

**Remove:**
```json
{"op": "remove", "path": "/children/0"}
```

**Move:**
```json
{"op": "move", "from": "/children/0", "path": "/children/1"}
```

**Copy:**
```json
{"op": "copy", "from": "/children/0", "path": "/children/-"}
```

---

## Next Steps

After manual testing:
1. Run automated tests: `pytest patching/tests/ -v`
2. Check test coverage: `pytest --cov=patching`
3. Review logs for any warnings
4. Monitor Redis memory usage over time
5. Test with frontend integration
