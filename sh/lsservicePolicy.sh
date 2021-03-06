#!/bin/bash

###
### THIS SCRIPT LISTS NODES FOR THE ORGANIZATION
###
### CONSUMES THE FOLLOWING ENVIRONMENT VARIABLES:
###
### + HZN_EXCHANGE_URL
### + HZN_ORG_ID
### + HZN_EXCHANGE_APIKEY
###

if [ -z $(command -v jq) ]; then
  echo "*** ERROR $0 $$ -- please install jq"
  exit 1
fi

if [ -z "${HZN_EXCHANGE_URL:-}" ]; then HZN_EXCHANGE_URL="http://exchange:3090/v1"; fi

if [ -z "${HZN_EXCHANGE_APIKEY:-}" ] || [ "${HZN_EXCHANGE_APIKEY:-}" == "null" ]; then
  echo "*** ERROR $0 $$ -- invalid HZN_EXCHANGE_APIKEY" &> /dev/stderr
  exit 1
fi
  
if [ -z "${HZN_ORG_ID:-}" ] || [ "${HZN_ORG_ID:-}" == "null" ]; then
  echo "*** ERROR $0 $$ -- invalid HZN_ORG_ID" &> /dev/stderr
  exit 1
fi

service=${1:-${SERVICE_LABEL:-$(jq -r '.label' service.json)}}

TEMP=$(mktemp)
CODE=$(curl -w '%{http_code}' -o ${TEMP} -sL -u "${HZN_ORG_ID}/${HZN_USER_ID:-${USER}}:${HZN_EXCHANGE_APIKEY}" "${HZN_EXCHANGE_URL%/}/orgs/${HZN_ORG_ID}/services/${service}/policy")
if [ ${CODE} != 200 ]; then
  output='{"service":"'${service}'","exchange":"'${HZN_EXCHANGE_URL}'","error":"'${CODE}'","org":"'${HZN_ORG_ID}'","policy":[]}'
else
  output=$(jq -c '{"service":"'${service}'","exchange":"'${HZN_EXCHANGE_URL}'","org":"'${HZN_ORG_ID}'","policy":.}' ${TEMP})
fi
rm -f ${TEMP}
echo "${output}"
