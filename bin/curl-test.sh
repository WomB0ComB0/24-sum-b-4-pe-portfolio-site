#!/bin/bash

TOKEN=""
METHOD="GET"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -t|--token) TOKEN="$2"; shift ;;
        -m|--method) METHOD="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$TOKEN" ]; then
    echo "Error: Token is required. Use -t or --token to provide the token."
    exit 1
fi

curl -X "$METHOD" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"name": "wecracked-2024", "description": "WeCracked NextJs hackathon 2024", "url": "https://github.com/WomB0ComB0/wecracked-2024", "language": "TypeScript"}' http://localhost:5000/api/v1/projects