#!/bin/bash

echo "Setting up metric files in the correct location..."

# Get the directory where this script is located (project root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Project root: $PROJECT_ROOT"

# Check if metric directories exist at project root
echo ""
echo "Checking for metric directories..."

for dir in markerEvent dagDetails eksMetrics sqsMetrics rdsMetrics; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "✓ Found $dir/"
        # List files in the directory
        files=$(ls -1 "$PROJECT_ROOT/$dir" 2>/dev/null)
        if [ -n "$files" ]; then
            echo "  Files: $files"
        else
            echo "  Warning: Directory is empty"
        fi
    else
        echo "✗ Missing $dir/"
        # Create the directory
        echo "  Creating $dir/"
        mkdir -p "$PROJECT_ROOT/$dir"
    fi
done

echo ""
echo "Expected file structure:"
echo "$PROJECT_ROOT/"
echo "├── backend/"
echo "├── frontend/"
echo "├── markerEvent/"
echo "│   └── 2025-08-01_marker_event.json"
echo "├── dagDetails/"
echo "│   └── 2025-08-01_dag_metrics.json"
echo "├── eksMetrics/"
echo "│   └── 2025-08-01_eks_metrics.json"
echo "├── sqsMetrics/"
echo "│   └── 2025-08-01_sqs_metrics.json"
echo "└── rdsMetrics/"
echo "    └── 2025-08-01_rds_metrics.json"

echo ""
echo "To test the file loading:"
echo "1. Start the backend: cd backend && source venv/bin/activate && python app.py"
echo "2. Check debug endpoint: curl http://localhost:5000/api/debug/paths"
echo ""
echo "This will show you exactly where the backend is looking for files."