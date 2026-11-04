# Image du serveur de détourage vidéo de Nexora Creative (SAM 2.1 + ViTMatte), poids HORS de l'image (volume /modeles).
#
#   RTX 5080 / 5090 / GB10 (sm_120, sm_121) : TORCH_INDEX=https://download.pytorch.org/whl/cu130 (défaut)
#   Tesla V100 (Volta, sm_70 ; pas de bf16, le code passe en fp16) : TORCH_INDEX=https://download.pytorch.org/whl/cu126
#     (les roues cu128 et cu130 n'incluent plus sm_70 ; pilote ≥ 560 requis pour CUDA 12.6)
#
# Construction (contexte = outils/detourage) : docker build -t <registre>/nexora/detourage:<version>-cu130 outils/detourage
# ou le Job kaniko deploy/k8s/detourage/20-construction-kaniko.yaml (sans démon ni root sur l'hôte).
ARG PYTHON_IMAGE=docker.io/library/python:3.12-slim-trixie@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30
FROM ${PYTHON_IMAGE}
ARG TORCH_INDEX=https://download.pytorch.org/whl/cu130
ARG TORCH_VERSION=2.14.1
ARG TORCHVISION_VERSION=0.29.1

# ffmpeg de Debian : prores_ks, libvpx-vp9, libx264, exr (vérifié au démarrage par /sante via les sorties)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/detourage/requirements.txt
RUN pip install --no-cache-dir "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" --index-url "${TORCH_INDEX}" \
 && pip install --no-cache-dir -r /opt/detourage/requirements.txt

COPY *.py /opt/detourage/
COPY verite/ /opt/detourage/verite/
RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin detourage

USER 1000
WORKDIR /opt/detourage
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    NEXORA_DETOURAGE_POIDS=/modeles \
    HF_HOME=/modeles/hf \
    NEXORA_DETOURAGE_DOSSIER=/travaux \
    NEXORA_DETOURAGE_PORT=8231 \
    FFMPEG_BIN=/usr/bin/ffmpeg \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
EXPOSE 8231
ENTRYPOINT ["python", "-I", "/opt/detourage/serveur.py"]
