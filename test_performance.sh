#!/bin/bash
echo "🔍 Testing Torah-Sod Performance (t3.2xlarge: 8 vCPU, 32GB RAM)"
echo "=================================================="

echo "1. 📊 Checking performance configuration:"
curl -s http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/performance | jq '.performance_config | {max_workers, index_ready, word_index_count, database_pool_size, redis_pool_size, torah_text_size_mb}'

echo "\n2. ⚡ Testing indexed search speed (first time):"
echo "Searching for 'אלהים' with new indexed search..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "אלהים"}' | jq '{search_time, total_variants, search_method, success}'

echo "\n3. 🚀 Testing cached search (should be instant):"
echo "Same search - should hit cache..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "אלהים"}' | jq '{search_time, total_variants, search_method, success}'

echo "\n4. 📈 Testing phrase search (2 words):"
echo "Testing 'בראשית ברא' with indexed phrase search..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "בראשית ברא"}' | jq '{search_time, total_variants, search_method, success}'

echo "\n5. 🧪 Testing longer phrase (3+ words):"
echo "Testing 'בראשית ברא אלהים את השמים'..."
time curl -s -X POST http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"phrase": "בראשית ברא אלהים את השמים"}' | jq '{search_time, total_variants, search_method, success}'

echo "\n🎯 Expected Results with Database Indexing:"
echo "- Single word: 50-200ms (vs 2-5 seconds before)"
echo "- Phrase search: 100-500ms (vs 5-15 seconds before)" 
echo "- Cached search: <50ms"
echo "- Search method: 'single_word_index', 'phrase_index', or 'text_search'"
echo "- NO MORE MEMORY KILLS! 🎉"