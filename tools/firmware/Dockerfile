# Every tool fw.py needs, for Linux, Windows (Docker Desktop / WSL) or a Mac without Homebrew.
#   docker build -t headunits-fw tools/firmware
#   docker run --rm --user "$(id -u):$(id -g)" -v ~/Dev/firmwares:/fw -e FW_WORK=/fw/_work headunits-fw extract "/fw/zxw gt7/20250718GT_KSW.zip"
# --user matters: as root, debugfs hands files Android's uids and the host user can't read or delete them.
FROM eclipse-temurin:21-jre-noble

ARG PAYLOAD_DUMPER_VERSION=2.1.0
ARG JADX_VERSION=1.5.6
ARG JADX_SHA256=545ea2be9c242511bc145755cf4bda2485ade42966e096f8b4d3da2a230e8974
ARG TARGETARCH

RUN apt-get update \
  && apt-get install -y --no-install-recommends e2fsprogs erofs-utils git curl unzip ca-certificates python3 \
  && rm -rf /var/lib/apt/lists/*

RUN case "$TARGETARCH" in \
      amd64) sum=bbbb53a71955c69272afdef7bc7e83a1bb1770f453d0c21dcaf61a3ba0463c11 ;; \
      arm64) sum=5743a39b48d0c4dab948ad6e5d9ff275e649528e5dfd2b7db4b6893093b70f6c ;; \
      *) echo "unsupported arch $TARGETARCH" && exit 1 ;; \
    esac \
  && curl -fsSL -o /tmp/pd.tgz "https://github.com/ssut/payload-dumper-go/releases/download/${PAYLOAD_DUMPER_VERSION}/payload-dumper-go_${PAYLOAD_DUMPER_VERSION}_linux_${TARGETARCH}.tar.gz" \
  && echo "$sum  /tmp/pd.tgz" | sha256sum -c - \
  && tar -xzf /tmp/pd.tgz -C /usr/local/bin payload-dumper-go \
  && rm /tmp/pd.tgz

RUN curl -fsSL -o /tmp/jadx.zip "https://github.com/skylot/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip" \
  && echo "$JADX_SHA256  /tmp/jadx.zip" | sha256sum -c - \
  && unzip -q /tmp/jadx.zip -d /opt/jadx \
  && ln -s /opt/jadx/bin/jadx /usr/local/bin/jadx \
  && rm /tmp/jadx.zip

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv
ENV UV_CACHE_DIR=/opt/uv-cache HOME=/tmp
COPY fw.py /opt/fw/fw.py
# Resolve the script's pinned Python deps at build time, not on every run.
RUN uv run --script /opt/fw/fw.py --help > /dev/null && chmod -R a+rwX /opt/uv-cache

ENTRYPOINT ["uv", "run", "--script", "/opt/fw/fw.py"]
