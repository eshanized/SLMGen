#!/bin/bash
echo "Testing Backend Connection..."
curl -v http://localhost:8000/health
echo "Testing /upload route..."
curl -v -X POST http://localhost:8000/upload
