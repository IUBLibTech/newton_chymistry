ARG TOMCAT_VERSION=9
ARG JRE_VERSION=jre11

FROM tomcat:$TOMCAT_VERSION-$JRE_VERSION AS base

RUN echo 'Downloading Packages' && \
    curl -sL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get update -qq && \
    apt-get install -y \
      build-essential \
      gettext \
      libsasl2-dev \
      netcat-openbsd \
      nodejs \
      pv \
      rsync \
      tzdata \
      python3 python3-pip python3-venv supervisor \
      zip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    echo 'Packages Downloaded'

# Set up app home
ENV APP_HOME=/app/newton_chymistry
RUN useradd -m -u 1001 -U -s /bin/bash --home-dir /app app
RUN mkdir $APP_HOME && chown -R app:app /app
WORKDIR $APP_HOME


# Web stage
FROM base AS app

# Copy application code
COPY --chown=app:app . $APP_HOME
