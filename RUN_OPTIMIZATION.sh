#!/bin/bash
# Quick script to run optimization in Docker
# Your Telegram ID is already hardcoded: 297936848

echo "🔬 Backtester Strategy Optimizer"
echo "================================"
echo ""
echo "Your Telegram ID: 297936848 (hardcoded)"
echo ""

# Default values
USER_ID="297936848"
N_TRIALS=100
CONFIG="optimization_config_no_indicators.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --with-indicators)
      CONFIG="optimization_config_with_indicators.json"
      N_TRIALS=150
      shift
      ;;
    --no-indicators)
      CONFIG="optimization_config_no_indicators.json"
      N_TRIALS=200
      shift
      ;;
    --trials)
      N_TRIALS="$2"
      shift 2
      ;;
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --help)
      echo "Usage: ./RUN_OPTIMIZATION.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --with-indicators    Use config WITH indicators (RSI, EMA)"
      echo "  --no-indicators      Use config WITHOUT indicators (default)"
      echo "  --trials N           Number of trials (default: 100)"
      echo "  --config FILE        Custom config file"
      echo "  --help               Show this help"
      echo ""
      echo "Examples:"
      echo "  ./RUN_OPTIMIZATION.sh"
      echo "  ./RUN_OPTIMIZATION.sh --with-indicators"
      echo "  ./RUN_OPTIMIZATION.sh --no-indicators --trials 200"
      echo "  ./RUN_OPTIMIZATION.sh --config my_config.json --trials 150"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo "Configuration:"
echo "  Config file: $CONFIG"
echo "  Trials: $N_TRIALS"
echo "  User ID: $USER_ID"
echo ""

# Check if config exists
if [ ! -f "$CONFIG" ]; then
    echo "❌ Error: Config file not found: $CONFIG"
    echo ""
    echo "Available configs:"
    ls -1 optimization_config_*.json 2>/dev/null || echo "  No configs found"
    exit 1
fi

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Start Docker first: docker-compose up -d"
    exit 1
fi

# Check if container exists
if ! docker ps | grep -q backtester_web; then
    echo "❌ Error: backtester_web container is not running"
    echo "Start it with: docker-compose up -d backtester-web"
    exit 1
fi

echo "🚀 Starting optimization..."
echo ""

# Run optimization
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config "$CONFIG" \
  --user-id "$USER_ID" \
  --n-trials "$N_TRIALS"

echo ""
echo "✅ Optimization command sent!"
echo "📱 Check your Telegram for progress updates"
echo "🌐 Or visit: http://localhost:8000/optimize"
