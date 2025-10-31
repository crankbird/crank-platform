#!/bin/bash
# GPU Classifier Build Monitor
# Check build progress and status

echo "🎮 GPU Image Classifier Build Status"
echo "===================================="
echo

# Check if build process is running
BUILD_PID=$(ps aux | grep "docker-compose.*gpu-workers.*build" | grep -v grep | awk '{print $2}')

if [ -n "$BUILD_PID" ]; then
    echo "✅ Build process running (PID: $BUILD_PID)"
    echo "⏱️  Started: $(ps -o lstart= -p $BUILD_PID 2>/dev/null || echo 'Unknown')"
    echo
else
    echo "❌ No build process found"
    echo
fi

# Check if log file exists and show recent progress
LOG_FILE="gpu_build_v2.log"
if [ ! -f "$LOG_FILE" ]; then
    LOG_FILE="gpu_build.log"
fi

if [ -f "$LOG_FILE" ]; then
    echo "📊 Build Log Status ($LOG_FILE):"
    echo "File size: $(du -h $LOG_FILE | cut -f1)"
    echo "Last modified: $(stat -c %y $LOG_FILE)"
    echo
    
    echo "📜 Last 10 lines of build log:"
    echo "────────────────────────────────"
    tail -10 $LOG_FILE
    echo "────────────────────────────────"
    echo
    
    # Check for common progress indicators
    if grep -q "Successfully built" $LOG_FILE; then
        echo "🎉 BUILD COMPLETED SUCCESSFULLY!"
    elif grep -q "failed to solve\|ERROR\|Error" $LOG_FILE; then
        echo "❌ Build errors detected - check full log"
        echo "Last error:"
        grep -E "failed to solve|ERROR|Error" $LOG_FILE | tail -1
    else
        echo "🔄 Build in progress..."
    fi
else
    echo "❌ No build log found"
fi

echo
echo "💡 Commands:"
echo "   tail -f gpu_build.log     # Follow build progress"
echo "   ./monitor_gpu_build.sh    # Run this script again"
echo "   kill $BUILD_PID           # Stop build if needed"