# Image ComfyUI du palier pro du détourage (LTX-2.5 22B distilled + IC-LoRA Alpha-Gen). Poids HORS de l'image :
# volume /modeles monté sur models/ (voir extra_model_paths.yaml) ; liste et sha256 : modeles-pro.json.
#   RTX 5080 (sm_120, FP4 natif) : TORCH_INDEX=.../cu130 (défaut), transformeur nvfp4 + déchargement partiel en RAM
#   Carte 32 Go CUDA (5090) : même image, transformeur int8-convrot ; ROCm (R9700) : image à part, non faite ici
ARG PYTHON_IMAGE=docker.io/library/python:3.12-slim-trixie@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30
FROM ${PYTHON_IMAGE}
ARG TORCH_INDEX=https://download.pytorch.org/whl/cu130
ARG TORCH_VERSION=2.14.1
ARG TORCHVISION_VERSION=0.29.1
ARG TORCHAUDIO_VERSION=2.14.1
ARG COMFYUI_REF=2c75dc1b379a59e0880619d029607af5169a62ef
ARG LTXVIDEO_REF=220e1d45aa0469f518e982102fca4dca92a61862

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" "torchaudio==${TORCHAUDIO_VERSION}" --index-url "${TORCH_INDEX}"
# ComfyUI v0.44.0 et ComfyUI-LTXVideo, commits épinglés
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI \
 && git -C /opt/ComfyUI checkout -q ${COMFYUI_REF} \
 && git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git /opt/ComfyUI/custom_nodes/ComfyUI-LTXVideo \
 && git -C /opt/ComfyUI/custom_nodes/ComfyUI-LTXVideo checkout -q ${LTXVIDEO_REF} \
 && rm -rf /opt/ComfyUI/.git /opt/ComfyUI/custom_nodes/ComfyUI-LTXVideo/.git
RUN grep -v -E '^(torch|torchvision|torchaudio)([=<> ]|$)' /opt/ComfyUI/requirements.txt > /tmp/req.txt \
 && pip install --no-cache-dir -r /tmp/req.txt -r /opt/ComfyUI/custom_nodes/ComfyUI-LTXVideo/requirements.txt \
 && rm /tmp/req.txt

COPY extra_model_paths.yaml /opt/ComfyUI/extra_model_paths.yaml
COPY graphes/ /opt/detourage-pro/graphes/
COPY *.py *.json /opt/detourage-pro/
RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin comfy \
 && mkdir -p /opt/ComfyUI/user /opt/ComfyUI/input /opt/ComfyUI/output /opt/ComfyUI/temp \
 && chown -R 1000:1000 /opt/ComfyUI/user /opt/ComfyUI/input /opt/ComfyUI/output /opt/ComfyUI/temp
USER 1000
WORKDIR /opt/ComfyUI
ENV PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 HOME=/tmp PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
EXPOSE 8188
# Écoute dans l'espace réseau du pod seulement ; joint par le serveur de détourage (même nœud) ou kubectl port-forward.
ENTRYPOINT ["python", "-I", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--disable-auto-launch", "--preview-method", "none"]
