#!/usr/bin/with-contenv bashio

###
### HZN TOOLS
###

# hzn::pattern() - find the pattern with the given name; searches HZN_ORGANIZATION only
hzn::pattern()
{
  bashio::log.trace "${FUNCNAME[0]} ${*}"

  local pattern=${1:-}
  local json

  if [ ! -z "${pattern}" ] && [ ! -z "${HZN_ORGANIZATION:-}" ] && [ ! -z "${HZN_EXCHANGE_APIKEY:-}" ] && [ ! -z "${HZN_EXCHANGE_URL:-}" ]; then
    local ALL=$(curl -sL -u "${HZN_ORGANIZATION}/${HZN_USER_ID:-iamapikey}:${HZN_EXCHANGE_APIKEY}" "${HZN_EXCHANGE_URL}orgs/${HZN_ORGANIZATION}/patterns")

    if [ ! -z "${ALL}" ]; then
      bashio::log.trace "searching for pattern ${pattern} in all patterns ${ALL}"
      json=$(echo "${ALL}" | jq '.patterns|to_entries[]|select(.key=="'${pattern}'")')
    fi
  fi
  if [ ! -z "${pattern}" ]; then 
    if [ -z "${json:-}" ]; then 
      bashio::log.warning "pattern was not found: ${pattern}"
    fi
  else
    bashio::log.warning "pattern not specified"
  fi
  echo ${json:-null}
}

# initialize horizon
hzn::init()
{
  bashio::log.trace "${FUNCNAME[0]}"

  local config='{"timestamp":"'$(date -u +%FT%TZ)'","date":'$(date +%s)',"hzn":{"agreementid":"'${HZN_AGREEMENTID:-}'","arch":"'${HZN_ARCH:-}'","cpus":'${HZN_CPUS:-0}',"device_id":"'${HZN_DEVICE_ID:-}'","exchange_url":"'${HZN_EXCHANGE_URL:-}'","host_ips":['$(echo "${HZN_HOST_IPS:-}" | sed 's/,/","/g' | sed 's/\(.*\)/"\1"/')'],"organization":"'${HZN_ORGANIZATION:-}'","ram":'${HZN_RAM:-0}',"pattern":'$(hzn::pattern "${HZN_PATTERN:-}")'}}'
  local file=$(hzn::config.file)

  bashio::log.debug "${FUNCNAME[0]}: writing horizon configuration; file: ${file}; config: ${config}"

  echo "${config}" > ${file} && cat ${file} || echo 'null'
}

# get horizon configuration
hzn::config()
{
  bashio::log.trace "${FUNCNAME[0]}"

  local config
  local file=$(hzn::config.file)

  if [ -s ${file} ]; then
    config=$(jq -c '.' ${file})
    if [ "${config:-null}" = 'null' ]; then
      bashio::log.error "${FUNCNAME[@]}: invalid configuration: ${config:-}; file: ${file}"
    else
      bashio::log.debug "${FUNCNAME[0]}: valid configuration: ${config:-}; file: ${file}"
    fi
  else
    bashio::log.error "${FUNCNAME[@]}: zero-length configuration file: ${file}"
  fi
  echo "${config:-null}"
}

hzn::config.file()
{
  bashio::log.trace "${FUNCNAME[0]} ${*}"

  echo "/var/run/horizon.json"
}

function hzn::log.level()
{
  bashio::log.trace "${FUNCNAME[0]} ${*}"

  local log_level=$(bashio::string.lower "${1:-}")
  local level=${__BASHIO_LOG_LEVEL:-0}

  if [ ! -z "${log_level:-}" ]; then
    # Find the matching log level
    case "${log_level}" in
      all|trace|debug|info|notice|warning|error|fatal|critical|off)
        bashio::log.level "${log_level}"
        log_level="${__BASHIO_LOG_LEVELS[${__BASHIO_LOG_LEVEL:-0}]}"
        bashio::log.debug "${FUNCNAME[0]}: updated log level; level: ${log_level:-null}"
        ;;
      *)
        bashio::log.fatal "Unknown log_level: ${log_level}"
        log_level=""
        ;;
    esac
  else
    log_level="${__BASHIO_LOG_LEVELS[${__BASHIO_LOG_LEVEL:-0}]}"
    bashio::log.debug "${FUNCNAME[0]}: reporting log level; level: ${log_level}"
  fi
  echo "${log_level}"
}
