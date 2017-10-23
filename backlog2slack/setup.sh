#!/bin/bash
VERSION=1.0.5
VENDOR=vendor
mkdir ${VENDOR} && cd ${VENDOR}
pip download slackweb==${VERSION} && pip wheel slackweb-${VERSION}.tar.gz && rm slackweb-${VERSION}.tar.gz
