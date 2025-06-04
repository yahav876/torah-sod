#!/bin/bash
echo "🔍 Testing Torah-Sod Performance (t3.2xlarge: 8 vCPU, 32GB RAM)"
echo "=================================================="

echo "1. 📊 Checking performance configuration:"
curl -s http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/performance | jq '.performance_config | {max_workers, batch_size_multiplier, database_pool_size, redis_pool_size, torah_text_size_mb}'

echo "\n2. ⚡ Testing search speed (first time - no cache):"
echo "Searching for 'אלהים'..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "אלהים"}' | jq '{search_time, total_variants, success}'

echo "\n3. 🚀 Testing cached search (should be much faster):"
echo "Same search - should hit cache..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "אלהים"}' | jq '{search_time, total_variants, success}'

echo "\n4. 📈 Performance comparison test:"
echo "Testing complex search..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "בראשית ברא אלהים"}' | jq '{search_time, total_variants, success}'

echo "\n🎯 Expected Results with 12 Workers:"
echo "- First search: ~2-5 seconds (with 12 workers vs 4)"
echo "- Cached search: <100ms"
echo "- Complex search: ~5-15 seconds (should be 3x faster than before)"
echo "- Workers should be: 12 (optimal for 8 vCPU)"