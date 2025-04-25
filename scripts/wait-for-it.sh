#!/bin/bash
# wait-for-it.sh: Wait for a service to be available
# Original source: https://github.com/vishnubob/wait-for-it

set -e

TIMEOUT=15
QUIET=0
HOST=""
PORT=""
STRICT=0
TIMEOUT_EXIT_CODE=1

usage() {
    echo "Usage: $0 host:port [-t timeout] [-q] [-- command args]"
    echo "  -t TIMEOUT  Timeout in seconds, default 15"
    echo "  -q          Quiet mode, no output"
    echo "  --          Command to execute after the service is available"
    exit 1
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -t)
                TIMEOUT="$2"
                shift 2
                ;;
            -q)
                QUIET=1
                shift
                ;;
            --)
                shift
                break
                ;;
            -*)
                echo "Unknown option: $1"
                usage
                ;;
            *)
                if [[ -z "$HOST" ]]; then
                    HOST=$(echo "$1" | cut -d : -f 1)
                    PORT=$(echo "$1" | cut -d : -f 2)
                else
                    echo "Host:port already specified"
                    usage
                fi
                shift
                ;;
        esac
    done
    COMMAND=("$@")
}

log() {
    if [[ $QUIET -eq 0 ]]; then
        echo "$@"
    fi
}

wait_for() {
    log "Waiting for $HOST:$PORT (timeout: $TIMEOUT seconds)..."
    for ((i=0; i<TIMEOUT; i++)); do
        if nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
            log "$HOST:$PORT is available"
            return 0
        fi
        sleep 1
    done
    log "Timeout waiting for $HOST:$PORT"
    return $TIMEOUT_EXIT_CODE
}

main() {
    parse_args "$@"
    if [[ -z "$HOST" || -z "$PORT" ]]; then
        echo "Error: host:port not specified"
        usage
    fi
    wait_for
    if [[ ${#COMMAND[@]} -gt 0 ]]; then
        log "Executing command: ${COMMAND[*]}"
        exec "${COMMAND[@]}"
    fi
}

main "$@"