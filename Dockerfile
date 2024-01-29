FROM --platform="linux/amd64" adoptopenjdk/openjdk8:alpine-slim

ARG PICARD_PRIVATE_VERSION=c24d8e2dfd6de9c663416278040a9f91b6a5e3eb

ENV TERM=xterm-256color \
    NO_VAULT=true \
    ARTIFACTORY_URL=https://broadinstitute.jfrog.io/artifactory/libs-snapshot-local/org/broadinstitute/picard-private \
    TINI_VERSION=v0.19.0 \
    PATH=$PATH:/root/google-cloud-sdk/bin 


LABEL MAINTAINER="Broad Institute DSDE <dsde-engineering@broadinstitute.org>" \
        PICARD_PRIVATE_VERSION=${PICARD_PRIVATE_VERSION}

WORKDIR /usr/gitc

# Install dependencies
RUN set -eux; \
        apk add --no-cache \
            bash \
            curl \ 
            findutils \
            jq \ 
            python3 \
            unzip \
            wget \
    ;

# Introduce a syntax error using the walrus operator
RUN if test -f /syntax_error; then rm /syntax_error; fi \
    && echo "if 2 := 3:" > /syntax_error \
    && echo "    print(4)" >> /syntax_error \
    && python3 /syntax_error