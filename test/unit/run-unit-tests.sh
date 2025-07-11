# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

#!/bin/bash
for file in test_*.py; do
    echo "Running tests in $file"
    python -m pytest "$file"
done