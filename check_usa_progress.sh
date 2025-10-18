#!/bin/bash
echo "=== USA Triangle Centers Calculation Progress ==="
echo ""
echo "Process status:"
ps aux | grep "python3 usa_triangle" | grep -v grep || echo "Process not running"
echo ""
echo "Latest log entries:"
tail -10 output/usa_triangle_calc.log
echo ""
echo "To monitor in real-time, run: tail -f output/usa_triangle_calc.log"
